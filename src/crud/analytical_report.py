"""CRUD operations for AnalyticalReport model"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.analytical_report import AnalyticalReport


async def create_analytical_report(
    db: AsyncSession,
    tenant_id: UUID,
    query_id: UUID,
    executive_summary: str,
    key_metrics: dict,
    agent_results: list,
    action_items: list,
    overall_confidence: float,
    execution_mode: str,
    risk_assessment: Optional[dict] = None,
    data_quality_warnings: Optional[list] = None,
    supporting_evidence: Optional[list] = None,
    execution_time_ms: Optional[float] = None,
    agents_used: Optional[list] = None
) -> AnalyticalReport:
    """
    Create a new analytical report
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        query_id: Query UUID
        executive_summary: High-level summary
        key_metrics: Dictionary of key metrics
        agent_results: List of agent results
        action_items: List of action items
        overall_confidence: Overall confidence score
        execution_mode: QUICK or DEEP
        risk_assessment: Optional risk assessment
        data_quality_warnings: Optional list of warnings
        supporting_evidence: Optional supporting evidence
        execution_time_ms: Optional execution time
        agents_used: Optional list of agents used
    
    Returns:
        Created AnalyticalReport object
    """
    report = AnalyticalReport(
        tenant_id=tenant_id,
        query_id=query_id,
        executive_summary=executive_summary,
        key_metrics=key_metrics,
        agent_results=agent_results,
        action_items=action_items,
        overall_confidence=overall_confidence,
        execution_mode=execution_mode,
        risk_assessment=risk_assessment,
        data_quality_warnings=data_quality_warnings,
        supporting_evidence=supporting_evidence,
        execution_time_ms=execution_time_ms,
        agents_used=agents_used
    )
    
    db.add(report)
    await db.flush()
    await db.refresh(report)
    
    return report


async def get_analytical_report_by_id(
    db: AsyncSession,
    report_id: UUID,
    tenant_id: UUID
) -> Optional[AnalyticalReport]:
    """Get an analytical report by ID"""
    result = await db.execute(
        select(AnalyticalReport).where(
            AnalyticalReport.id == report_id,
            AnalyticalReport.tenant_id == tenant_id
        )
    )
    return result.scalar_one_or_none()


async def get_analytical_reports_by_query(
    db: AsyncSession,
    query_id: UUID,
    tenant_id: UUID
) -> List[AnalyticalReport]:
    """Get all analytical reports for a query"""
    result = await db.execute(
        select(AnalyticalReport).where(
            AnalyticalReport.query_id == query_id,
            AnalyticalReport.tenant_id == tenant_id
        ).order_by(desc(AnalyticalReport.created_at))
    )
    return result.scalars().all()


async def get_recent_analytical_reports(
    db: AsyncSession,
    tenant_id: UUID,
    limit: int = 10
) -> List[AnalyticalReport]:
    """Get recent analytical reports for a tenant"""
    result = await db.execute(
        select(AnalyticalReport).where(
            AnalyticalReport.tenant_id == tenant_id
        ).order_by(desc(AnalyticalReport.created_at)).limit(limit)
    )
    return result.scalars().all()
