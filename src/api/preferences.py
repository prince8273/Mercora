"""User preferences API endpoints"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.models.user import User
from src.models.user_preferences import UserPreferences
from src.schemas.preferences import (
    UserPreferencesRequest,
    UserPreferencesResponse
)
from src.auth.dependencies import get_current_active_user, get_tenant_id

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=UserPreferencesResponse)
async def get_user_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
) -> UserPreferencesResponse:
    """
    Get user preferences (TENANT-ISOLATED).
    
    Retrieves the current user's preferences including KPI preferences,
    marketplace focus, and business goals.
    
    Args:
        db: Database session
        current_user: Authenticated user
        tenant_id: Tenant ID from JWT token
        
    Returns:
        User preferences
    """
    # Fetch user preferences (TENANT-FILTERED)
    result = await db.execute(
        select(UserPreferences).where(
            UserPreferences.user_id == current_user.id,
            UserPreferences.tenant_id == tenant_id
        )
    )
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Return default preferences if none exist
        return UserPreferencesResponse(
            user_id=current_user.id,
            tenant_id=tenant_id,
            kpi_preferences={},
            marketplace_focus=[],
            business_goals={}
        )
    
    return UserPreferencesResponse.model_validate(preferences)


@router.put("", response_model=UserPreferencesResponse)
async def update_user_preferences(
    request: UserPreferencesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
) -> UserPreferencesResponse:
    """
    Update user preferences (TENANT-ISOLATED).
    
    Creates or updates the current user's preferences including KPI preferences,
    marketplace focus, and business goals.
    
    Args:
        request: User preferences update request
        db: Database session
        current_user: Authenticated user
        tenant_id: Tenant ID from JWT token
        
    Returns:
        Updated user preferences
    """
    # Check if preferences exist (TENANT-FILTERED)
    result = await db.execute(
        select(UserPreferences).where(
            UserPreferences.user_id == current_user.id,
            UserPreferences.tenant_id == tenant_id
        )
    )
    preferences = result.scalar_one_or_none()
    
    if preferences:
        # Update existing preferences
        if request.kpi_preferences is not None:
            preferences.kpi_preferences = request.kpi_preferences
        if request.marketplace_focus is not None:
            preferences.marketplace_focus = request.marketplace_focus
        if request.business_goals is not None:
            preferences.business_goals = request.business_goals
    else:
        # Create new preferences
        preferences = UserPreferences(
            user_id=current_user.id,
            tenant_id=tenant_id,
            kpi_preferences=request.kpi_preferences or {},
            marketplace_focus=request.marketplace_focus or [],
            business_goals=request.business_goals or {}
        )
        db.add(preferences)
    
    await db.commit()
    await db.refresh(preferences)
    
    return UserPreferencesResponse.model_validate(preferences)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
) -> None:
    """
    Delete user preferences (TENANT-ISOLATED).
    
    Removes the current user's preferences, resetting them to defaults.
    
    Args:
        db: Database session
        current_user: Authenticated user
        tenant_id: Tenant ID from JWT token
    """
    # Fetch and delete preferences (TENANT-FILTERED)
    result = await db.execute(
        select(UserPreferences).where(
            UserPreferences.user_id == current_user.id,
            UserPreferences.tenant_id == tenant_id
        )
    )
    preferences = result.scalar_one_or_none()
    
    if preferences:
        await db.delete(preferences)
        await db.commit()
