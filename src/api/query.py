"""Query execution API endpoints"""
import re
from uuid import UUID, uuid4
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.models.product import Product
from src.models.review import Review
from src.models.user import User
from src.schemas.query import QueryRequest
from src.schemas.report import StructuredReport
from src.schemas.pricing import (
    PricingAnalysisRequest,
    MarginConstraints
)
from src.schemas.sentiment import SentimentAnalysisResult
from src.agents.pricing_intelligence_v2 import EnhancedPricingIntelligenceAgent
from src.agents.sentiment_analysis_v2 import EnhancedSentimentAgent
from src.agents.data_qa_agent import DataQAAgent
from src.schemas.product import ProductResponse
from src.schemas.review import ReviewResponse
from src.auth.dependencies import get_current_active_user, get_tenant_id

router = APIRouter(prefix="/query", tags=["query"])


@router.get("/history")
async def get_query_history(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Get query history for the current user (TENANT-ISOLATED).
    
    Args:
        limit: Maximum number of queries to return
        offset: Number of queries to skip
        current_user: Authenticated user
        tenant_id: Tenant ID from JWT token
        
    Returns:
        List of historical queries
    """
    # For MVP, return empty list
    # In production, this would query a query_history table
    return {
        "data": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }


@router.post("", response_model=StructuredReport)
async def execute_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
) -> StructuredReport:
    """
    Execute a natural language query using orchestration layer (TENANT-ISOLATED).
    
    ORCHESTRATED FLOW:
    1. Query Router: Pattern matching and execution mode determination
    2. LLM Reasoning Engine: Query understanding and agent selection
    3. Execution Service: Parallel agent execution with timeout handling
    4. Result Synthesizer: Multi-agent result aggregation
    
    Args:
        request: Query request with query text and optional parameters
        db: Database session
        current_user: Authenticated user
        tenant_id: Tenant ID from JWT token
        
    Returns:
        Structured report with synthesized intelligence
    """
    import logging
    from src.orchestration.query_router import QueryRouter
    from src.orchestration.llm_reasoning_engine import LLMReasoningEngine
    from src.orchestration.execution_service import ExecutionService
    from src.orchestration.result_synthesizer import ResultSynthesizer
    from src.schemas.orchestration import ExecutionMode
    
    logger = logging.getLogger(__name__)
    logger.info(f"[ORCHESTRATION] Processing query: {request.query_text[:100]}...")
    
    try:
        # STEP 1: Query Router - Deterministic pattern matching
        query_router = QueryRouter(tenant_id=tenant_id)
        routing_decision = query_router.route_query(request.query_text)
        
        logger.info(f"[ORCHESTRATION] Routing decision: mode={routing_decision.execution_mode.value}, "
                    f"agents={[a.value for a in routing_decision.required_agents]}, "
                    f"use_cache={routing_decision.use_cache}")
        
        # Check cache if Quick Mode
        if routing_decision.use_cache and routing_decision.cache_key:
            cached_result = query_router.check_cache(routing_decision.cache_key)
            if cached_result:
                logger.info("[ORCHESTRATION] Cache hit! Returning cached result")
                # Return cached result (would need to deserialize from cache)
                # For MVP, skip cache and continue to execution
                pass
        
        # STEP 2: LLM Reasoning Engine - Query understanding
        llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
        intent, parameters = llm_engine.understand_query(request.query_text)
        
        # Select agents based on intent
        suggested_agents = llm_engine.select_agents(intent, parameters)
        
        logger.info(f"[ORCHESTRATION] Query understanding: intent={intent}, "
                    f"parameters={parameters}, "
                    f"suggested_agents={[a.value for a in suggested_agents]}")
        
        # Combine router and LLM agent suggestions
        required_agents = list(set(routing_decision.required_agents + suggested_agents))
        
        # STEP 3: Create Execution Plan
        execution_mode = routing_decision.execution_mode
        execution_plan = llm_engine.generate_execution_plan(
            query_id=str(uuid4()),
            query=request.query_text,
            intent=intent,
            parameters=parameters,
            execution_mode=execution_mode
        )
        
        logger.info(f"[ORCHESTRATION] Execution plan: {len(execution_plan.tasks)} tasks, "
                    f"{len(execution_plan.parallel_groups)} parallel groups, "
                    f"estimated duration={execution_plan.estimated_duration}")
        
        # STEP 4: Execute Plan with Execution Service
        execution_service = ExecutionService(tenant_id=tenant_id)
        
        # Prepare query data for agents
        product_ids = request.product_ids
        if not product_ids:
            product_ids = _extract_product_ids_from_query(request.query_text)
        
        # If still no product IDs, determine based on query intent (TENANT-FILTERED)
        if not product_ids:
            product_ids = await _get_relevant_products_for_query(
                db, tenant_id, request.query_text, intent.value  # Convert enum to string
            )
        
        query_data = {
            'product_ids': product_ids,
            'query_text': request.query_text,
            'analysis_type': request.analysis_type,
            'db': db,
            'tenant_id': tenant_id
        }
        
        # Execute agents
        agent_results = await execution_service.execute_plan(execution_plan, query_data)
        
        logger.info(f"[ORCHESTRATION] Execution complete: {len(agent_results)} results, "
                    f"{sum(1 for r in agent_results if r.success)} successful")
        
        # STEP 5: Synthesize Results
        query_id = str(uuid4())  # Generate unique query ID
        execution_metadata = {
            'execution_mode': execution_plan.mode.value,
            'agents_used': [agent.value for agent in execution_plan.agents],
            'execution_time': execution_plan.estimated_duration.total_seconds(),
            'parallel_execution': execution_plan.parallel_execution
        }
        
        result_synthesizer = ResultSynthesizer(tenant_id=tenant_id)
        structured_report = result_synthesizer.synthesize_results(
            query_id=query_id,
            query=request.query_text,
            agent_results=agent_results,
            execution_metadata=execution_metadata
        )
        
        logger.info(f"[ORCHESTRATION] Report synthesized: confidence={structured_report.overall_confidence}, "
                    f"insights={len(structured_report.insights)}, "
                    f"action_items={len(structured_report.action_items)}")
        
        # Log token usage if LLM was used
        token_usage = llm_engine.get_total_token_usage()
        if token_usage['total_tokens'] > 0:
            logger.info(f"[ORCHESTRATION] Token usage: {token_usage['total_tokens']} tokens, "
                        f"${token_usage['total_cost_usd']} cost")
        
        return structured_report
    
    except Exception as e:
        logger.error(f"[ORCHESTRATION] Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


async def _execute_pricing_analysis(
    product_ids: List[UUID],
    db: AsyncSession,
    qa_agent: DataQAAgent,
    tenant_id: UUID
):
    """
    Execute pricing analysis for the given products (TENANT-ISOLATED).
    
    Args:
        product_ids: List of product IDs to analyze
        db: Database session
        qa_agent: Data QA agent instance
        tenant_id: Tenant ID for filtering
        
    Returns:
        Pricing analysis response and QA report
    """
    from src.api.pricing import (
        _get_mock_competitor_products,
        _get_mock_historical_prices,
        _get_mock_competitor_data,
        _calculate_market_data
    )
    
    # Initialize enhanced agent (TENANT-AWARE)
    agent = EnhancedPricingIntelligenceAgent(tenant_id=tenant_id)
    
    # Fetch our products (TENANT-FILTERED)
    result = await db.execute(
        select(Product).where(
            Product.id.in_(product_ids),
            Product.tenant_id == tenant_id  # TENANT ISOLATION
        )
    )
    products = result.scalars().all()
    
    if not products:
        return None, None
    
    # Convert to response schemas
    our_products = [ProductResponse.model_validate(p) for p in products]
    
    # Layer 0: Assess data quality
    qa_report = qa_agent.assess_product_data_quality(our_products)
    
    # Get mock competitor data (for MVP)
    competitor_products = _get_mock_competitor_products(our_products)
    
    # Create product mappings
    all_mappings = []
    for our_product in our_products:
        mappings = agent.map_product_equivalence(our_product, competitor_products)
        all_mappings.extend(mappings)
    
    # Calculate price gaps
    price_gaps = agent.calculate_price_gaps(
        our_products,
        competitor_products,
        all_mappings
    )
    
    # Detect price changes
    historical_prices = _get_mock_historical_prices(our_products, competitor_products)
    price_changes = agent.detect_price_changes(historical_prices)
    
    # Extract promotions
    competitor_data = _get_mock_competitor_data(competitor_products)
    promotions = agent.extract_promotions(competitor_data)
    
    # Generate recommendations with QA-adjusted confidence
    recommendations = []
    margin_constraints = MarginConstraints(
        min_margin_percentage=20.0,
        max_discount_percentage=30.0
    )
    
    for our_product in our_products:
        market_data = _calculate_market_data(our_product, competitor_products, all_mappings)
        
        # Generate recommendation with QA integration
        recommendation = agent.suggest_dynamic_pricing_with_qa(
            our_product,
            market_data,
            margin_constraints,
            qa_report
        )
        recommendations.append(recommendation)
    
    from src.schemas.pricing import PricingAnalysisResponse
    return PricingAnalysisResponse(
        price_gaps=price_gaps,
        price_changes=price_changes,
        promotions=promotions,
        recommendations=recommendations
    ), qa_report


async def _execute_sentiment_analysis(
    product_ids: List[UUID],
    db: AsyncSession,
    qa_agent: DataQAAgent,
    tenant_id: UUID
) -> tuple:
    """
    Execute sentiment analysis for the given products (TENANT-ISOLATED).
    
    Args:
        product_ids: List of product IDs to analyze
        db: Database session
        qa_agent: Data QA agent instance
        tenant_id: Tenant ID for filtering
        
    Returns:
        List of sentiment analysis results or None if no reviews, and QA report
    """
    # Initialize enhanced agent (TENANT-AWARE)
    agent = EnhancedSentimentAgent(tenant_id=tenant_id)
    
    results = []
    all_reviews = []
    
    for product_id in product_ids:
        # Fetch reviews for this product (TENANT-FILTERED)
        result = await db.execute(
            select(Review).where(
                Review.product_id == product_id,
                Review.tenant_id == tenant_id  # TENANT ISOLATION
            )
        )
        review_records = result.scalars().all()
        
        if not review_records:
            # Skip products with no reviews
            continue
        
        # Convert to ReviewResponse objects
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
            for r in review_records
        ]
        
        all_reviews.extend(reviews)
        
        # Layer 0: Assess review data quality
        review_qa_report = qa_agent.assess_review_data_quality(reviews)
        
        # Perform sentiment analysis with QA integration
        analysis_result = agent.calculate_aggregate_sentiment_with_qa(
            reviews,
            review_qa_report
        )
        results.append(analysis_result)
    
    # Create overall QA report for all reviews
    overall_qa_report = qa_agent.assess_review_data_quality(all_reviews) if all_reviews else None
    
    return (results if results else None), overall_qa_report


def _extract_product_ids_from_query(query_text: str) -> List[UUID]:
    """
    Extract product IDs from query text using simple pattern matching.
    
    Args:
        query_text: The query text
        
    Returns:
        List of extracted product IDs
    """
    # Look for UUID patterns in the query
    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    matches = re.findall(uuid_pattern, query_text, re.IGNORECASE)
    
    product_ids = []
    for match in matches:
        try:
            product_ids.append(UUID(match))
        except ValueError:
            continue
    
    return product_ids


def _generate_executive_summary(
    query_text: str,
    pricing_analysis,
    sentiment_analysis,
    product_count: int
) -> str:
    """
    Generate executive summary from analysis results.
    
    Args:
        query_text: Original query text
        pricing_analysis: Pricing analysis results
        sentiment_analysis: Sentiment analysis results
        product_count: Number of products analyzed
        
    Returns:
        Executive summary text
    """
    summary_parts = []
    
    # Opening
    summary_parts.append(f"Analysis completed for {product_count} product(s).")
    
    # Pricing insights
    if pricing_analysis:
        gap_count = len(pricing_analysis.price_gaps)
        change_count = len(pricing_analysis.price_changes)
        promo_count = len(pricing_analysis.promotions)
        rec_count = len(pricing_analysis.recommendations)
        
        if gap_count > 0:
            avg_gap = sum(g.gap_percentage for g in pricing_analysis.price_gaps) / gap_count
            summary_parts.append(
                f"Identified {gap_count} price gap(s) with competitors, "
                f"averaging {avg_gap:.1f}% difference."
            )
        
        if change_count > 0:
            summary_parts.append(
                f"Detected {change_count} significant price change(s) in the market."
            )
        
        if promo_count > 0:
            summary_parts.append(
                f"Found {promo_count} active promotion(s) from competitors."
            )
        
        if rec_count > 0:
            summary_parts.append(
                f"Generated {rec_count} pricing recommendation(s) to optimize competitiveness."
            )
    
    # Sentiment insights
    if sentiment_analysis:
        total_reviews = sum(s.total_reviews for s in sentiment_analysis)
        avg_sentiment = sum(s.aggregate_sentiment for s in sentiment_analysis) / len(sentiment_analysis)
        
        sentiment_label = "positive" if avg_sentiment > 0.2 else "negative" if avg_sentiment < -0.2 else "neutral"
        
        summary_parts.append(
            f"Analyzed {total_reviews} customer review(s) with overall {sentiment_label} sentiment "
            f"(score: {avg_sentiment:.2f})."
        )
        
        # Count feature requests and complaints
        total_features = sum(len(s.feature_requests) for s in sentiment_analysis)
        total_complaints = sum(len(s.complaint_patterns) for s in sentiment_analysis)
        
        if total_features > 0:
            summary_parts.append(f"Identified {total_features} feature request(s) from customers.")
        
        if total_complaints > 0:
            summary_parts.append(f"Found {total_complaints} complaint pattern(s) requiring attention.")
    
    if not summary_parts:
        summary_parts.append("No significant insights found for the analyzed products.")
    
    return " ".join(summary_parts)


def _calculate_key_metrics(pricing_analysis, sentiment_analysis) -> dict:
    """
    Calculate key metrics from analysis results.
    
    Args:
        pricing_analysis: Pricing analysis results
        sentiment_analysis: Sentiment analysis results
        
    Returns:
        Dictionary of key metrics
    """
    metrics = {
        "products_analyzed": 0,
        "price_gaps_identified": 0,
        "price_changes_detected": 0,
        "promotions_found": 0,
        "recommendations_generated": 0
    }
    
    if pricing_analysis:
        metrics["price_gaps_identified"] = len(pricing_analysis.price_gaps)
        metrics["price_changes_detected"] = len(pricing_analysis.price_changes)
        metrics["promotions_found"] = len(pricing_analysis.promotions)
        metrics["recommendations_generated"] = len(pricing_analysis.recommendations)
        
        # Calculate average confidence from recommendations
        if pricing_analysis.recommendations:
            avg_confidence = sum(
                r.confidence_score for r in pricing_analysis.recommendations
            ) / len(pricing_analysis.recommendations)
            metrics["average_recommendation_confidence"] = round(avg_confidence, 2)
        
        # Calculate average price gap percentage
        if pricing_analysis.price_gaps:
            avg_gap = sum(
                abs(g.gap_percentage) for g in pricing_analysis.price_gaps
            ) / len(pricing_analysis.price_gaps)
            metrics["average_price_gap_percentage"] = round(avg_gap, 2)
    
    if sentiment_analysis:
        metrics["total_reviews_analyzed"] = sum(s.total_reviews for s in sentiment_analysis)
        
        if sentiment_analysis:
            avg_sentiment = sum(s.aggregate_sentiment for s in sentiment_analysis) / len(sentiment_analysis)
            metrics["average_sentiment_score"] = round(avg_sentiment, 2)
            
            # Count positive, negative, neutral
            total_positive = sum(s.sentiment_distribution.get("positive", 0) for s in sentiment_analysis)
            total_negative = sum(s.sentiment_distribution.get("negative", 0) for s in sentiment_analysis)
            total_neutral = sum(s.sentiment_distribution.get("neutral", 0) for s in sentiment_analysis)
            
            metrics["positive_reviews"] = total_positive
            metrics["negative_reviews"] = total_negative
            metrics["neutral_reviews"] = total_neutral
            
            # Feature requests and complaints
            metrics["feature_requests_identified"] = sum(len(s.feature_requests) for s in sentiment_analysis)
            metrics["complaint_patterns_found"] = sum(len(s.complaint_patterns) for s in sentiment_analysis)
    
    return metrics


def _calculate_confidence(pricing_analysis, sentiment_analysis) -> float:
    """
    Calculate overall confidence score for the report.
    
    Args:
        pricing_analysis: Pricing analysis results
        sentiment_analysis: Sentiment analysis results
        
    Returns:
        Confidence score between 0 and 1
    """
    confidences = []
    
    # Add pricing confidence
    if pricing_analysis and pricing_analysis.recommendations:
        pricing_confidences = [r.confidence_score for r in pricing_analysis.recommendations]
        avg_pricing_confidence = sum(pricing_confidences) / len(pricing_confidences)
        confidences.append(avg_pricing_confidence)
    
    # Add sentiment confidence
    if sentiment_analysis:
        sentiment_confidences = [s.confidence_score for s in sentiment_analysis]
        avg_sentiment_confidence = sum(sentiment_confidences) / len(sentiment_confidences)
        confidences.append(avg_sentiment_confidence)
    
    if not confidences:
        return 0.5  # Default medium confidence
    
    # Average all confidences
    overall_confidence = sum(confidences) / len(confidences)
    
    return round(overall_confidence, 2)


async def _get_relevant_products_for_query(
    db: AsyncSession,
    tenant_id: UUID,
    query_text: str,
    intent: str
) -> List[UUID]:
    """
    Get relevant product IDs based on query intent and content.
    
    Args:
        db: Database session
        tenant_id: Tenant ID for filtering
        query_text: The query text
        intent: Query intent from LLM
        
    Returns:
        List of product IDs relevant to the query
    """
    from sqlalchemy import select, func, desc
    from src.models.sales_record import SalesRecord
    from src.models.review import Review
    
    query_lower = query_text.lower()
    
    # Check for "top selling" or "most selling" or "best selling" queries
    if any(keyword in query_lower for keyword in ['top selling', 'most selling', 'best selling', 'highest sales', 'top products']):
        # Get products with most sales (TENANT-FILTERED)
        result = await db.execute(
            select(
                SalesRecord.product_id,
                func.sum(SalesRecord.quantity).label('total_quantity')
            )
            .where(SalesRecord.tenant_id == tenant_id)
            .group_by(SalesRecord.product_id)
            .order_by(desc('total_quantity'))
            .limit(10)
        )
        sales_data = result.all()
        
        if sales_data:
            return [row.product_id for row in sales_data]
    
    # Check for "low inventory" or "stock" queries
    if any(keyword in query_lower for keyword in ['low inventory', 'out of stock', 'stock level', 'inventory']):
        # Get products with low inventory (TENANT-FILTERED)
        result = await db.execute(
            select(Product)
            .where(
                Product.tenant_id == tenant_id,
                Product.inventory_level < 50  # Low inventory threshold
            )
            .order_by(Product.inventory_level)
            .limit(10)
        )
        products = result.scalars().all()
        
        if products:
            return [p.id for p in products]
    
    # Check for "negative reviews" or "poor ratings" queries
    if any(keyword in query_lower for keyword in ['negative', 'poor rating', 'low rating', 'bad reviews', 'complaints']):
        # Get products with low ratings (TENANT-FILTERED)
        result = await db.execute(
            select(
                Review.product_id,
                func.avg(Review.rating).label('avg_rating')
            )
            .where(Review.tenant_id == tenant_id)
            .group_by(Review.product_id)
            .having(func.avg(Review.rating) < 3.0)
            .order_by('avg_rating')
            .limit(10)
        )
        review_data = result.all()
        
        if review_data:
            return [row.product_id for row in review_data]
    
    # Check for "high price" or "expensive" queries
    if any(keyword in query_lower for keyword in ['expensive', 'high price', 'costly', 'premium']):
        # Get most expensive products (TENANT-FILTERED)
        result = await db.execute(
            select(Product)
            .where(Product.tenant_id == tenant_id)
            .order_by(desc(Product.price))
            .limit(10)
        )
        products = result.scalars().all()
        
        if products:
            return [p.id for p in products]
    
    # Check for "low price" or "cheap" queries
    if any(keyword in query_lower for keyword in ['cheap', 'low price', 'affordable', 'budget']):
        # Get least expensive products (TENANT-FILTERED)
        result = await db.execute(
            select(Product)
            .where(Product.tenant_id == tenant_id)
            .order_by(Product.price)
            .limit(10)
        )
        products = result.scalars().all()
        
        if products:
            return [p.id for p in products]
    
    # Default: Get all products (TENANT-FILTERED)
    result = await db.execute(
        select(Product)
        .where(Product.tenant_id == tenant_id)
        .limit(20)  # Increased from 5 to 20 for better analysis
    )
    products = result.scalars().all()
    
    return [p.id for p in products] if products else []
