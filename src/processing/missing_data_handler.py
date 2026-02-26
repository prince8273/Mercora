"""Missing data handler component"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal


class MissingDataHandler:
    """
    Handles missing data in records.
    
    Responsibilities:
    - Detect missing critical fields
    - Apply default values where appropriate
    - Implement interpolation strategies
    - Flag records with missing data
    """
    
    # Default values for different field types
    DEFAULT_VALUES = {
        'currency': 'USD',
        'inventory_level': None,  # Don't assume inventory
        'category': 'Uncategorized',
        'is_spam': False,
    }
    
    # Critical fields that cannot have defaults
    CRITICAL_PRODUCT_FIELDS = ['sku', 'name', 'price', 'marketplace']
    CRITICAL_REVIEW_FIELDS = ['product_id', 'rating', 'text']
    
    def handle_missing_product_data(
        self,
        product: Dict[str, Any],
        apply_defaults: bool = True
    ) -> Dict[str, Any]:
        """
        Handle missing data in product record.
        
        Args:
            product: Product dictionary
            apply_defaults: Whether to apply default values
            
        Returns:
            Product with missing data handled and flags added
        """
        result = product.copy()
        missing_fields = []
        critical_missing = []
        
        # Check for missing fields
        for field in self.CRITICAL_PRODUCT_FIELDS:
            if field not in result or result[field] is None or result[field] == '':
                critical_missing.append(field)
        
        # Check optional fields
        optional_fields = ['category', 'inventory_level', 'currency']
        for field in optional_fields:
            if field not in result or result[field] is None:
                missing_fields.append(field)
                
                # Apply defaults if requested
                if apply_defaults and field in self.DEFAULT_VALUES:
                    result[field] = self.DEFAULT_VALUES[field]
        
        # Add metadata about missing data
        result['_missing_fields'] = missing_fields
        result['_critical_missing'] = critical_missing
        result['_has_missing_data'] = len(missing_fields) > 0 or len(critical_missing) > 0
        
        return result
    
    def handle_missing_review_data(
        self,
        review: Dict[str, Any],
        apply_defaults: bool = True
    ) -> Dict[str, Any]:
        """
        Handle missing data in review record.
        
        Args:
            review: Review dictionary
            apply_defaults: Whether to apply default values
            
        Returns:
            Review with missing data handled and flags added
        """
        result = review.copy()
        missing_fields = []
        critical_missing = []
        
        # Check for missing critical fields
        for field in self.CRITICAL_REVIEW_FIELDS:
            if field not in result or result[field] is None or result[field] == '':
                critical_missing.append(field)
        
        # Check optional fields
        optional_fields = ['sentiment', 'is_spam', 'verified_purchase']
        for field in optional_fields:
            if field not in result or result[field] is None:
                missing_fields.append(field)
                
                # Apply defaults if requested
                if apply_defaults and field in self.DEFAULT_VALUES:
                    result[field] = self.DEFAULT_VALUES[field]
        
        # Add metadata
        result['_missing_fields'] = missing_fields
        result['_critical_missing'] = critical_missing
        result['_has_missing_data'] = len(missing_fields) > 0 or len(critical_missing) > 0
        
        return result
    
    def interpolate_missing_prices(
        self,
        products: List[Dict[str, Any]],
        group_by: str = 'category'
    ) -> List[Dict[str, Any]]:
        """
        Interpolate missing prices based on similar products.
        
        Args:
            products: List of product dictionaries
            group_by: Field to group by for interpolation
            
        Returns:
            Products with interpolated prices
        """
        from statistics import mean
        
        # Group products by category
        groups = {}
        for product in products:
            group_key = product.get(group_by, 'unknown')
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(product)
        
        # Calculate average prices per group
        group_averages = {}
        for group_key, group_products in groups.items():
            prices = [
                float(p['price']) for p in group_products
                if 'price' in p and p['price'] is not None
            ]
            if prices:
                group_averages[group_key] = Decimal(str(mean(prices)))
        
        # Interpolate missing prices
        result = []
        for product in products:
            if 'price' not in product or product['price'] is None:
                group_key = product.get(group_by, 'unknown')
                if group_key in group_averages:
                    product['price'] = group_averages[group_key]
                    product['_price_interpolated'] = True
                else:
                    product['_price_interpolated'] = False
            result.append(product)
        
        return result
    
    def flag_incomplete_records(
        self,
        records: List[Dict[str, Any]],
        required_fields: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Flag records with missing required fields.
        
        Args:
            records: List of record dictionaries
            required_fields: List of required field names
            
        Returns:
            Records with completeness flags
        """
        result = []
        for record in records:
            missing = []
            for field in required_fields:
                if field not in record or record[field] is None or record[field] == '':
                    missing.append(field)
            
            record['_incomplete'] = len(missing) > 0
            record['_missing_required_fields'] = missing
            result.append(record)
        
        return result
    
    def get_completeness_score(self, record: Dict[str, Any], all_fields: List[str]) -> float:
        """
        Calculate completeness score for a record.
        
        Args:
            record: Record dictionary
            all_fields: List of all possible fields
            
        Returns:
            Completeness score (0.0 to 1.0)
        """
        if not all_fields:
            return 1.0
        
        present_count = 0
        for field in all_fields:
            if field in record and record[field] is not None and record[field] != '':
                present_count += 1
        
        return present_count / len(all_fields)
