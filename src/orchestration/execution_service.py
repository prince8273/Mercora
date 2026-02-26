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
        else:
            # Unknown agent type
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
            
            # Convert price gaps to dicts for serialization
            price_gaps_list = [
                {
                    'product_id': str(gap.product_id),
                    'our_price': float(gap.our_price),
                    'competitor_price': float(gap.competitor_price),
                    'gap_amount': float(gap.gap_amount),
                    'gap_percentage': float(gap.gap_percentage),
                    'confidence': 0.85  # Default confidence
                }
                for gap in price_gaps
            ]
            
            logger.info("Pricing agent: Returning results")
            
            return {
                'agent': 'pricing',
                'status': 'completed',
                'confidence': avg_confidence,
                'data': {
                    'message': f'Analyzed {len(our_products)} products, found {len(price_gaps)} price gaps',
                    'product_count': len(our_products),
                    'price_gaps': price_gaps_list,  # Return the actual list, not the count
                    'average_price': float(sum(p.price for p in our_products) / len(our_products)) if our_products else 0,
                    'price_change_pct': 0.0,  # Would calculate from historical data
                    'recommendations': [
                        {
                            'title': f'Price adjustment for product',
                            'description': f'Consider adjusting price by {gap.gap_percentage:.1f}%',
                            'priority': 'high' if abs(gap.gap_percentage) > 10 else 'medium',
                            'impact': 'high',
                            'urgency': 'medium',
                            'confidence': 0.85
                        }
                        for gap in price_gaps[:3]  # Top 3 gaps
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
        
        # Calculate average sentiment
        avg_sentiment = sentiment_result.aggregate_sentiment
        
        return {
            'agent': 'sentiment',
            'status': 'completed',
            'confidence': sentiment_result.confidence_score,
            'data': {
                'message': f'Analyzed {len(reviews)} reviews with {avg_sentiment:.2f} average sentiment',
                'review_count': len(reviews),
                'aggregate_sentiment_score': avg_sentiment,  # Add this field for synthesizer
                'average_sentiment': avg_sentiment,
                'sentiment_change': 0.0,  # Would calculate from historical data
                'positive_count': sentiment_result.sentiment_distribution.get('positive', 0),
                'negative_count': sentiment_result.sentiment_distribution.get('negative', 0),
                'neutral_count': sentiment_result.sentiment_distribution.get('neutral', 0),
                'feature_requests': [],  # Add empty list for now (would extract from reviews)
                'complaint_patterns': [],  # Add empty list for now (would extract from reviews)
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
