"""SKU normalization component"""
from typing import Dict, Optional
import re


class SKUNormalizer:
    """
    Normalizes SKU identifiers across different marketplace formats.
    
    Responsibilities:
    - Normalize SKU formats from different marketplaces
    - Create product equivalence mappings
    - Calculate mapping confidence
    """
    
    # Marketplace-specific SKU patterns
    MARKETPLACE_PATTERNS = {
        'amazon': r'^[A-Z0-9]{10}$',  # ASIN format
        'ebay': r'^\d{12}$',  # 12-digit item number
        'walmart': r'^\d{8,9}$',  # 8-9 digit item ID
        'shopify': r'^\d+$',  # Numeric ID
    }
    
    def normalize_sku(self, sku: str, marketplace: Optional[str] = None) -> str:
        """
        Normalize a SKU to a consistent format.
        
        Normalization rules:
        1. Convert to uppercase
        2. Remove whitespace
        3. Remove special characters (except hyphens and underscores)
        4. Apply marketplace-specific rules
        
        Args:
            sku: Original SKU
            marketplace: Marketplace name (optional)
            
        Returns:
            Normalized SKU
        """
        if not sku:
            return ""
        
        # Basic normalization
        normalized = sku.strip().upper()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', '', normalized)
        
        # Remove special characters except hyphens and underscores
        normalized = re.sub(r'[^A-Z0-9\-_]', '', normalized)
        
        # Apply marketplace-specific normalization
        if marketplace:
            marketplace_lower = marketplace.lower()
            
            if marketplace_lower == 'amazon':
                # Amazon ASINs are 10 characters
                if len(normalized) == 10 and normalized.isalnum():
                    return normalized
            
            elif marketplace_lower == 'ebay':
                # eBay item numbers are numeric
                if normalized.isdigit():
                    return normalized
            
            elif marketplace_lower == 'walmart':
                # Walmart item IDs are 8-9 digits
                if normalized.isdigit() and 8 <= len(normalized) <= 9:
                    return normalized
            
            elif marketplace_lower == 'shopify':
                # Shopify uses numeric IDs
                if normalized.isdigit():
                    return normalized
        
        return normalized
    
    def calculate_sku_similarity(self, sku1: str, sku2: str) -> float:
        """
        Calculate similarity between two SKUs.
        
        Uses Levenshtein distance normalized to 0-1 range.
        
        Args:
            sku1: First SKU
            sku2: Second SKU
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not sku1 or not sku2:
            return 0.0
        
        if sku1 == sku2:
            return 1.0
        
        # Levenshtein distance
        distance = self._levenshtein_distance(sku1, sku2)
        max_len = max(len(sku1), len(sku2))
        
        if max_len == 0:
            return 0.0
        
        similarity = 1.0 - (distance / max_len)
        return max(0.0, min(1.0, similarity))
    
    def create_product_mapping(
        self,
        sku1: str,
        marketplace1: str,
        sku2: str,
        marketplace2: str
    ) -> Dict[str, any]:
        """
        Create a product equivalence mapping between two SKUs.
        
        Args:
            sku1: First product SKU
            marketplace1: First marketplace
            sku2: Second product SKU
            marketplace2: Second marketplace
            
        Returns:
            Mapping dictionary with confidence score
        """
        norm_sku1 = self.normalize_sku(sku1, marketplace1)
        norm_sku2 = self.normalize_sku(sku2, marketplace2)
        
        # Calculate confidence based on similarity
        similarity = self.calculate_sku_similarity(norm_sku1, norm_sku2)
        
        # Exact match = high confidence
        if norm_sku1 == norm_sku2:
            confidence = 1.0
            mapping_type = "exact"
        # High similarity = medium confidence
        elif similarity >= 0.8:
            confidence = similarity * 0.9  # Slightly reduce confidence
            mapping_type = "similarity"
        # Low similarity = low confidence
        else:
            confidence = similarity * 0.5
            mapping_type = "weak"
        
        return {
            'sku1': sku1,
            'normalized_sku1': norm_sku1,
            'marketplace1': marketplace1,
            'sku2': sku2,
            'normalized_sku2': norm_sku2,
            'marketplace2': marketplace2,
            'confidence': confidence,
            'mapping_type': mapping_type,
            'similarity_score': similarity
        }
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance between two strings.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Edit distance
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
