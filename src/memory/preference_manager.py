"""
Preference Manager - Manages user preferences and personalization

This module provides specialized management for user preferences,
KPI tracking, marketplace focus, and business goals.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from src.memory.models import UserPreferences, KPI

logger = logging.getLogger(__name__)


class PreferenceManager:
    """
    Manages user preferences and personalization settings.
    
    Provides specialized operations for KPI preferences, marketplace focus,
    and business goal management.
    """
    
    def __init__(self):
        """Initialize preference manager"""
        self._preferences: Dict[UUID, UserPreferences] = {}
        logger.info("PreferenceManager initialized")
    
    def store_kpi_preferences(
        self,
        user_id: UUID,
        tenant_id: UUID,
        kpis: Dict[str, bool]
    ) -> None:
        """
        Store KPI preferences for a user.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            kpis: Dictionary of KPI name -> enabled status
        """
        preferences = self._get_or_create_preferences(user_id, tenant_id)
        preferences.kpi_preferences = kpis
        preferences.updated_at = datetime.utcnow()
        
        logger.info(f"Stored KPI preferences for user_id={user_id}: {len(kpis)} KPIs")
    
    def get_kpi_preferences(
        self,
        user_id: UUID
    ) -> Dict[str, bool]:
        """
        Get KPI preferences for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            Dictionary of KPI name -> enabled status
        """
        preferences = self._preferences.get(user_id)
        
        if preferences:
            return preferences.kpi_preferences
        
        # Return default KPIs if no preferences set
        return {
            "revenue": True,
            "margin": True,
            "inventory_turnover": True,
            "customer_satisfaction": True
        }
    
    def set_marketplace_focus(
        self,
        user_id: UUID,
        tenant_id: UUID,
        marketplaces: List[str]
    ) -> None:
        """
        Set marketplace focus for a user.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            marketplaces: List of marketplace names to focus on
        """
        preferences = self._get_or_create_preferences(user_id, tenant_id)
        preferences.marketplace_focus = marketplaces
        preferences.updated_at = datetime.utcnow()
        
        logger.info(f"Set marketplace focus for user_id={user_id}: {marketplaces}")
    
    def get_marketplace_focus(
        self,
        user_id: UUID
    ) -> List[str]:
        """
        Get marketplace focus for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            List of marketplace names
        """
        preferences = self._preferences.get(user_id)
        
        if preferences and preferences.marketplace_focus:
            return preferences.marketplace_focus
        
        # Return empty list if no focus set (all marketplaces)
        return []
    
    def update_business_goals(
        self,
        user_id: UUID,
        tenant_id: UUID,
        goals: Dict[str, Any]
    ) -> None:
        """
        Update business goals for a user.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            goals: Dictionary of business goals
        """
        preferences = self._get_or_create_preferences(user_id, tenant_id)
        preferences.business_goals = goals
        preferences.updated_at = datetime.utcnow()
        
        logger.info(f"Updated business goals for user_id={user_id}")
    
    def get_business_goals(
        self,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Get business goals for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            Dictionary of business goals
        """
        preferences = self._preferences.get(user_id)
        
        if preferences:
            return preferences.business_goals
        
        return {}
    
    def get_all_preferences(
        self,
        user_id: UUID
    ) -> Optional[UserPreferences]:
        """
        Get all preferences for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            UserPreferences object if found, None otherwise
        """
        return self._preferences.get(user_id)
    
    def update_preferences(
        self,
        user_id: UUID,
        tenant_id: UUID,
        kpi_preferences: Optional[Dict[str, bool]] = None,
        marketplace_focus: Optional[List[str]] = None,
        business_goals: Optional[Dict[str, Any]] = None,
        notification_settings: Optional[Dict[str, bool]] = None
    ) -> UserPreferences:
        """
        Update multiple preference fields at once.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            kpi_preferences: Optional KPI preferences
            marketplace_focus: Optional marketplace focus list
            business_goals: Optional business goals
            notification_settings: Optional notification settings
            
        Returns:
            Updated UserPreferences object
        """
        preferences = self._get_or_create_preferences(user_id, tenant_id)
        
        if kpi_preferences is not None:
            preferences.kpi_preferences = kpi_preferences
        
        if marketplace_focus is not None:
            preferences.marketplace_focus = marketplace_focus
        
        if business_goals is not None:
            preferences.business_goals = business_goals
        
        if notification_settings is not None:
            preferences.notification_settings = notification_settings
        
        preferences.updated_at = datetime.utcnow()
        
        logger.info(f"Updated preferences for user_id={user_id}")
        return preferences
    
    def delete_preferences(
        self,
        user_id: UUID
    ) -> bool:
        """
        Delete all preferences for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            True if preferences were deleted, False if not found
        """
        if user_id in self._preferences:
            del self._preferences[user_id]
            logger.info(f"Deleted preferences for user_id={user_id}")
            return True
        
        return False
    
    def get_preferences_by_tenant(
        self,
        tenant_id: UUID
    ) -> List[UserPreferences]:
        """
        Get all preferences for a tenant.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            List of UserPreferences for the tenant
        """
        return [
            prefs for prefs in self._preferences.values()
            if prefs.tenant_id == tenant_id
        ]
    
    def _get_or_create_preferences(
        self,
        user_id: UUID,
        tenant_id: UUID
    ) -> UserPreferences:
        """
        Get existing preferences or create new ones.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            
        Returns:
            UserPreferences object
        """
        if user_id not in self._preferences:
            self._preferences[user_id] = UserPreferences(
                user_id=user_id,
                tenant_id=tenant_id
            )
            logger.info(f"Created new preferences for user_id={user_id}")
        
        return self._preferences[user_id]
    
    def clear_tenant_preferences(self, tenant_id: UUID) -> int:
        """
        Clear all preferences for a tenant.
        
        Used for tenant cleanup or testing.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Number of preferences cleared
        """
        user_ids_to_remove = [
            uid for uid, prefs in self._preferences.items()
            if prefs.tenant_id == tenant_id
        ]
        
        for uid in user_ids_to_remove:
            del self._preferences[uid]
        
        cleared = len(user_ids_to_remove)
        logger.info(f"Cleared {cleared} preferences for tenant {tenant_id}")
        return cleared
