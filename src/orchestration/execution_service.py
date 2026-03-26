"""Execution Service for coordinating agent execution"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from src.schemas.orchestration import (
    ExecutionPlan,
    ExecutionMode,
    AgentType,
    AgentResult,
    AgentTask,
    FallbackStrategy,
    ParsedQuery
)
from src.observability.metrics import get_metrics_collector, AgentMetrics


class ExecutionService:
    """
    Coordinates agent execution with parallelism and dependencies.
    
    Executes agents according to execution plan, handling:
    - Parallel execution where dependencies allow
    - Timeout enforcement
    - Failure handling with fallback strategies
    - Resource limit enforcement
    
    TENANT ISOLATION:
    All agent executions are tenant-scoped.
    """
    
    def __init__(self, tenant_id: UUID):
        """
        Initialize execution service.
        
        Args:
            tenant_id: UUID of the tenant this service operates for
        """
        self.tenant_id = tenant_id
        self.max_concurrent_agents = 5
        self.execution_history: List[Dict[str, Any]] = []
    
    async def execute_plan(
        self,
        plan,  # Can be either ExecutionPlan type
        query_data: Optional[Dict[str, Any]] = None
    ) -> List[AgentResult]:
        """
        Execute an execution plan.
        
        Args:
            plan: Execution plan with tasks (supports both schema and LLM engine versions)
            query_data: Optional query data to pass to agents
            
        Returns:
            List of agent results
        """
        results = []
        
        # Handle both ExecutionPlan types
        if hasattr(plan, 'parallel_groups') and hasattr(plan, 'tasks'):
            # Schema-based ExecutionPlan with parallel_groups and tasks
            for group in plan.parallel_groups:
                group_results = await self.execute_agents_parallel(
                    group,
                    plan,
                    query_data
                )
                results.extend(group_results)
        elif hasattr(plan, 'agents'):
            # LLMReasoningEngine ExecutionPlan with agents list
            # Convert to schema format on the fly
            from src.schemas.orchestration import AgentTask, ExecutionPlan as SchemaPlan
            
            agents = plan.agents
            tasks = [
                AgentTask(
                    agent_type=agent,
                    parameters=plan.parameters,
                    dependencies=[],
                    timeout_seconds=120 if plan.execution_mode.value == "quick" else 300
                )
                for agent in agents
            ]
            
            # Create parallel groups
            if hasattr(plan, 'parallel_execution') and plan.parallel_execution and len(agents) > 1:
                parallel_groups = [agents]
            else:
                parallel_groups = [[agent] for agent in agents]
            
            # Create schema plan
            schema_plan = SchemaPlan(
                tasks=tasks,
                execution_mode=plan.execution_mode,
                parallel_groups=parallel_groups,
                estimated_duration=timedelta(seconds=plan.estimated_duration_seconds)
            )
            
            # Execute with schema plan
            for group in parallel_groups:
                group_results = await self.execute_agents_parallel(
                    group,
                    schema_plan,
                    query_data
                )
                results.extend(group_results)
        else:
            raise ValueError(f"Invalid execution plan type: {type(plan)}")
        
        # Record execution
        self._record_execution(plan, results)
        
        return results
    
    async def execute_agents_parallel(
        self,
        agents: List[AgentType],
        plan: ExecutionPlan,
        query_data: Optional[Dict[str, Any]] = None
    ) -> List[AgentResult]:
        """
        Execute multiple agents in parallel.
        
        Args:
            agents: List of agent types to execute
            plan: Execution plan
            query_data: Optional query data
            
        Returns:
            List of agent results
        """
        # Create tasks for each agent
        tasks = []
        agent_task_map = {task.agent_type: task for task in plan.tasks}
        
        for agent in agents:
            if agent in agent_task_map:
                task = agent_task_map[agent]
                tasks.append(
                    self._execute_single_agent(agent, task, query_data)
                )
        
        # Execute all tasks in parallel with semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent_agents)
        
        async def execute_with_semaphore(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )
        
        # Convert exceptions to failed results
        agent_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_results.append(AgentResult(
                    agent_type=agents[i],
                    success=False,
                    error=str(result),
                    execution_time=0.0
                ))
            else:
                agent_results.append(result)
        
        return agent_results
    
    async def _execute_single_agent(
        self,
        agent_type: AgentType,
        task: AgentTask,
        query_data: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Execute a single agent with timeout and error handling.
        
        Args:
            agent_type: Type of agent to execute
            task: Agent task with parameters
            query_data: Optional query data
            
        Returns:
            AgentResult
        """
        start_time = time.time()
        metrics_collector = get_metrics_collector()
        
        try:
            # Execute with timeout
            result_data = await asyncio.wait_for(
                self._call_agent(agent_type, task.parameters, query_data),
                timeout=task.timeout_seconds
            )
            
            execution_time = time.time() - start_time
            
            # Record metrics
            agent_metrics = AgentMetrics(
                agent_type=agent_type.value,
                execution_time_seconds=execution_time,
                status="success"
            )
            metrics_collector.record_agent_execution(agent_metrics)
            
            return AgentResult(
                agent_type=agent_type,
                success=True,
                data=result_data,
                execution_time=execution_time,
                confidence=result_data.get('confidence') if result_data else None
            )
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            
            # Record timeout metrics
            agent_metrics = AgentMetrics(
                agent_type=agent_type.value,
                execution_time_seconds=execution_time,
                status="failure",
                error_message=f"Timeout after {task.timeout_seconds}s"
            )
            metrics_collector.record_agent_execution(agent_metrics)
            
            # Handle timeout with fallback
            fallback = self.handle_agent_failure(
                agent_type,
                TimeoutError(f"Agent {agent_type.value} exceeded timeout of {task.timeout_seconds}s")
            )
            
            return AgentResult(
                agent_type=agent_type,
                success=False,
                error=f"Timeout after {task.timeout_seconds}s (fallback: {fallback.value})",
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Record error metrics
            agent_metrics = AgentMetrics(
                agent_type=agent_type.value,
                execution_time_seconds=execution_time,
                status="failure",
                error_message=str(e)
            )
            metrics_collector.record_agent_execution(agent_metrics)
            
            # Handle other errors
            fallback = self.handle_agent_failure(agent_type, e)
            
            return AgentResult(
                agent_type=agent_type,
                success=False,
                error=f"{type(e).__name__}: {str(e)} (fallback: {fallback.value})",
                execution_time=execution_time
            )
    
    async def _call_agent(
        self,
        agent_type: AgentType,
        parameters: Dict[str, Any],
        query_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call the actual agent implementation.
        
        Args:
            agent_type: Type of agent
            parameters: Agent parameters
            query_data: Optional query data (includes db, tenant_id, product_sku)
            
        Returns:
            Agent result data
        """
        if not query_data:
            # Fallback to mock if no query data
            await asyncio.sleep(0.1)
            return {
                'agent': agent_type.value,
                'status': 'completed',
                'confidence': 0.85,
                'data': {
                    'message': f'{agent_type.value} analysis completed (no data)',
                    'parameters': parameters
                }
            }
        
        # Extract common data
        db = query_data.get('db')
        tenant_id = query_data.get('tenant_id', self.tenant_id)
        product_sku = query_data.get('product_sku')
        
        if not db or not tenant_id:
            raise ValueError("Database session and tenant_id required for agent execution")
        
        # Resolve product_sku to product_ids if provided
        product_ids = []
        if product_sku:
            from sqlalchemy import select, func
            from src.models.product import Product
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Looking for SKU '{product_sku}' for tenant {tenant_id}")
            
            result = await db.execute(
                select(Product).where(
                    Product.tenant_id == tenant_id,
                    func.lower(Product.sku) == product_sku.lower()
                )
            )
            products = result.scalars().all()
            product_ids = [p.id for p in products]
            
            logger.info(f"Found {len(products)} product(s) for SKU '{product_sku}'")
            if products:
                logger.info(f"Product IDs: {[str(p.id) for p in products]}")
            else:
                logger.warning(f"No products found for SKU '{product_sku}' with tenant {tenant_id}")
        
        # Also check for explicit product_ids in query_data
        if 'product_ids' in query_data:
            product_ids.extend(query_data['product_ids'])
        
        if not product_ids:
            # Sales and General agents don't need product_ids — they query all tenant data
            if agent_type == AgentType.SALES:
                # Merge category_filter from query_data into parameters
                params_with_category = {**parameters, 'category_filter': query_data.get('category_filter')}
                return await self._execute_sales_agent(db, tenant_id, query_data.get('query_text', ''), params_with_category)
            if agent_type == AgentType.GENERAL:
                return await self._execute_general_agent(db, tenant_id, query_data.get('query_text', ''), parameters)
            # Return mock data if no products found
            return {
                'agent': agent_type.value,
                'status': 'no_products',
                'confidence': 0.0,
                'data': {
                    'message': f'No products found for SKU: {product_sku}',
                    'parameters': parameters
                }
            }
        
        # Route to appropriate agent
        if agent_type == AgentType.PRICING:
            return await self._execute_pricing_agent(db, tenant_id, product_ids, parameters)
        elif agent_type == AgentType.SENTIMENT:
            return await self._execute_sentiment_agent(db, tenant_id, product_ids, parameters)
        elif agent_type == AgentType.DEMAND_FORECAST:
            return await self._execute_forecast_agent(db, tenant_id, product_ids, parameters)
        elif agent_type == AgentType.DATA_QA:
            return await self._execute_qa_agent(db, tenant_id, product_ids, parameters)
        elif agent_type == AgentType.SALES:
            params_with_category = {**parameters, 'category_filter': query_data.get('category_filter')}
            return await self._execute_sales_agent(db, tenant_id, query_data.get('query_text', ''), params_with_category)
        elif agent_type == AgentType.GENERAL:
            return await self._execute_general_agent(db, tenant_id, query_data.get('query_text', ''), parameters)
        else:            # Unknown agent type
            return {
                'agent': agent_type.value,
                'status': 'unsupported',
                'confidence': 0.0,
                'data': {
                    'message': f'Agent type {agent_type.value} not implemented',
                    'parameters': parameters
                }
            }
    
    async def _execute_pricing_agent(
        self,
        db,
        tenant_id: UUID,
        product_ids: List[UUID],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute pricing intelligence agent"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from sqlalchemy import select
            from src.models.product import Product
            from src.agents.pricing_intelligence_v2 import EnhancedPricingIntelligenceAgent
            from src.agents.data_qa_agent import DataQAAgent
            from src.schemas.product import ProductResponse
            
            logger.info(f"Pricing agent: Fetching {len(product_ids)} products")
            
            # Fetch products
            result = await db.execute(
                select(Product).where(
                    Product.id.in_(product_ids),
                    Product.tenant_id == tenant_id
                )
            )
            products = result.scalars().all()
            
            if not products:
                logger.warning("Pricing agent: No products found")
                return {
                    'agent': 'pricing',
                    'status': 'no_data',
                    'confidence': 0.0,
                    'data': {'message': 'No products found'}
                }
            
            logger.info(f"Pricing agent: Found {len(products)} products, converting to schemas")
            
            # Convert to response schemas
            our_products = [ProductResponse.model_validate(p) for p in products]
            
            logger.info("Pricing agent: Initializing agents")
            
            # Initialize agents
            pricing_agent = EnhancedPricingIntelligenceAgent(tenant_id=tenant_id)
            qa_agent = DataQAAgent(tenant_id=tenant_id)
            
            logger.info("Pricing agent: Assessing data quality")
            
            # Assess data quality
            qa_report = qa_agent.assess_product_data_quality(our_products)
            
            logger.info("Pricing agent: Getting mock competitor data")
            
            # Get mock competitor data (for MVP)
            from src.api.pricing import _get_mock_competitor_products
            competitor_products = _get_mock_competitor_products(our_products)
            
            logger.info(f"Pricing agent: Got {len(competitor_products)} competitor products")
            
            # Create product mappings
            all_mappings = []
            for our_product in our_products:
                mappings = pricing_agent.map_product_equivalence(our_product, competitor_products)
                all_mappings.extend(mappings)
            
            logger.info(f"Pricing agent: Created {len(all_mappings)} product mappings")
            
            # Calculate price gaps
            price_gaps = pricing_agent.calculate_price_gaps(
                our_products,
                competitor_products,
                all_mappings
            )
            
            logger.info(f"Pricing agent: Calculated {len(price_gaps)} price gaps")
            
            # Calculate average confidence
            avg_confidence = qa_report.overall_quality_score if qa_report else 0.8
            
            # Create product lookup dict
            product_lookup = {p.id: p for p in our_products}
            
            # Convert price gaps to dicts for serialization with product names
            price_gaps_list = []
            for gap in price_gaps:
                product = product_lookup.get(gap.product_id)
                price_gaps_list.append({
                    'product_id': str(gap.product_id),
                    'product_name': product.name if product else f'Product {str(gap.product_id)[:8]}',
                    'sku': product.sku if product else f'SKU-{str(gap.product_id)[:8]}',
                    'our_price': float(gap.our_price),
                    'competitor_price': float(gap.competitor_price),
                    'gap_amount': float(gap.gap_amount),
                    'gap_percentage': float(gap.gap_percentage),
                    'confidence': 0.85
                })
            
            logger.info("Pricing agent: Returning results")
            
            return {
                'agent': 'pricing',
                'status': 'completed',
                'confidence': avg_confidence,
                'data': {
                    'message': f'Analyzed {len(our_products)} products, found {len(price_gaps)} price gaps',
                    'product_count': len(our_products),
                    'price_gaps': price_gaps_list,
                    'average_price': float(sum(p.price for p in our_products) / len(our_products)) if our_products else 0,
                    'price_change_pct': 0.0,
                    'recommendations': [
                        {
                            'product_id': str(gap.product_id),
                            'product_name': product_lookup.get(gap.product_id).name if gap.product_id in product_lookup else 'Unknown Product',
                            'sku': product_lookup.get(gap.product_id).sku if gap.product_id in product_lookup else 'Unknown SKU',
                            'title': f'Price adjustment for {product_lookup.get(gap.product_id).name if gap.product_id in product_lookup else "product"}',
                            'description': f'Consider adjusting price by {gap.gap_percentage:.1f}%',
                            'priority': 'high' if abs(gap.gap_percentage) > 10 else 'medium',
                            'impact': 'high',
                            'urgency': 'medium',
                            'confidence': 0.85
                        }
                        for gap in price_gaps[:3]
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Pricing agent failed: {e}", exc_info=True)
            return {
                'agent': 'pricing',
                'status': 'error',
                'confidence': 0.0,
                'data': {'message': f'Error: {str(e)}'}
            }
    
    async def _execute_sentiment_agent(
        self,
        db,
        tenant_id: UUID,
        product_ids: List[UUID],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute sentiment analysis agent"""
        from sqlalchemy import select
        from src.models.review import Review
        from src.models.product import Product
        from src.agents.sentiment_analysis_v2 import EnhancedSentimentAgent
        from src.agents.data_qa_agent import DataQAAgent
        from src.schemas.review import ReviewResponse
        
        # Fetch reviews
        result = await db.execute(
            select(Review).where(
                Review.product_id.in_(product_ids),
                Review.tenant_id == tenant_id
            )
        )
        reviews_records = result.scalars().all()
        
        if not reviews_records:
            return {
                'agent': 'sentiment',
                'status': 'no_data',
                'confidence': 0.0,
                'data': {'message': 'No reviews found'}
            }
        
        # Convert to response schemas
        reviews = [
            ReviewResponse(
                id=r.id,
                product_id=r.product_id,
                rating=r.rating,
                text=r.text,
                sentiment=r.sentiment,
                sentiment_confidence=r.sentiment_confidence,
                is_spam=r.is_spam,
                created_at=r.created_at,
                source=r.source
            )
            for r in reviews_records
        ]
        
        # Initialize agents
        sentiment_agent = EnhancedSentimentAgent(tenant_id=tenant_id)
        qa_agent = DataQAAgent(tenant_id=tenant_id)
        
        # Assess data quality
        qa_report = qa_agent.assess_review_data_quality(reviews)
        
        # Calculate aggregate sentiment
        sentiment_result = sentiment_agent.calculate_aggregate_sentiment_with_qa(
            reviews,
            qa_report
        )
        
        # Calculate per-product sentiment for "which product" queries
        product_sentiments = []
        raw_by_product = {}
        
        # Group raw DB records by product_id
        for r in reviews_records:
            pid = r.product_id
            if pid not in raw_by_product:
                raw_by_product[pid] = []
            raw_by_product[pid].append(r)
        
        # Calculate sentiment for each product
        for product_id, product_reviews in raw_by_product.items():
            sentiments = []
            for r in product_reviews:
                # Try to get sentiment value from either sentiment or sentiment_score field
                sentiment_value = r.sentiment_score if r.sentiment_score is not None else r.sentiment
                if sentiment_value is not None:
                    try:
                        sentiments.append(float(sentiment_value))
                    except (ValueError, TypeError):
                        continue
            
            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)
                positive_count = sum(1 for s in sentiments if s > 0.4)
                positive_pct = (positive_count / len(sentiments)) * 100
                
                # Fetch product name from database
                product_result = await db.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = product_result.scalar_one_or_none()
                
                product_sentiments.append({
                    'product_id': str(product_id),
                    'sku': product.sku if product else f'PROD-{str(product_id)[:8]}',
                    'product_name': product.name if product else f'Product {str(product_id)[:8]}',
                    'average_sentiment': avg_sentiment,
                    'review_count': len(product_reviews),
                    'positive_count': positive_count,
                    'positive_percentage': positive_pct
                })
        
        # Sort by average sentiment (highest first)
        product_sentiments.sort(key=lambda x: x['average_sentiment'], reverse=True)
        
        # Calculate average sentiment
        avg_sentiment = sentiment_result.aggregate_sentiment

        # ── Extract complaint patterns from low-rated review text ────────────
        complaint_patterns = []
        try:
            from collections import Counter
            import re as _re
            COMPLAINT_KEYWORDS = {
                'quality': ['quality', 'cheap', 'flimsy', 'broke', 'broken', 'defective', 'poor quality', 'bad quality'],
                'delivery': ['late', 'delayed', 'shipping', 'delivery', 'arrived late', 'slow delivery', 'not delivered'],
                'size/fit': ['size', 'fit', 'small', 'large', 'tight', 'loose', 'wrong size', 'sizing'],
                'packaging': ['packaging', 'damaged', 'package', 'box', 'wrapped', 'crushed'],
                'value': ['expensive', 'overpriced', 'not worth', 'waste of money', 'price', 'costly'],
                'functionality': ["doesn't work", "not working", "stopped working", 'malfunction', 'broken', 'defect'],
                'customer service': ['customer service', 'support', 'refund', 'return', 'response', 'unhelpful'],
                'description': ['not as described', 'misleading', 'different', 'fake', 'not genuine', 'wrong product'],
            }
            low_reviews = [r for r in reviews_records if r.rating and r.rating <= 2]
            keyword_counts = Counter()
            for review in low_reviews:
                text = (review.text or '').lower()
                for category, keywords in COMPLAINT_KEYWORDS.items():
                    if any(kw in text for kw in keywords):
                        keyword_counts[category] += 1
            for category, count in keyword_counts.most_common(5):
                if count > 0:
                    complaint_patterns.append({
                        'pattern': category,
                        'frequency': count,
                        'severity': 'high' if count > 5 else 'medium' if count > 2 else 'low',
                    })
        except Exception:
            pass
        
        return {
            'agent': 'sentiment',
            'status': 'completed',
            'confidence': sentiment_result.confidence_score,
            'data': {
                'message': f'Analyzed {len(reviews)} reviews across {len(product_sentiments)} products',
                'review_count': len(reviews),
                'aggregate_sentiment_score': avg_sentiment,
                'average_sentiment': avg_sentiment,
                'sentiment_change': 0.0,
                'positive_count': sentiment_result.sentiment_distribution.get('positive', 0),
                'negative_count': sentiment_result.sentiment_distribution.get('negative', 0),
                'neutral_count': sentiment_result.sentiment_distribution.get('neutral', 0),
                'product_sentiments': product_sentiments,
                'feature_requests': [],
                'complaint_patterns': complaint_patterns,
                'recommendations': [
                    {
                        'title': 'Address negative feedback',
                        'description': f'Found {sentiment_result.sentiment_distribution.get("negative", 0)} negative reviews',
                        'priority': 'high' if sentiment_result.sentiment_distribution.get('negative', 0) > 5 else 'medium',
                        'impact': 'high',
                        'urgency': 'high',
                        'confidence': sentiment_result.confidence_score
                    }
                ] if sentiment_result.sentiment_distribution.get('negative', 0) > 0 else []
            }
        }
    
    async def _execute_forecast_agent(
        self,
        db,
        tenant_id: UUID,
        product_ids: List[UUID],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute demand forecast agent"""
        from sqlalchemy import select
        from src.models.sales_record import SalesRecord
        from src.agents.demand_forecast_agent import DemandForecastAgent
        
        # Fetch sales records
        result = await db.execute(
            select(SalesRecord).where(
                SalesRecord.product_id.in_(product_ids),
                SalesRecord.tenant_id == tenant_id
            )
        )
        sales_records = result.scalars().all()
        
        if not sales_records:
            return {
                'agent': 'demand_forecast',
                'status': 'no_data',
                'confidence': 0.0,
                'data': {'message': 'No sales data found'}
            }
        
        # Initialize agent
        forecast_agent = DemandForecastAgent(tenant_id=tenant_id)
        
        # For MVP, return basic forecast info
        total_sales = sum(s.quantity for s in sales_records)
        avg_daily_sales = total_sales / max(len(sales_records), 1)
        
        return {
            'agent': 'demand_forecast',
            'status': 'completed',
            'confidence': 0.7,
            'final_confidence': 0.7,  # Add this for synthesizer
            'data': {
                'message': f'Forecasted demand based on {len(sales_records)} sales records',
                'sales_records': len(sales_records),
                'forecasted_demand': avg_daily_sales * 30,  # 30-day forecast
                'demand_change_pct': 0.0,  # Would calculate from trend
                'supply_gap': 0.0,
                'trend': 'stable',  # Add this field for synthesizer
                'seasonality': {},  # Add empty dict for now
                'alerts': [],  # Add empty list for now
                'recommendations': [
                    {
                        'title': 'Maintain current inventory levels',
                        'description': f'Forecasted demand: {avg_daily_sales * 30:.0f} units/month',
                        'priority': 'medium',
                        'impact': 'medium',
                        'urgency': 'low',
                        'confidence': 0.7
                    }
                ]
            }
        }
    
    async def _execute_qa_agent(
        self,
        db,
        tenant_id: UUID,
        product_ids: List[UUID],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute data QA agent"""
        from sqlalchemy import select
        from src.models.product import Product
        from src.agents.data_qa_agent import DataQAAgent
        from src.schemas.product import ProductResponse
        
        # Fetch products
        result = await db.execute(
            select(Product).where(
                Product.id.in_(product_ids),
                Product.tenant_id == tenant_id
            )
        )
        products = result.scalars().all()
        
        if not products:
            return {
                'agent': 'data_qa',
                'status': 'no_data',
                'confidence': 0.0,
                'data': {'message': 'No products found'}
            }
        
        # Convert to response schemas
        our_products = [ProductResponse.model_validate(p) for p in products]
        
        # Initialize agent
        qa_agent = DataQAAgent(tenant_id=tenant_id)
        
        # Assess data quality
        qa_report = qa_agent.assess_product_data_quality(our_products)
        
        return {
            'agent': 'data_qa',
            'status': 'completed',
            'confidence': qa_report.overall_quality_score,
            'data': {
                'message': f'Assessed {len(our_products)} products, quality score: {qa_report.overall_quality_score:.2f}',
                'product_count': len(our_products),
                'quality_score': qa_report.overall_quality_score,
                'issues_found': len(qa_report.issues),
                'recommendations': [
                    {
                        'title': 'Data quality improvement',
                        'description': f'Found {len(qa_report.issues)} data quality issues',
                        'priority': 'medium',
                        'impact': 'medium',
                        'urgency': 'low',
                        'confidence': qa_report.overall_quality_score
                    }
                ] if qa_report.issues else []
            }
        }
    
    async def _execute_sales_agent(
        self,
        db,
        tenant_id: UUID,
        query_text: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute sales/revenue analysis agent — handles revenue by category, top sellers, etc."""
        import logging
        from sqlalchemy import select, func, desc
        from src.models.sales_record import SalesRecord
        from src.models.product import Product

        logger = logging.getLogger(__name__)
        query_lower = query_text.lower()

        # Use category_filter from parameters, or self-extract from query text as fallback
        category_filter = parameters.get('category_filter')
        if not category_filter:
            _CATS = [
                'electronics', 'home & kitchen', 'sports & fitness',
                'beauty & personal care', 'clothing', 'books', 'toys',
                'automotive', 'garden', 'health', 'kitchen', 'sports',
                'beauty', 'fashion', 'apparel',
            ]
            _ALIASES = {
                'kitchen': 'home & kitchen', 'sports': 'sports & fitness',
                'beauty': 'beauty & personal care', 'fashion': 'clothing',
                'apparel': 'clothing', 'health': 'beauty & personal care',
            }
            _found = next((c for c in _CATS if c in query_lower), None)
            if _found:
                category_filter = _ALIASES.get(_found, _found)

        try:
            # Revenue by category
            if any(k in query_lower for k in ['category', 'revenue by', 'sales by']):
                result = await db.execute(
                    select(
                        Product.category,
                        func.sum(SalesRecord.revenue).label('total_revenue'),
                        func.sum(SalesRecord.quantity).label('total_units'),
                        func.count(SalesRecord.id).label('order_count')
                    )
                    .join(Product, SalesRecord.product_id == Product.id)
                    .where(SalesRecord.tenant_id == tenant_id)
                    .group_by(Product.category)
                    .order_by(desc('total_revenue'))
                )
                rows = result.all()

                if not rows:
                    return {'agent': 'sales', 'status': 'no_data', 'confidence': 0.0,
                            'data': {'message': 'No sales data found'}}

                categories = [
                    {
                        'category': row.category or 'Uncategorized',
                        'total_revenue': float(row.total_revenue),
                        'total_units': int(row.total_units),
                        'order_count': int(row.order_count),
                    }
                    for row in rows
                ]
                top = categories[0]
                return {
                    'agent': 'sales',
                    'status': 'completed',
                    'confidence': 0.95,
                    'data': {
                        'analysis_type': 'revenue_by_category',
                        'message': f'Revenue breakdown across {len(categories)} categories. '
                                   f'Top category: {top["category"]} with ₹{top["total_revenue"]:,.2f}',
                        'categories': categories,
                        'total_revenue': sum(c['total_revenue'] for c in categories),
                        'total_units': sum(c['total_units'] for c in categories),
                    }
                }

            # Top selling products — scoped to category if one was detected
            filters = [SalesRecord.tenant_id == tenant_id]
            if category_filter:
                filters.append(func.lower(Product.category).contains(category_filter.lower()))

            result = await db.execute(
                select(
                    Product.name,
                    Product.sku,
                    Product.category,
                    func.sum(SalesRecord.quantity).label('total_units'),
                    func.sum(SalesRecord.revenue).label('total_revenue'),
                )
                .join(Product, SalesRecord.product_id == Product.id)
                .where(*filters)
                .group_by(Product.id, Product.name, Product.sku, Product.category)
                .order_by(desc('total_revenue'))
                .limit(10)
            )
            rows = result.all()

            if not rows:
                return {'agent': 'sales', 'status': 'no_data', 'confidence': 0.0,
                        'data': {'message': f'No sales data found{f" for {category_filter}" if category_filter else ""}'}}

            def _clean_name(name, sku):
                import re
                if not name:
                    return sku or 'Unknown'
                if re.match(r'^Product\s+[A-Z0-9]{8,}$', name.strip()):
                    return sku or name
                cleaned = re.sub(r'\s*\([A-Z0-9][A-Z0-9\-]{3,}\)', '', name).strip()
                return cleaned or sku or name

            products = [
                {
                    'name': _clean_name(row.name, row.sku),
                    'sku': row.sku,
                    'category': row.category or 'Uncategorized',
                    'total_units': int(row.total_units),
                    'total_revenue': float(row.total_revenue),
                }
                for row in rows
            ]
            top = products[0]
            scope = f' in {category_filter}' if category_filter else ''
            return {
                'agent': 'sales',
                'status': 'completed',
                'confidence': 0.95,
                'data': {
                    'analysis_type': 'top_products',
                    'message': f'Top {len(products)} products by revenue{scope}. '
                               f'Leader: {top["name"]} (₹{top["total_revenue"]:,.2f})',
                    'products': products,
                    'total_revenue': sum(p['total_revenue'] for p in products),
                    'total_units': sum(p['total_units'] for p in products),
                    'category_filter': category_filter,
                }
            }

        except Exception as e:
            logger.error(f"Sales agent failed: {e}", exc_info=True)
            return {'agent': 'sales', 'status': 'error', 'confidence': 0.0,
                    'data': {'message': f'Error: {str(e)}'}}

    async def _execute_general_agent(
        self,
        db,
        tenant_id: UUID,
        query_text: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Universal agent — answers ANY natural language question from the DB.

        Covers: revenue totals, complaints, product performance diagnostics,
        profit margins, business health, trends over time, comparisons,
        inventory, pricing, reviews, marketplace, category deep dives, and more.
        """
        import logging
        import re
        from sqlalchemy import select, func, desc, asc, and_, or_, case
        from src.models.product import Product
        from src.models.sales_record import SalesRecord
        from src.models.review import Review
        from src.models.price_history import PriceHistory

        logger = logging.getLogger(__name__)
        q = query_text.lower()

        # ── helpers ──────────────────────────────────────────────────────────
        def _clean(name, sku):
            if not name:
                return sku or 'Unknown'
            if re.match(r'^Product\s+[A-Z0-9]{8,}$', name.strip()):
                return sku or name
            return re.sub(r'\s*\([A-Z0-9][A-Z0-9\-]{3,}\)', '', name).strip() or sku or name

        KNOWN_CATEGORIES = [
            'electronics', 'home & kitchen', 'sports & fitness',
            'beauty & personal care', 'clothing', 'books', 'toys',
            'automotive', 'garden', 'health', 'kitchen', 'sports',
            'beauty', 'fashion', 'apparel',
        ]
        CATEGORY_ALIASES = {
            'kitchen': 'home & kitchen', 'sports': 'sports & fitness',
            'beauty': 'beauty & personal care', 'fashion': 'clothing',
            'apparel': 'clothing', 'health': 'beauty & personal care',
        }
        mentioned_category = next((c for c in KNOWN_CATEGORIES if c in q), None)
        if mentioned_category:
            mentioned_category = CATEGORY_ALIASES.get(mentioned_category, mentioned_category)

        def _ok(r):
            """Return standard no-data response."""
            return {'agent': 'general', 'status': 'no_data', 'confidence': 0.9,
                    'data': {'message': 'No data found for your query.', 'analysis_type': 'empty', 'items': []}}

        try:
            # ── 0. TOTAL REVENUE (single number) ─────────────────────────────
            if any(k in q for k in ['total revenue', 'total sales', 'total earning',
                                     'how much revenue', 'how much have', 'revenue generated',
                                     'revenue till', 'revenue so far', 'all time revenue',
                                     'overall revenue', 'gross revenue']):
                r = await db.execute(
                    select(
                        func.coalesce(func.sum(SalesRecord.revenue), 0).label('total_revenue'),
                        func.coalesce(func.sum(SalesRecord.quantity), 0).label('total_units'),
                        func.count(SalesRecord.id).label('total_orders'),
                    ).where(SalesRecord.tenant_id == tenant_id)
                )
                row = r.one()
                # Also break down by category
                cat_r = await db.execute(
                    select(
                        Product.category,
                        func.sum(SalesRecord.revenue).label('rev'),
                        func.sum(SalesRecord.quantity).label('units'),
                    )
                    .join(Product, SalesRecord.product_id == Product.id)
                    .where(SalesRecord.tenant_id == tenant_id)
                    .group_by(Product.category)
                    .order_by(desc('rev'))
                )
                cats = [{'category': c.category or 'Uncategorized',
                         'revenue': round(float(c.rev), 2),
                         'units': int(c.units)} for c in cat_r.all()]
                total = round(float(row.total_revenue), 2)
                return {
                    'agent': 'general', 'status': 'completed', 'confidence': 0.98,
                    'data': {
                        'analysis_type': 'total_revenue',
                        'message': (f'Total revenue generated: ₹{total:,.2f} '
                                    f'from {int(row.total_orders):,} orders '
                                    f'({int(row.total_units):,} units sold).'),
                        'total_revenue': total,
                        'total_units': int(row.total_units),
                        'total_orders': int(row.total_orders),
                        'items': cats,
                        'columns': ['Category', 'Revenue', 'Units'],
                    }
                }

            # ── 0b. PROFIT / MARGIN queries ───────────────────────────────────
            if any(k in q for k in ['profit', 'margin', 'gross profit', 'net profit',
                                     'profit margin', 'how profitable']):
                r = await db.execute(
                    select(
                        Product.category,
                        func.sum(SalesRecord.revenue).label('revenue'),
                        func.sum(SalesRecord.quantity * Product.cost).label('cost'),
                        func.sum(SalesRecord.quantity).label('units'),
                    )
                    .join(Product, SalesRecord.product_id == Product.id)
                    .where(
                        SalesRecord.tenant_id == tenant_id,
                        Product.cost.isnot(None)
                    )
                    .group_by(Product.category)
                    .order_by(desc('revenue'))
                )
                rows = r.all()
                if not rows:
                    # No cost data — return revenue only
                    r2 = await db.execute(
                        select(func.sum(SalesRecord.revenue).label('rev'))
                        .where(SalesRecord.tenant_id == tenant_id)
                    )
                    rev = float(r2.scalar() or 0)
                    return {
                        'agent': 'general', 'status': 'completed', 'confidence': 0.7,
                        'data': {
                            'analysis_type': 'profit',
                            'message': f'Total revenue: ₹{rev:,.2f}. Cost data not available to calculate profit margin.',
                            'items': [],
                        }
                    }
                items = []
                for row in rows:
                    rev = float(row.revenue or 0)
                    cost = float(row.cost or 0)
                    profit = rev - cost
                    margin = (profit / rev * 100) if rev > 0 else 0
                    items.append({
                        'category': row.category or 'Uncategorized',
                        'revenue': round(rev, 2),
                        'cost': round(cost, 2),
                        'profit': round(profit, 2),
                        'margin_pct': round(margin, 1),
                        'units': int(row.units),
                    })
                total_rev = sum(i['revenue'] for i in items)
                total_profit = sum(i['profit'] for i in items)
                overall_margin = (total_profit / total_rev * 100) if total_rev > 0 else 0
                return {
                    'agent': 'general', 'status': 'completed', 'confidence': 0.93,
                    'data': {
                        'analysis_type': 'profit',
                        'message': (f'Overall profit: ₹{total_profit:,.2f} on ₹{total_rev:,.2f} revenue '
                                    f'({overall_margin:.1f}% margin).'),
                        'total_revenue': round(total_rev, 2),
                        'total_profit': round(total_profit, 2),
                        'overall_margin_pct': round(overall_margin, 1),
                        'items': items,
                        'columns': ['Category', 'Revenue', 'Cost', 'Profit', 'Margin %', 'Units'],
                    }
                }

            # ── 0c. COMPLAINTS / NEGATIVE REVIEWS ────────────────────────────
            if any(k in q for k in ['complaint', 'complain', 'most complaint', 'common complaint',
                                     'negative review', 'bad review', 'worst review',
                                     'what do customer complain', 'what are customer saying bad',
                                     'unhappy', 'dissatisfied', 'issue', 'problem with product']):
                filters = [Review.tenant_id == tenant_id, Review.rating <= 2]
                if mentioned_category:
                    filters.append(func.lower(Product.category).contains(mentioned_category))

                r = await db.execute(
                    select(
                        Product.sku,
                        Product.name,
                        Product.category,
                        func.count(Review.id).label('complaint_count'),
                        func.avg(Review.rating).label('avg_rating'),
                        func.min(Review.rating).label('min_rating'),
                    )
                    .join(Product, Review.product_id == Product.id)
                    .where(and_(*filters))
                    .group_by(Product.id, Product.sku, Product.name, Product.category)
                    .order_by(desc('complaint_count'))
                    .limit(20)
                )
                rows = r.all()

                # Also get sample complaint texts
                sample_r = await db.execute(
                    select(Review.text, Product.name, Review.rating)
                    .join(Product, Review.product_id == Product.id)
                    .where(Review.tenant_id == tenant_id, Review.rating <= 2)
                    .order_by(Review.rating)
                    .limit(5)
                )
                samples = [{'product': _clean(s.name, ''), 'rating': s.rating,
                            'text': (s.text or '')[:200]} for s in sample_r.all()]

                # Total complaint count
                total_r = await db.execute(
                    select(func.count(Review.id))
                    .where(Review.tenant_id == tenant_id, Review.rating <= 2)
                )
                total_complaints = total_r.scalar() or 0

                if not rows:
                    return {'agent': 'general', 'status': 'completed', 'confidence': 0.9,
                            'data': {'analysis_type': 'complaints',
                                     'message': 'No complaints (1-2 star reviews) found.', 'items': []}}

                items = [{'sku': r.sku, 'name': _clean(r.name, r.sku),
                          'category': r.category,
                          'complaint_count': int(r.complaint_count),
                          'avg_rating': round(float(r.avg_rating), 2)} for r in rows]
                top = items[0]
                return {
                    'agent': 'general', 'status': 'completed', 'confidence': 0.93,
                    'data': {
                        'analysis_type': 'complaints',
                        'message': (f'{total_complaints} total complaints (1-2★ reviews). '
                                    f'Most complained: {top["name"]} ({top["complaint_count"]} complaints).'),
                        'total_complaints': total_complaints,
                        'items': items,
                        'sample_reviews': samples,
                        'columns': ['SKU', 'Name', 'Category', 'Complaints', 'Avg Rating'],
                    }
                }

            # ── 0d. BUSINESS HEALTH / OVERVIEW ───────────────────────────────
            # ── 0d. BUSINESS HEALTH / OVERVIEW ───────────────────────────────
            BUSINESS_HEALTH_KEYWORDS = [
                'business health', 'business overview', 'how is my business',
                'overall performance', 'business summary', 'how am i doing',
                'business doing', 'overall status', 'dashboard summary',
                'give me a summary', 'business report', 'board',
                'executive summary', 'board-ready', 'board ready',
                'quarterly', 'this quarter', 'q1', 'q2', 'q3', 'q4',
                'summary of the business', 'summary of my business',
                'how are we doing', 'state of the business',
                'past six months', 'past 6 months', 'last six months',
                'last 6 months', 'past three months', 'last three months',
                'past month', 'last month', 'year to date', 'ytd',
                'month summary', 'week summary', 'annual summary',
                'performance summary', 'health report', 'status report',
                'investor', 'stakeholder', 'management report',
            ]
            # Also catch "summary" + any time word as a business overview request
            TIME_WORDS = ['month', 'quarter', 'year', 'week', 'period', 'six', 'three', 'annual']
            is_timed_summary = ('summary' in q or 'report' in q) and any(t in q for t in TIME_WORDS)

            if any(k in q for k in BUSINESS_HEALTH_KEYWORDS) or is_timed_summary:
                # Revenue
                rev_r = await db.execute(
                    select(
                        func.coalesce(func.sum(SalesRecord.revenue), 0).label('total_revenue'),
                        func.coalesce(func.sum(SalesRecord.quantity), 0).label('total_units'),
                        func.count(SalesRecord.id).label('total_orders'),
                    ).where(SalesRecord.tenant_id == tenant_id)
                )
                rev_row = rev_r.one()
                # Products
                prod_r = await db.execute(
                    select(func.count(Product.id)).where(Product.tenant_id == tenant_id)
                )
                prod_count = prod_r.scalar() or 0
                # Reviews
                review_r = await db.execute(
                    select(
                        func.count(Review.id).label('total'),
                        func.avg(Review.rating).label('avg_rating'),
                        func.sum(case((Review.rating <= 2, 1), else_=0)).label('complaints'),
                        func.sum(case((Review.rating >= 4, 1), else_=0)).label('positive'),
                    ).where(Review.tenant_id == tenant_id)
                )
                rev_row2 = review_r.one()
                # Low stock
                low_r = await db.execute(
                    select(func.count(Product.id))
                    .where(Product.tenant_id == tenant_id, Product.inventory_level < 20)
                )
                low_stock = low_r.scalar() or 0

                total_rev = round(float(rev_row.total_revenue), 2)
                avg_rating = round(float(rev_row2.avg_rating or 0), 2)
                complaint_pct = round((int(rev_row2.complaints or 0) / max(int(rev_row2.total or 1), 1)) * 100, 1)

                return {
                    'agent': 'general', 'status': 'completed', 'confidence': 0.95,
                    'data': {
                        'analysis_type': 'business_health',
                        'message': (
                            f'Business overview: ₹{total_rev:,.2f} total revenue, '
                            f'{prod_count} products, {int(rev_row.total_orders):,} orders, '
                            f'avg rating {avg_rating}/5, {complaint_pct}% complaint rate.'
                        ),
                        'items': [
                            {'metric': 'Total Revenue', 'value': f'₹{total_rev:,.2f}'},
                            {'metric': 'Total Orders', 'value': f'{int(rev_row.total_orders):,}'},
                            {'metric': 'Units Sold', 'value': f'{int(rev_row.total_units):,}'},
                            {'metric': 'Products', 'value': str(prod_count)},
                            {'metric': 'Avg Rating', 'value': f'{avg_rating}/5'},
                            {'metric': 'Total Reviews', 'value': str(int(rev_row2.total or 0))},
                            {'metric': 'Complaints (1-2★)', 'value': str(int(rev_row2.complaints or 0))},
                            {'metric': 'Positive Reviews (4-5★)', 'value': str(int(rev_row2.positive or 0))},
                            {'metric': 'Low Stock Products (<20)', 'value': str(low_stock)},
                        ],
                        'columns': ['Metric', 'Value'],
                        'total_revenue': total_rev,
                    }
                }

            # ── 0e. SENTIMENT TREND OVER TIME ────────────────────────────────
            if any(k in q for k in ['sentiment trend', 'customer sentiment', 'review trend',
                                     'rating trend', 'sentiment over time', 'how are reviews',
                                     'how is sentiment', 'customer feedback trend']):
                from sqlalchemy import case as sa_case
                r = await db.execute(
                    select(
                        func.strftime('%Y-%m', Review.created_at).label('month'),
                        func.count(Review.id).label('review_count'),
                        func.avg(Review.rating).label('avg_rating'),
                        func.sum(sa_case((Review.rating >= 4, 1), else_=0)).label('positive'),
                        func.sum(sa_case((Review.rating <= 2, 1), else_=0)).label('negative'),
                    )
                    .where(Review.tenant_id == tenant_id)
                    .group_by(func.strftime('%Y-%m', Review.created_at))
                    .order_by('month')
                )
                rows = r.all()
                if not rows:
                    return _ok(None)
                items = []
                for row in rows:
                    total = int(row.review_count)
                    pos = int(row.positive or 0)
                    neg = int(row.negative or 0)
                    items.append({
                        'month': str(row.month)[:7],
                        'review_count': total,
                        'avg_rating': round(float(row.avg_rating or 0), 2),
                        'positive': pos,
                        'negative': neg,
                        'positive_pct': round(pos / total * 100, 1) if total > 0 else 0,
                    })
                # Overall trend
                if len(items) >= 2:
                    first_r = items[0]['avg_rating']
                    last_r = items[-1]['avg_rating']
                    delta = last_r - first_r
                    trend_word = 'improving' if delta > 0.1 else 'declining' if delta < -0.1 else 'stable'
                else:
                    trend_word = 'stable'
                    delta = 0
                overall_avg = round(sum(i['avg_rating'] for i in items) / len(items), 2)
                return {
                    'agent': 'general', 'status': 'completed', 'confidence': 0.93,
                    'data': {
                        'analysis_type': 'sentiment_trend',
                        'message': (f'Customer sentiment over {len(items)} months. '
                                    f'Overall {trend_word} — avg rating {overall_avg}/5 '
                                    f'({delta:+.2f} change).'),
                        'items': items,
                        'trend': trend_word,
                        'overall_avg_rating': overall_avg,
                        'columns': ['Month', 'Reviews', 'Avg Rating', 'Positive', 'Negative', 'Positive %'],
                    }
                }

            # ── 0f. REVENUE TREND OVER TIME ───────────────────────────────────
            # Require revenue/sales context to avoid matching "sentiment trends"
            is_revenue_trend = (
                any(k in q for k in ['revenue trend', 'sales trend', 'revenue over time',
                                     'sales over time', 'month by month', 'revenue history',
                                     'sales history', 'revenue growth', 'sales growth'])
                or (any(k in q for k in ['trend', 'over time', 'monthly', 'growth'])
                    and any(k in q for k in ['revenue', 'sales', 'earning', 'income']))
            )
            if is_revenue_trend:
                r = await db.execute(
                    select(
                        func.strftime('%Y-%m', SalesRecord.date).label('month'),
                        func.sum(SalesRecord.revenue).label('revenue'),
                        func.sum(SalesRecord.quantity).label('units'),
                        func.count(SalesRecord.id).label('orders'),
                    )
                    .where(SalesRecord.tenant_id == tenant_id)
                    .group_by(func.strftime('%Y-%m', SalesRecord.date))
                    .order_by('month')
                )
                rows = r.all()
                if not rows:
                    return _ok(None)
                items = [{'month': str(row.month)[:7],
                          'revenue': round(float(row.revenue), 2),
                          'units': int(row.units),
                          'orders': int(row.orders)} for row in rows]
                # Calculate growth
                if len(items) >= 2:
                    first, last = items[0]['revenue'], items[-1]['revenue']
                    growth = ((last - first) / first * 100) if first > 0 else 0
                    trend_word = 'growing' if growth > 5 else 'declining' if growth < -5 else 'stable'
                else:
                    growth, trend_word = 0, 'stable'
                return {
                    'agent': 'general', 'status': 'completed', 'confidence': 0.95,
                    'data': {
                        'analysis_type': 'revenue_trend',
                        'message': (f'Revenue trend over {len(items)} months. '
                                    f'Overall {trend_word} ({growth:+.1f}% change).'),
                        'items': items,
                        'growth_pct': round(growth, 1),
                        'trend': trend_word,
                        'columns': ['Month', 'Revenue', 'Units', 'Orders'],
                    }
                }

            # ── 0f. PRODUCT PERFORMANCE DIAGNOSTIC ("why not performing") ────
            if any(k in q for k in ['why', 'not performing', 'performing bad', 'performing poor',
                                     'not doing well', 'doing poorly', 'underperform',
                                     'what is wrong', "what's wrong", 'issue with',
                                     'problem with', 'why is', 'why are']):
                # Cross-reference sales + reviews + pricing for all products
                # (or category-specific if mentioned)
                filters_p = [Product.tenant_id == tenant_id]
                if mentioned_category:
                    filters_p.append(func.lower(Product.category).contains(mentioned_category))

                r = await db.execute(
                    select(
                        Product.id.label('product_id'),
                        Product.sku,
                        Product.name,
                        Product.category,
                        Product.price,
                        Product.inventory_level,
                        func.coalesce(func.sum(SalesRecord.quantity), 0).label('units_sold'),
                        func.coalesce(func.sum(SalesRecord.revenue), 0).label('revenue'),
                        func.coalesce(func.count(Review.id), 0).label('review_count'),
                        func.coalesce(func.avg(Review.rating), 0).label('avg_rating'),
                        func.coalesce(
                            func.sum(case((Review.rating <= 2, 1), else_=0)), 0
                        ).label('complaints'),
                    )
                    .outerjoin(SalesRecord, and_(
                        SalesRecord.product_id == Product.id,
                        SalesRecord.tenant_id == tenant_id
                    ))
                    .outerjoin(Review, and_(
                        Review.product_id == Product.id,
                        Review.tenant_id == tenant_id
                    ))
                    .where(and_(*filters_p))
                    .group_by(Product.id, Product.sku, Product.name,
                              Product.category, Product.price, Product.inventory_level)
                    .order_by(asc('revenue'))
                    .limit(30)
                )
                rows = r.all()
                if not rows:
                    return _ok(None)

                # Get category-level context for comparison
                cat_ctx = {}
                if mentioned_category:
                    cat_r = await db.execute(
                        select(
                            func.count(Product.id).label('product_count'),
                            func.coalesce(func.sum(SalesRecord.revenue), 0).label('cat_revenue'),
                            func.coalesce(func.sum(SalesRecord.quantity), 0).label('cat_units'),
                        )
                        .outerjoin(SalesRecord, and_(
                            SalesRecord.product_id == Product.id,
                            SalesRecord.tenant_id == tenant_id
                        ))
                        .where(
                            Product.tenant_id == tenant_id,
                            func.lower(Product.category).contains(mentioned_category)
                        )
                    )
                    cat_row = cat_r.one()
                    # Get rank among all categories
                    all_cat_r = await db.execute(
                        select(
                            Product.category,
                            func.coalesce(func.sum(SalesRecord.revenue), 0).label('rev'),
                        )
                        .outerjoin(SalesRecord, and_(
                            SalesRecord.product_id == Product.id,
                            SalesRecord.tenant_id == tenant_id
                        ))
                        .where(Product.tenant_id == tenant_id)
                        .group_by(Product.category)
                        .order_by(desc('rev'))
                    )
                    all_cats = all_cat_r.all()
                    total_categories = len(all_cats)
                    cat_rank = next(
                        (i + 1 for i, c in enumerate(all_cats)
                         if c.category and mentioned_category.lower() in c.category.lower()),
                        None
                    )
                    cat_ctx = {
                        'product_count': int(cat_row.product_count),
                        'cat_revenue': round(float(cat_row.cat_revenue), 2),
                        'cat_units': int(cat_row.cat_units),
                        'cat_rank': cat_rank,
                        'total_categories': total_categories,
                    }

                items = []
                issues = []
                for row in rows:
                    units = int(row.units_sold)
                    rev = round(float(row.revenue), 2)
                    rating = round(float(row.avg_rating), 2)
                    complaints = int(row.complaints)
                    inv = row.inventory_level or 0
                    name = _clean(row.name, row.sku)
                    price = float(row.price)

                    # Complaint rate is more meaningful than raw count
                    complaint_rate = (complaints / units * 100) if units > 0 else 0

                    product_issues = []
                    if units == 0:
                        product_issues.append('zero sales — no demand or visibility issue')
                    if rating > 0 and rating < 3.0:
                        product_issues.append(f'poor rating ({rating}/5)')
                    elif rating >= 3.0 and complaint_rate > 15:
                        # Good avg rating but high complaint rate = vocal unhappy minority
                        product_issues.append(
                            f'high complaint rate ({complaint_rate:.0f}% of buyers complained despite {rating}★ avg)'
                        )
                    elif complaint_rate > 25:
                        product_issues.append(f'very high complaint rate ({complaint_rate:.0f}%)')
                    if inv == 0:
                        product_issues.append('out of stock')
                    elif inv < 10:
                        product_issues.append('critically low stock')
                    if units > 0 and rev / units < price * 0.5:
                        product_issues.append('revenue per unit below expected (possible returns/discounts)')

                    # Category-level issues (only once, on first product)
                    if cat_ctx and not items:
                        if cat_ctx['product_count'] <= 2:
                            product_issues.append(
                                f'thin catalogue — only {cat_ctx["product_count"]} product(s) in category'
                            )
                        if cat_ctx['cat_rank'] and cat_ctx['cat_rank'] >= cat_ctx['total_categories']:
                            product_issues.append(
                                f'lowest revenue category (ranked {cat_ctx["cat_rank"]} of {cat_ctx["total_categories"]})'
                            )

                    # Fetch actual 1-2★ review texts for this product
                    low_reviews = []
                    if complaints > 0:
                        rev_r = await db.execute(
                            select(Review.rating, Review.text)
                            .where(
                                Review.product_id == row.product_id,
                                Review.tenant_id == tenant_id,
                                Review.rating <= 2,
                                Review.text.isnot(None),
                            )
                            .order_by(Review.rating)
                            .limit(10)
                        )
                        low_reviews = [
                            {'rating': int(r.rating), 'text': (r.text or '').strip()}
                            for r in rev_r.all()
                            if r.text and r.text.strip()
                        ]

                    items.append({
                        'sku': row.sku,
                        'name': name,
                        'category': row.category,
                        'price': price,
                        'units_sold': units,
                        'revenue': rev,
                        'avg_rating': rating,
                        'complaints': complaints,
                        'complaint_rate': round(complaint_rate, 1),
                        'inventory': inv,
                        'issues': ', '.join(product_issues) if product_issues else 'no issues detected',
                        'low_reviews': low_reviews,
                    })
                    if product_issues:
                        issues.append(f'{name}: {", ".join(product_issues[:2])}')

                scope = f' in {mentioned_category}' if mentioned_category else ''
                # Build a richer summary with category context
                ctx_parts = []
                if cat_ctx:
                    ctx_parts.append(f'{cat_ctx["product_count"]} product(s) in catalogue')
                    if cat_ctx['cat_rank']:
                        ctx_parts.append(
                            f'ranked #{cat_ctx["cat_rank"]} of {cat_ctx["total_categories"]} categories by revenue'
                        )
                    ctx_parts.append(f'₹{cat_ctx["cat_revenue"]:,.2f} total category revenue')
                ctx_str = ' — ' + ', '.join(ctx_parts) if ctx_parts else ''
                msg = (f'Performance diagnostic{scope}: {len(items)} product(s) analysed{ctx_str}. '
                       f'{len(issues)} have issues.')
                if issues:
                    msg += f' Key problems: {"; ".join(issues[:3])}.'
                return {
                    'agent': 'general', 'status': 'completed', 'confidence': 0.92,
                    'data': {
                        'analysis_type': 'performance_diagnostic',
                        'message': msg,
                        'items': items,
                        'issue_count': len(issues),
                        'columns': ['SKU', 'Name', 'Category', 'Price', 'Units Sold',
                                    'Revenue', 'Avg Rating', 'Complaints', 'Stock', 'Issues'],
                    }
                }

            # ── 1. INVENTORY queries ──────────────────────────────────────────
            if any(k in q for k in ['inventory', 'stock', 'in stock', 'out of stock', 'low stock']):
                filters = [Product.tenant_id == tenant_id]
                if mentioned_category:
                    filters.append(func.lower(Product.category).contains(mentioned_category))
                if any(k in q for k in ['low', 'running out', 'reorder']):
                    filters.append(Product.inventory_level < 50)
                    order = asc(Product.inventory_level)
                elif any(k in q for k in ['out of stock', 'zero', 'no stock']):
                    filters.append(Product.inventory_level == 0)
                    order = asc(Product.inventory_level)
                elif any(k in q for k in ['high', 'most', 'highest']):
                    order = desc(Product.inventory_level)
                else:
                    order = asc(Product.inventory_level)

                result = await db.execute(
                    select(Product).where(and_(*filters)).order_by(order).limit(20)
                )
                products = result.scalars().all()
                if not products:
                    return {'agent': 'general', 'status': 'no_data', 'confidence': 0.9,
                            'data': {'message': 'No products match your inventory query.',
                                     'analysis_type': 'inventory', 'items': []}}
                items = [{'sku': p.sku, 'name': _clean(p.name, p.sku),
                          'category': p.category, 'inventory': p.inventory_level,
                          'price': float(p.price)} for p in products]
                total = sum(i['inventory'] or 0 for i in items)
                return {
                    'agent': 'general', 'status': 'completed', 'confidence': 0.92,
                    'data': {
                        'analysis_type': 'inventory',
                        'message': f'Found {len(items)} products. Total stock: {total:,} units.',
                        'items': items,
                        'columns': ['SKU', 'Name', 'Category', 'Stock', 'Price'],
                    }
                }

            # ── 2. PRODUCT LIST / CATALOGUE queries ───────────────────────────
            if any(k in q for k in ['list', 'show', 'all products', 'products in', 'what products',
                                     'how many products', 'count product', 'number of product']):
                filters = [Product.tenant_id == tenant_id]
                if mentioned_category:
                    filters.append(func.lower(Product.category).contains(mentioned_category))

                # Count query
                if any(k in q for k in ['how many', 'count', 'number of']):
                    count_result = await db.execute(
                        select(func.count(Product.id)).where(and_(*filters))
                    )
                    count = count_result.scalar()
                    # Also break down by category if no specific category asked
                    if not mentioned_category:
                        cat_result = await db.execute(
                            select(Product.category, func.count(Product.id).label('cnt'))
                            .where(Product.tenant_id == tenant_id)
                            .group_by(Product.category)
                            .order_by(desc('cnt'))
                        )
                        cats = [{'category': r.category or 'Uncategorized', 'count': r.cnt}
                                for r in cat_result.all()]
                        return {
                            'agent': 'general', 'status': 'completed', 'confidence': 0.95,
                            'data': {
                                'analysis_type': 'product_count',
                                'message': f'You have {count} products across {len(cats)} categories.',
                                'total': count,
                                'by_category': cats,
                                'columns': ['Category', 'Count'],
                            }
                        }
                    return {
                        'agent': 'general', 'status': 'completed', 'confidence': 0.95,
                        'data': {
                            'analysis_type': 'product_count',
                            'message': f'Found {count} products' + (f' in {mentioned_category}.' if mentioned_category else '.'),
                            'total': count,
                        }
                    }

                result = await db.execute(
                    select(Product).where(and_(*filters))
                    .order_by(Product.name).limit(30)
                )
                products = result.scalars().all()
                items = [{'sku': p.sku, 'name': _clean(p.name, p.sku),
                          'category': p.category, 'price': float(p.price),
                          'inventory': p.inventory_level} for p in products]
                return {
                    'agent': 'general', 'status': 'completed', 'confidence': 0.95,
                    'data': {
                        'analysis_type': 'product_list',
                        'message': f'Found {len(items)} products' + (f' in {mentioned_category}.' if mentioned_category else '.'),
                        'items': items,
                        'columns': ['SKU', 'Name', 'Category', 'Price', 'Stock'],
                    }
                }

            # ── 3. PRICE queries ──────────────────────────────────────────────
            if any(k in q for k in ['price', 'cost', 'expensive', 'cheap', 'affordable', 'pricing']):
                filters = [Product.tenant_id == tenant_id]
                if mentioned_category:
                    filters.append(func.lower(Product.category).contains(mentioned_category))

                if any(k in q for k in ['average', 'avg', 'mean']):
                    avg_result = await db.execute(
                        select(
                            Product.category,
                            func.avg(Product.price).label('avg_price'),
                            func.min(Product.price).label('min_price'),
                            func.max(Product.price).label('max_price'),
                            func.count(Product.id).label('count'),
                        )
                        .where(and_(*filters))
                        .group_by(Product.category)
                        .order_by(desc('avg_price'))
                    )
                    rows = avg_result.all()
                    items = [{'category': r.category or 'Uncategorized',
                              'avg_price': round(float(r.avg_price), 2),
                              'min_price': round(float(r.min_price), 2),
                              'max_price': round(float(r.max_price), 2),
                              'count': r.count} for r in rows]
                    return {
                        'agent': 'general', 'status': 'completed', 'confidence': 0.93,
                        'data': {
                            'analysis_type': 'price_summary',
                            'message': f'Average price breakdown across {len(items)} categories.',
                            'items': items,
                            'columns': ['Category', 'Avg Price', 'Min', 'Max', 'Products'],
                        }
                    }

                order = desc(Product.price) if any(k in q for k in ['expensive', 'highest', 'most expensive']) \
                    else asc(Product.price)
                result = await db.execute(
                    select(Product).where(and_(*filters)).order_by(order).limit(20)
                )
                products = result.scalars().all()
                items = [{'sku': p.sku, 'name': _clean(p.name, p.sku),
                          'category': p.category, 'price': float(p.price)} for p in products]
                label = 'most expensive' if any(k in q for k in ['expensive', 'highest']) else 'cheapest'
                return {
                    'agent': 'general', 'status': 'completed', 'confidence': 0.93,
                    'data': {
                        'analysis_type': 'price_list',
                        'message': f'Top {len(items)} {label} products' + (f' in {mentioned_category}.' if mentioned_category else '.'),
                        'items': items,
                        'columns': ['SKU', 'Name', 'Category', 'Price'],
                    }
                }

            # ── 4. REVIEW / RATING queries ────────────────────────────────────
            if any(k in q for k in ['review', 'rating', 'rated', 'feedback', 'complaint',
                                     'satisfaction', 'worst rated', 'best rated', 'highest rated']):
                filters = [Review.tenant_id == tenant_id]
                if mentioned_category:
                    filters.append(func.lower(Product.category).contains(mentioned_category))

                order = desc('avg_rating') if any(k in q for k in ['best', 'highest', 'top']) \
                    else asc('avg_rating')

                result = await db.execute(
                    select(
                        Product.sku,
                        Product.name,
                        Product.category,
                        func.avg(Review.rating).label('avg_rating'),
                        func.count(Review.id).label('review_count'),
                    )
                    .join(Product, Review.product_id == Product.id)
                    .where(and_(*filters))
                    .group_by(Product.id, Product.sku, Product.name, Product.category)
                    .having(func.count(Review.id) > 0)
                    .order_by(order)
                    .limit(20)
                )
                rows = result.all()
                if not rows:
                    return {'agent': 'general', 'status': 'no_data', 'confidence': 0.9,
                            'data': {'message': 'No reviews found.', 'analysis_type': 'reviews', 'items': []}}
                items = [{'sku': r.sku, 'name': _clean(r.name, r.sku),
                          'category': r.category,
                          'avg_rating': round(float(r.avg_rating), 2),
                          'review_count': r.review_count} for r in rows]
                overall_avg = sum(i['avg_rating'] for i in items) / len(items)
                return {
                    'agent': 'general', 'status': 'completed', 'confidence': 0.91,
                    'data': {
                        'analysis_type': 'reviews',
                        'message': f'Found {len(items)} products with reviews. Overall avg rating: {overall_avg:.1f}/5.',
                        'items': items,
                        'columns': ['SKU', 'Name', 'Category', 'Avg Rating', 'Reviews'],
                    }
                }

            # ── 5. MARKETPLACE queries ────────────────────────────────────────
            if any(k in q for k in ['marketplace', 'platform', 'amazon', 'flipkart', 'channel']):
                result = await db.execute(
                    select(
                        Product.marketplace,
                        func.count(Product.id).label('product_count'),
                        func.sum(SalesRecord.revenue).label('total_revenue'),
                    )
                    .outerjoin(SalesRecord, and_(
                        SalesRecord.product_id == Product.id,
                        SalesRecord.tenant_id == tenant_id
                    ))
                    .where(Product.tenant_id == tenant_id)
                    .group_by(Product.marketplace)
                    .order_by(desc('total_revenue'))
                )
                rows = result.all()
                items = [{'marketplace': r.marketplace or 'Unknown',
                          'products': r.product_count,
                          'revenue': round(float(r.total_revenue or 0), 2)} for r in rows]
                return {
                    'agent': 'general', 'status': 'completed', 'confidence': 0.93,
                    'data': {
                        'analysis_type': 'marketplace',
                        'message': f'Performance across {len(items)} marketplaces.',
                        'items': items,
                        'columns': ['Marketplace', 'Products', 'Revenue'],
                    }
                }

            # ── 6. REVENUE / SALES queries (category-specific or general) ─────
            if any(k in q for k in ['revenue', 'sales', 'earning', 'income', 'sold', 'selling',
                                     'not selling', 'poor sales', 'low sales', 'performance']):
                if mentioned_category:
                    # Category-specific deep dive
                    result = await db.execute(
                        select(
                            Product.sku,
                            Product.name,
                            Product.price,
                            Product.inventory_level,
                            func.coalesce(func.sum(SalesRecord.quantity), 0).label('units_sold'),
                            func.coalesce(func.sum(SalesRecord.revenue), 0).label('revenue'),
                            func.coalesce(func.count(Review.id), 0).label('review_count'),
                            func.coalesce(func.avg(Review.rating), 0).label('avg_rating'),
                        )
                        .outerjoin(SalesRecord, and_(
                            SalesRecord.product_id == Product.id,
                            SalesRecord.tenant_id == tenant_id
                        ))
                        .outerjoin(Review, and_(
                            Review.product_id == Product.id,
                            Review.tenant_id == tenant_id
                        ))
                        .where(
                            Product.tenant_id == tenant_id,
                            func.lower(Product.category).contains(mentioned_category)
                        )
                        .group_by(Product.id, Product.sku, Product.name, Product.price, Product.inventory_level)
                        .order_by(desc('revenue'))
                    )
                    rows = result.all()
                    if not rows:
                        return {'agent': 'general', 'status': 'no_data', 'confidence': 0.9,
                                'data': {'message': f'No products found in {mentioned_category}.',
                                         'analysis_type': 'category_deep_dive', 'items': []}}
                    items = [{
                        'sku': r.sku,
                        'name': _clean(r.name, r.sku),
                        'price': float(r.price),
                        'inventory': r.inventory_level,
                        'units_sold': int(r.units_sold),
                        'revenue': round(float(r.revenue), 2),
                        'review_count': int(r.review_count),
                        'avg_rating': round(float(r.avg_rating), 2) if r.avg_rating else 0,
                    } for r in rows]
                    total_rev = sum(i['revenue'] for i in items)
                    total_units = sum(i['units_sold'] for i in items)
                    zero_sales = [i for i in items if i['units_sold'] == 0]
                    msg = (f'{mentioned_category.title()} category: {len(items)} products, '
                           f'₹{total_rev:,.2f} revenue, {total_units:,} units sold.')
                    if zero_sales:
                        msg += f' {len(zero_sales)} products have zero sales.'
                    return {
                        'agent': 'general', 'status': 'completed', 'confidence': 0.93,
                        'data': {
                            'analysis_type': 'category_deep_dive',
                            'category': mentioned_category,
                            'message': msg,
                            'items': items,
                            'total_revenue': total_rev,
                            'total_units': total_units,
                            'zero_sales_count': len(zero_sales),
                            'columns': ['SKU', 'Name', 'Price', 'Stock', 'Units Sold', 'Revenue', 'Reviews', 'Avg Rating'],
                        }
                    }
                else:
                    # Overall revenue by category
                    result = await db.execute(
                        select(
                            Product.category,
                            func.sum(SalesRecord.revenue).label('total_revenue'),
                            func.sum(SalesRecord.quantity).label('total_units'),
                            func.count(SalesRecord.id).label('order_count'),
                        )
                        .join(Product, SalesRecord.product_id == Product.id)
                        .where(SalesRecord.tenant_id == tenant_id)
                        .group_by(Product.category)
                        .order_by(desc('total_revenue'))
                    )
                    rows = result.all()
                    if not rows:
                        return {'agent': 'general', 'status': 'no_data', 'confidence': 0.9,
                                'data': {'message': 'No sales data found.', 'analysis_type': 'revenue_by_category', 'items': []}}
                    items = [{'category': r.category or 'Uncategorized',
                              'revenue': round(float(r.total_revenue), 2),
                              'units': int(r.total_units),
                              'orders': int(r.order_count)} for r in rows]
                    top = items[0]
                    return {
                        'agent': 'general', 'status': 'completed', 'confidence': 0.95,
                        'data': {
                            'analysis_type': 'revenue_by_category',
                            'message': f'Revenue across {len(items)} categories. Top: {top["category"]} (₹{top["revenue"]:,.2f}).',
                            'items': items,
                            'columns': ['Category', 'Revenue', 'Units', 'Orders'],
                        }
                    }

            # ── 7. PRODUCT DETAIL / SPECIFIC PRODUCT ─────────────────────────
            # e.g. "tell me about yoga mat", "what is the price of kettle"
            # Only trigger if the query explicitly asks about a specific product/item
            PRODUCT_SEARCH_TRIGGERS = [
                'tell me about', 'what is', 'show me', 'find product', 'search for',
                'details of', 'info on', 'information about', 'product called',
                'item called', 'sku', 'product named',
            ]
            is_product_search = any(t in q for t in PRODUCT_SEARCH_TRIGGERS)
            # Also block business/summary queries from falling into product search
            BUSINESS_QUERY_SIGNALS = [
                'summary', 'overview', 'report', 'quarter', 'board', 'executive',
                'business', 'performance', 'health', 'status', 'dashboard',
                'investor', 'stakeholder', 'month', 'annual', 'year to date',
            ]
            is_business_query = any(t in q for t in BUSINESS_QUERY_SIGNALS)

            stop_words = {'what', 'is', 'the', 'of', 'for', 'me', 'about', 'show',
                          'tell', 'give', 'get', 'find', 'a', 'an', 'my', 'our', 'i', 'how'}
            words = [w for w in re.findall(r'\b[a-z]+\b', q) if w not in stop_words and len(w) > 2]
            if words and is_product_search and not is_business_query:
                # Try to find products matching any of the keywords
                keyword_filters = [Product.tenant_id == tenant_id]
                name_conditions = [func.lower(Product.name).contains(w) for w in words[:4]]
                keyword_filters.append(or_(*name_conditions))
                result = await db.execute(
                    select(Product).where(and_(*keyword_filters)).limit(10)
                )
                products = result.scalars().all()
                if products:
                    items = [{'sku': p.sku, 'name': _clean(p.name, p.sku),
                              'category': p.category, 'price': float(p.price),
                              'inventory': p.inventory_level,
                              'marketplace': p.marketplace} for p in products]
                    return {
                        'agent': 'general', 'status': 'completed', 'confidence': 0.85,
                        'data': {
                            'analysis_type': 'product_search',
                            'message': f'Found {len(items)} matching products.',
                            'items': items,
                            'columns': ['SKU', 'Name', 'Category', 'Price', 'Stock', 'Marketplace'],
                        }
                    }

            # ── 8. FALLBACK: return a summary of what data is available ───────
            counts = {}
            for model, label in [(Product, 'products'), (SalesRecord, 'sales_records'), (Review, 'reviews')]:
                c = await db.execute(select(func.count(model.id)).where(model.tenant_id == tenant_id))
                counts[label] = c.scalar()

            return {
                'agent': 'general', 'status': 'completed', 'confidence': 0.5,
                'data': {
                    'analysis_type': 'data_summary',
                    'message': (
                        f"I couldn't find a specific match for your query. "
                        f"Your database has {counts['products']} products, "
                        f"{counts['sales_records']} sales records, and {counts['reviews']} reviews. "
                        f"Try asking about revenue, inventory, pricing, reviews, or a specific category."
                    ),
                    'available_data': counts,
                }
            }

        except Exception as e:
            logger.error(f"General agent failed: {e}", exc_info=True)
            return {'agent': 'general', 'status': 'error', 'confidence': 0.0,
                    'data': {'message': f'Error processing query: {str(e)}'}}

    def handle_agent_failure(
        self,
        agent: AgentType,
        error: Exception
    ) -> FallbackStrategy:
        """
        Determine fallback strategy for agent failure.
        
        Args:
            agent: Failed agent type
            error: Exception that occurred
            
        Returns:
            FallbackStrategy to use
        """
        # Timeout errors: try to use cache
        if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
            return FallbackStrategy.USE_CACHE
        
        # For critical agents, retry once
        if agent in [AgentType.PRICING, AgentType.SENTIMENT]:
            return FallbackStrategy.RETRY
        
        # For non-critical agents, skip and continue
        return FallbackStrategy.SKIP
    
    def enforce_resource_limits(
        self,
        execution_time: float,
        mode: ExecutionMode
    ) -> bool:
        """
        Check if execution is within resource limits.
        
        Args:
            execution_time: Current execution time in seconds
            mode: Execution mode
            
        Returns:
            True if within limits, False otherwise
        """
        # Quick mode: 2 minute limit
        if mode == ExecutionMode.QUICK and execution_time > 120:
            return False
        
        # Deep mode: 10 minute limit
        if mode == ExecutionMode.DEEP and execution_time > 600:
            return False
        
        return True
    
    def _record_execution(
        self,
        plan: ExecutionPlan,
        results: List[AgentResult]
    ) -> None:
        """Record execution for monitoring"""
        record = {
            'timestamp': datetime.utcnow(),
            'tenant_id': str(self.tenant_id),
            'mode': plan.execution_mode.value,
            'agents': [task.agent_type.value for task in plan.tasks],
            'success_count': sum(1 for r in results if r.success),
            'failure_count': sum(1 for r in results if not r.success),
            'total_time': sum(r.execution_time for r in results),
            'results': [
                {
                    'agent': r.agent_type.value,
                    'success': r.success,
                    'time': r.execution_time,
                    'error': r.error
                }
                for r in results
            ]
        }
        
        self.execution_history.append(record)
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'success_rate': 0.0,
                'avg_execution_time': 0.0
            }
        
        total = len(self.execution_history)
        successful = sum(
            1 for record in self.execution_history
            if record['failure_count'] == 0
        )
        
        avg_time = sum(
            record['total_time'] for record in self.execution_history
        ) / total
        
        return {
            'total_executions': total,
            'success_rate': successful / total,
            'avg_execution_time': avg_time,
            'by_mode': self._stats_by_mode()
        }
    
    def _stats_by_mode(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics broken down by execution mode"""
        stats = {}
        
        for mode in [ExecutionMode.QUICK, ExecutionMode.DEEP]:
            mode_records = [
                r for r in self.execution_history
                if r['mode'] == mode.value
            ]
            
            if mode_records:
                stats[mode.value] = {
                    'count': len(mode_records),
                    'avg_time': sum(r['total_time'] for r in mode_records) / len(mode_records),
                    'success_rate': sum(
                        1 for r in mode_records if r['failure_count'] == 0
                    ) / len(mode_records)
                }
        
        return stats
