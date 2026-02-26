"""User preferences schemas"""
from uuid import UUID
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class UserPreferencesRequest(BaseModel):
    """Request schema for updating user preferences"""
    kpi_preferences: Optional[Dict[str, Any]] = Field(
        None,
        description="User's KPI preferences (e.g., {'revenue': True, 'margin': True})"
    )
    marketplace_focus: Optional[List[str]] = Field(
        None,
        description="List of marketplaces to prioritize (e.g., ['amazon', 'ebay'])"
    )
    business_goals: Optional[Dict[str, Any]] = Field(
        None,
        description="User's business goals (e.g., {'target_revenue': 1000000, 'target_margin': 0.25})"
    )


class UserPreferencesResponse(BaseModel):
    """Response schema for user preferences"""
    user_id: UUID
    tenant_id: UUID
    kpi_preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="User's KPI preferences"
    )
    marketplace_focus: List[str] = Field(
        default_factory=list,
        description="List of prioritized marketplaces"
    )
    business_goals: Dict[str, Any] = Field(
        default_factory=dict,
        description="User's business goals"
    )
    
    model_config = {
        "from_attributes": True
    }
