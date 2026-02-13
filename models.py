from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class URL(Base):
    """URL model for storing long URLs and their short slugs"""
    __tablename__ = "urls"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    long_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    
    # Relationship with clicks (use selectinload in queries for better performance)
    clicks = relationship("Click", back_populates="url", cascade="all, delete-orphan")
    
    @property
    def click_count(self):
        """Get total number of clicks"""
        return len(self.clicks)

class Click(Base):
    """Click model for tracking analytics"""
    __tablename__ = "clicks"
    
    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Request metadata
    referrer = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    
    # Geographic data (would require GeoIP library)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    
    # Device information (parsed from user agent)
    device_type = Column(String, nullable=True)  # mobile, desktop, tablet
    browser = Column(String, nullable=True)
    os = Column(String, nullable=True)
    
    # Relationship with URL
    url = relationship("URL", back_populates="clicks")
