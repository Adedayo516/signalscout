from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from database import engine, SessionLocal
from models import Base
from services.reddit_service import RedditService
from services.youtube_service import YouTubeService
from services.content_generator import ContentGenerator
from services.trend_analyzer import TrendAnalyzer

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SignalScout - AI Content Intelligence", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://*.netlify.app",
        "*"  # For production - replace with your domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

reddit_service = RedditService()
youtube_service = YouTubeService()
content_generator = ContentGenerator()
trend_analyzer = TrendAnalyzer()

class TrendRequest(BaseModel):
    subreddit: str
    limit: int = 25

class ContentGenerationRequest(BaseModel):
    trend_id: int
    content_type: str  # "tweet", "linkedin", "script", "carousel"
    brand_voice: str
    target_audience: str

class BrandVoiceRequest(BaseModel):
    sample_content: List[str]
    brand_name: str
    tone: str

@app.get("/")
async def root():
    return {"message": "SignalScout API - AI Content Intelligence Platform", "status": "running"}

@app.post("/trends/reddit")
async def fetch_reddit_trends(request: TrendRequest, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(reddit_service.fetch_trending_posts, request.subreddit, request.limit)
        return {"message": f"Started fetching trends from r/{request.subreddit}", "status": "processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trends/youtube")
async def fetch_youtube_trends(background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(youtube_service.fetch_trending_videos)
        return {"message": "Started fetching YouTube trending videos", "status": "processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trends")
async def get_trends(limit: int = 50, platform: Optional[str] = None):
    try:
        db = SessionLocal()
        trends = trend_analyzer.get_trending_content(db, limit, platform)
        db.close()
        return {"trends": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/content/generate")
async def generate_content(request: ContentGenerationRequest):
    try:
        db = SessionLocal()
        content = await content_generator.generate_content(
            db, request.trend_id, request.content_type, 
            request.brand_voice, request.target_audience
        )
        db.close()
        return {"generated_content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/brand-voice/train")
async def train_brand_voice(request: BrandVoiceRequest):
    try:
        voice_profile = await content_generator.train_brand_voice(
            request.sample_content, request.brand_name, request.tone
        )
        return {"voice_profile": voice_profile, "status": "trained"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/virality")
async def get_virality_analytics(days: int = 7):
    try:
        db = SessionLocal()
        analytics = trend_analyzer.get_virality_analytics(db, days)
        db.close()
        return {"analytics": analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/content/vault")
async def get_content_vault(limit: int = 50, topic: Optional[str] = None):
    try:
        db = SessionLocal()
        content = content_generator.get_generated_content(db, limit, topic)
        db.close()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", os.getenv("API_PORT", 8000)))
    uvicorn.run(app, host=os.getenv("API_HOST", "0.0.0.0"), port=port)