"""Data validation component"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ValidationError, Field
from datetime import datetime
from decimal import Decimal
import re


class ValidationResult(BaseModel):
    """Result of data validation"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validated_data: Optional[Dict[str, Any]] = None


class DataValidator:
    """
    Validates incoming data against schemas and business rules.
    
    Responsibilities:
    - Schema validation using Pydantic
    - Data type validation
    - Business rule validation
    - Spam review filtering
    """
    
    # Spam detection patterns
    SPAM_PATTERNS = [
        r'(buy|click|visit)\s+(here|now|link)',
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        r'(viagra|cialis|pharmacy|casino|lottery)',
        r'(\w)\1{5,}',  # Repeated characters
        r'FREE\s+MONEY|CLICK\s+HERE|LIMITED\s+TIME',
    ]
    
    SPAM_KEYWORDS = [
        'viagra', 'cialis', 'pharmacy', 'casino', 'lottery',
        'free money', 'click here', 'buy now', 'limited time',
        'act now', 'special offer', 'winner', 'congratulations'
    ]
    
    def validate_product_data(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate product data.
        
        Args:
            data: Raw product data dictionary
            
        Returns:
            ValidationResult with validation status and errors
        """
        errors = []
        warnings = []
        
        # Required fields
        required_fields = ['sku', 'name', 'price', 'marketplace']
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return ValidationResult(is_valid=False, errors=errors)
        
        # Data type validation
        try:
            # Price validation
            price = data.get('price')
            if price is not None:
                # Check for infinity or NaN first
                if isinstance(price, float):
                    import math
                    if math.isinf(price) or math.isnan(price):
                        errors.append(f"Price cannot be infinity or NaN: {price}")
                        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
                
                if isinstance(price, str):
                    price = Decimal(price)
                elif isinstance(price, (int, float)):
                    price = Decimal(str(price))
                
                if price <= 0:
                    errors.append(f"Price must be positive, got: {price}")
                elif price > 1000000:
                    warnings.append(f"Unusually high price: {price}")
                
                data['price'] = price
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid price format: {e}")
        
        # SKU validation
        sku = data.get('sku', '')
        if len(sku) < 3:
            errors.append(f"SKU too short (min 3 chars): {sku}")
        elif len(sku) > 255:
            errors.append(f"SKU too long (max 255 chars): {sku}")
        
        # Name validation
        name = data.get('name', '')
        if len(name) < 2:
            errors.append(f"Product name too short: {name}")
        elif len(name) > 500:
            warnings.append(f"Product name very long: {len(name)} chars")
        
        # Currency validation
        currency = data.get('currency', 'USD')
        if len(currency) != 3 or not currency.isupper():
            errors.append(f"Invalid currency code: {currency}")
        
        # Inventory validation
        inventory = data.get('inventory_level')
        if inventory is not None:
            try:
                inventory = int(inventory)
                if inventory < 0:
                    errors.append(f"Inventory cannot be negative: {inventory}")
                data['inventory_level'] = inventory
            except (ValueError, TypeError):
                errors.append(f"Invalid inventory level: {inventory}")
        
        # Marketplace validation
        marketplace = data.get('marketplace', '')
        if not marketplace or len(marketplace) < 2:
            errors.append(f"Invalid marketplace: {marketplace}")
        
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            validated_data=data if is_valid else None
        )
    
    def validate_review_data(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate review data.
        
        Args:
            data: Raw review data dictionary
            
        Returns:
            ValidationResult with validation status and errors
        """
        errors = []
        warnings = []
        
        # Required fields
        required_fields = ['product_id', 'rating', 'text']
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return ValidationResult(is_valid=False, errors=errors)
        
        # Rating validation
        rating = data.get('rating')
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                errors.append(f"Rating must be 1-5, got: {rating}")
            data['rating'] = rating
        except (ValueError, TypeError):
            errors.append(f"Invalid rating format: {rating}")
        
        # Text validation
        text = data.get('text', '')
        if len(text) < 5:
            errors.append(f"Review text too short (min 5 chars): {len(text)}")
        elif len(text) > 5000:
            warnings.append(f"Review text very long: {len(text)} chars")
        
        # Check for spam
        is_spam, spam_reasons = self.is_spam_review(text)
        if is_spam:
            data['is_spam'] = True
            warnings.extend(spam_reasons)
        else:
            data['is_spam'] = False
        
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            validated_data=data if is_valid else None
        )
    
    def is_spam_review(self, text: str) -> tuple[bool, List[str]]:
        """
        Detect if a review is spam.
        
        Args:
            text: Review text
            
        Returns:
            Tuple of (is_spam, reasons)
        """
        reasons = []
        text_lower = text.lower()
        
        # Check patterns
        for pattern in self.SPAM_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                reasons.append(f"Spam pattern detected: {pattern}")
        
        # Check keywords
        for keyword in self.SPAM_KEYWORDS:
            if keyword in text_lower:
                reasons.append(f"Spam keyword detected: {keyword}")
        
        # Check for excessive caps
        if len(text) > 10:
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.5:
                reasons.append(f"Excessive caps: {caps_ratio:.1%}")
        
        # Check for repeated characters
        if re.search(r'(.)\1{4,}', text):
            reasons.append("Repeated characters detected")
        
        # Check for very short reviews (likely spam)
        if len(text) < 10:
            reasons.append("Review too short")
        
        return len(reasons) > 0, reasons
    
    def filter_spam_reviews(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out spam reviews from a list.
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            List of non-spam reviews
        """
        filtered = []
        for review in reviews:
            text = review.get('text', '')
            is_spam, _ = self.is_spam_review(text)
            if not is_spam:
                filtered.append(review)
            else:
                review['is_spam'] = True
        
        return filtered
