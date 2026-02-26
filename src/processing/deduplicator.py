"""Data deduplication component"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict


class Deduplicator:
    """
    Detects and removes duplicate records.
    
    Responsibilities:
    - Detect duplicate products and reviews
    - Apply resolution strategy (most recent wins)
    - Preserve data lineage
    """
    
    def deduplicate_products(
        self,
        products: List[Dict[str, Any]],
        key_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate products, keeping the most recent version.
        
        Args:
            products: List of product dictionaries
            key_fields: Fields to use for duplicate detection (default: sku + marketplace)
            
        Returns:
            Deduplicated list of products
        """
        if not products:
            return []
        
        if key_fields is None:
            key_fields = ['sku', 'marketplace']
        
        # Group by key
        groups = defaultdict(list)
        for product in products:
            key = self._make_key(product, key_fields)
            groups[key].append(product)
        
        # Keep most recent from each group
        deduplicated = []
        for key, group in groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Sort by updated_at or created_at, keep most recent
                most_recent = self._get_most_recent(group)
                deduplicated.append(most_recent)
        
        return deduplicated
    
    def deduplicate_reviews(
        self,
        reviews: List[Dict[str, Any]],
        key_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate reviews, keeping the most recent version.
        
        Args:
            reviews: List of review dictionaries
            key_fields: Fields to use for duplicate detection (default: product_id + text)
            
        Returns:
            Deduplicated list of reviews
        """
        if not reviews:
            return []
        
        if key_fields is None:
            key_fields = ['product_id', 'text']
        
        # Group by key
        groups = defaultdict(list)
        for review in reviews:
            key = self._make_key(review, key_fields)
            groups[key].append(review)
        
        # Keep most recent from each group
        deduplicated = []
        for key, group in groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                most_recent = self._get_most_recent(group)
                deduplicated.append(most_recent)
        
        return deduplicated
    
    def find_duplicates(
        self,
        records: List[Dict[str, Any]],
        key_fields: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find all duplicate groups without removing them.
        
        Args:
            records: List of record dictionaries
            key_fields: Fields to use for duplicate detection
            
        Returns:
            Dictionary mapping keys to lists of duplicate records
        """
        groups = defaultdict(list)
        for record in records:
            key = self._make_key(record, key_fields)
            groups[key].append(record)
        
        # Return only groups with duplicates
        return {k: v for k, v in groups.items() if len(v) > 1}
    
    def _make_key(self, record: Dict[str, Any], key_fields: List[str]) -> str:
        """
        Create a composite key from specified fields.
        
        Args:
            record: Record dictionary
            key_fields: Fields to include in key
            
        Returns:
            Composite key string
        """
        key_parts = []
        for field in key_fields:
            value = record.get(field)
            if value is not None:
                # Normalize text fields
                if isinstance(value, str):
                    value = value.strip().lower()
                key_parts.append(str(value))
            else:
                key_parts.append("__NULL__")
        
        return "||".join(key_parts)
    
    def _get_most_recent(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get the most recent record from a list.
        
        Looks for 'updated_at' first, then 'created_at', then returns first record.
        
        Args:
            records: List of record dictionaries
            
        Returns:
            Most recent record
        """
        if not records:
            return {}
        
        if len(records) == 1:
            return records[0]
        
        # Try to sort by updated_at
        records_with_updated = [r for r in records if 'updated_at' in r and r['updated_at']]
        if records_with_updated:
            return max(records_with_updated, key=lambda r: self._parse_datetime(r['updated_at']))
        
        # Try to sort by created_at
        records_with_created = [r for r in records if 'created_at' in r and r['created_at']]
        if records_with_created:
            return max(records_with_created, key=lambda r: self._parse_datetime(r['created_at']))
        
        # Default to first record
        return records[0]
    
    def _parse_datetime(self, dt: Any) -> datetime:
        """
        Parse datetime from various formats.
        
        Args:
            dt: Datetime value (datetime object, string, or timestamp)
            
        Returns:
            datetime object
        """
        if isinstance(dt, datetime):
            return dt
        
        if isinstance(dt, str):
            try:
                return datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except ValueError:
                return datetime.min
        
        if isinstance(dt, (int, float)):
            try:
                return datetime.fromtimestamp(dt)
            except (ValueError, OSError):
                return datetime.min
        
        return datetime.min
