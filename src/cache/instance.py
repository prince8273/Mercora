"""Global cache manager instance"""
from typing import Optional
from src.cache.cache_manager import CacheManager

# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def set_cache_manager(manager: Optional[CacheManager]):
    """Set the global cache manager instance"""
    global _cache_manager
    _cache_manager = manager


def get_cache_manager() -> Optional[CacheManager]:
    """Get the global cache manager instance"""
    return _cache_manager
