from googleapiclient.discovery import build
import os
from typing import List, Dict
from models import TrendingContent
from database import SessionLocal
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self):
        self.youtube = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))
    
    async def fetch_trending_videos(self, region_code: str = "US", limit: int = 50) -> List[Dict]:
        try:
            # Fetch trending videos
            request = self.youtube.videos().list(
                part="snippet,statistics",
                chart="mostPopular",
                regionCode=region_code,
                maxResults=limit
            )
            response = request.execute()
            
            videos = []
            for item in response.get('items', []):
                video_data = {
                    "platform": "youtube",
                    "content_id": item['id'],
                    "title": item['snippet']['title'],
                    "description": item['snippet']['description'][:500],
                    "url": f"https://www.youtube.com/watch?v={item['id']}",
                    "author": item['snippet']['channelTitle'],
                    "score": int(item['statistics'].get('viewCount', 0)),
                    "comments_count": int(item['statistics'].get('commentCount', 0)),
                    "engagement_rate": self._calculate_engagement_rate(item['statistics']),
                    "virality_score": self._calculate_virality_score(item),
                    "tags": item['snippet'].get('tags', [])[:10],  # Limit tags
                    "sentiment": self._analyze_sentiment(item['snippet']['title']),
                    "topic_cluster": self._categorize_topic(item['snippet'])
                }
                videos.append(video_data)
            
            # Store in database
            self._store_trending_content(videos)
            logger.info(f"Fetched {len(videos)} trending YouTube videos")
            return videos
            
        except Exception as e:
            logger.error(f"Error fetching YouTube trends: {str(e)}")
            raise e
    
    async def search_trending_by_keyword(self, keyword: str, days_back: int = 7, limit: int = 25) -> List[Dict]:
        try:
            # Calculate date range
            published_after = (datetime.now() - timedelta(days=days_back)).isoformat() + "Z"
            
            # Search for videos
            search_request = self.youtube.search().list(
                part="snippet",
                q=keyword,
                type="video",
                order="relevance",
                publishedAfter=published_after,
                maxResults=limit
            )
            search_response = search_request.execute()
            
            # Get video statistics
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            
            if not video_ids:
                return []
            
            stats_request = self.youtube.videos().list(
                part="statistics,snippet",
                id=','.join(video_ids)
            )
            stats_response = stats_request.execute()
            
            videos = []
            for item in stats_response.get('items', []):
                video_data = {
                    "platform": "youtube",
                    "content_id": item['id'],
                    "title": item['snippet']['title'],
                    "description": item['snippet']['description'][:500],
                    "url": f"https://www.youtube.com/watch?v={item['id']}",
                    "author": item['snippet']['channelTitle'],
                    "score": int(item['statistics'].get('viewCount', 0)),
                    "comments_count": int(item['statistics'].get('commentCount', 0)),
                    "engagement_rate": self._calculate_engagement_rate(item['statistics']),
                    "virality_score": self._calculate_virality_score(item),
                    "tags": item['snippet'].get('tags', [])[:10],
                    "sentiment": self._analyze_sentiment(item['snippet']['title']),
                    "topic_cluster": self._categorize_topic(item['snippet'])
                }
                videos.append(video_data)
            
            self._store_trending_content(videos)
            logger.info(f"Fetched {len(videos)} videos for keyword: {keyword}")
            return videos
            
        except Exception as e:
            logger.error(f"Error searching YouTube by keyword: {str(e)}")
            raise e
    
    def _calculate_engagement_rate(self, statistics: Dict) -> float:
        views = int(statistics.get('viewCount', 0))
        likes = int(statistics.get('likeCount', 0))
        comments = int(statistics.get('commentCount', 0))
        
        if views == 0:
            return 0.0
        
        engagement = likes + (comments * 2)  # Weight comments more
        return (engagement / views) * 100
    
    def _calculate_virality_score(self, video_item: Dict) -> float:
        stats = video_item['statistics']
        snippet = video_item['snippet']
        
        views = int(stats.get('viewCount', 0))
        likes = int(stats.get('likeCount', 0))
        comments = int(stats.get('commentCount', 0))
        
        # Calculate days since published
        published_date = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
        days_old = (datetime.now(published_date.tzinfo) - published_date).days
        days_old = max(days_old, 1)  # Avoid division by zero
        
        # Views per day
        views_per_day = views / days_old
        
        # Engagement factor
        engagement_factor = (likes + (comments * 3)) / max(views, 1)
        
        # Virality score (normalize to 0-100)
        virality_score = min((views_per_day / 1000) + (engagement_factor * 50), 100)
        
        return virality_score
    
    def _analyze_sentiment(self, text: str) -> str:
        positive_words = ["amazing", "incredible", "best", "awesome", "love", "great", "fantastic"]
        negative_words = ["worst", "terrible", "bad", "awful", "hate", "horrible", "disaster"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _categorize_topic(self, snippet: Dict) -> str:
        title = snippet.get('title', '').lower()
        description = snippet.get('description', '').lower()
        tags = [tag.lower() for tag in snippet.get('tags', [])]
        
        content = f"{title} {description} {' '.join(tags)}"
        
        categories = {
            "technology": ["tech", "ai", "software", "coding", "programming", "gadget"],
            "business": ["business", "startup", "marketing", "entrepreneur", "money"],
            "lifestyle": ["lifestyle", "health", "fitness", "beauty", "fashion", "food"],
            "entertainment": ["entertainment", "movie", "music", "comedy", "funny", "celebrity"],
            "education": ["tutorial", "how to", "learn", "education", "course", "guide"],
            "gaming": ["gaming", "game", "gameplay", "review", "playthrough"],
            "travel": ["travel", "vacation", "trip", "destination", "explore"],
            "sports": ["sports", "football", "basketball", "soccer", "workout", "training"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in content for keyword in keywords):
                return category
        
        return "general"
    
    def _store_trending_content(self, videos: List[Dict]):
        db = SessionLocal()
        try:
            for video_data in videos:
                # Check if already exists
                existing = db.query(TrendingContent).filter(
                    TrendingContent.content_id == video_data["content_id"],
                    TrendingContent.platform == "youtube"
                ).first()
                
                if not existing:
                    trending_content = TrendingContent(**video_data)
                    db.add(trending_content)
            
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing trending content: {str(e)}")
        finally:
            db.close()