"""Review model"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from src.database import Base
from src.models.product import GUID


class Review(Base):
    """Review model for storing customer reviews"""
    __tablename__ = "reviews"
    
    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)
    
    # Foreign key to tenant (MULTI-TENANCY)
    tenant_id = Column(GUID(), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Foreign key to product
    product_id = Column(GUID(), ForeignKey('products.id'), nullable=False)
    
    # Review content
    rating = Column(Integer, nullable=False)  # 1-5
    text = Column(String, nullable=False)
    review_text = Column(String, nullable=True)  # Alias for compatibility
    
    # Sentiment analysis results
    sentiment = Column(String(20), nullable=True)  # positive, negative, neutral
    sentiment_label = Column(String(20), nullable=True)  # Alias for compatibility
    sentiment_confidence = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)  # Alias for compatibility
    
    # Spam detection
    is_spam = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Source
    source = Column(String(100), nullable=False, default="unknown")
    
    # Relationships
    tenant = relationship("Tenant", back_populates="reviews")
    product = relationship("Product", backref="reviews")
    
    # Indexes
    __table_args__ = (
        Index('idx_reviews_tenant', 'tenant_id'),
        Index('idx_reviews_product', 'product_id'),
        Index('idx_reviews_sentiment', 'sentiment'),
    )
    
    def __repr__(self):
        return f"<Review(id={self.id}, product_id={self.product_id}, rating={self.rating})>"
