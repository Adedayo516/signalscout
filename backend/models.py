from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.sql import func
from database import Base

class TrendingContent(Base):
    __tablename__ = "trending_content"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)
    content_id = Column(String(255), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    url = Column(String(512))
    author = Column(String(255))
    score = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    virality_score = Column(Float, default=0.0)
    tags = Column(JSON)
    sentiment = Column(String(50))
    topic_cluster = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

class GeneratedContent(Base):
    __tablename__ = "generated_content"
    
    id = Column(Integer, primary_key=True, index=True)
    trend_id = Column(Integer, index=True)
    content_type = Column(String(50), nullable=False)  # tweet, linkedin, script, carousel
    generated_text = Column(Text, nullable=False)
    brand_voice = Column(String(255))
    target_audience = Column(String(255))
    quality_score = Column(Float, default=0.0)
    topic_cluster = Column(String(100))
    is_used = Column(Boolean, default=False)
    performance_prediction = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BrandVoice(Base):
    __tablename__ = "brand_voices"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_name = Column(String(255), nullable=False)
    tone = Column(String(100))
    characteristics = Column(JSON)
    sample_content = Column(JSON)
    voice_embedding = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ViralityPattern(Base):
    __tablename__ = "virality_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_type = Column(String(100), nullable=False)  # hook, timing, emotion, format
    pattern_data = Column(JSON)
    success_rate = Column(Float, default=0.0)
    platforms = Column(JSON)
    topic_clusters = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())