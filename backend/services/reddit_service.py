import praw
import os
from typing import List, Dict
from models import TrendingContent
from database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedditService:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "ContentIntelligenceDashboard/1.0")
        )
    
    async def fetch_trending_posts(self, subreddit_name: str, limit: int = 25) -> List[Dict]:
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            # Fetch hot posts
            for submission in subreddit.hot(limit=limit):
                if not submission.stickied:  # Skip pinned posts
                    post_data = {
                        "platform": "reddit",
                        "content_id": submission.id,
                        "title": submission.title,
                        "description": submission.selftext[:500] if submission.selftext else "",
                        "url": f"https://reddit.com{submission.permalink}",
                        "author": str(submission.author) if submission.author else "unknown",
                        "score": submission.score,
                        "comments_count": submission.num_comments,
                        "engagement_rate": self._calculate_engagement_rate(submission),
                        "virality_score": self._calculate_virality_score(submission),
                        "tags": self._extract_tags(submission),
                        "sentiment": self._analyze_sentiment(submission.title),
                        "topic_cluster": self._categorize_topic(submission.title, submission.selftext)
                    }
                    posts.append(post_data)
            
            # Store in database
            self._store_trending_content(posts)
            logger.info(f"Fetched {len(posts)} trending posts from r/{subreddit_name}")
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching Reddit trends: {str(e)}")
            raise e
    
    def _calculate_engagement_rate(self, submission) -> float:
        if submission.score <= 0:
            return 0.0
        return (submission.num_comments / submission.score) * 100
    
    def _calculate_virality_score(self, submission) -> float:
        # Simple virality score based on engagement metrics
        age_hours = (submission.created_utc) / 3600
        if age_hours == 0:
            age_hours = 1
        
        score_per_hour = submission.score / age_hours
        comment_ratio = submission.num_comments / max(submission.score, 1)
        
        virality_score = (score_per_hour * 0.7) + (comment_ratio * 100 * 0.3)
        return min(virality_score, 100.0)  # Cap at 100
    
    def _extract_tags(self, submission) -> List[str]:
        tags = []
        
        # Extract from title and text
        text = f"{submission.title} {submission.selftext}".lower()
        
        # Common trending patterns
        if any(word in text for word in ["trending", "viral", "popular"]):
            tags.append("trending")
        if any(word in text for word in ["tips", "hack", "secret"]):
            tags.append("educational")
        if any(word in text for word in ["funny", "lol", "humor"]):
            tags.append("humor")
        if any(word in text for word in ["breaking", "news", "update"]):
            tags.append("news")
        
        return tags
    
    def _analyze_sentiment(self, text: str) -> str:
        # Simple sentiment analysis (you can integrate with more sophisticated tools)
        positive_words = ["great", "awesome", "amazing", "love", "best", "incredible"]
        negative_words = ["bad", "terrible", "awful", "hate", "worst", "horrible"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _categorize_topic(self, title: str, text: str) -> str:
        content = f"{title} {text}".lower()
        
        categories = {
            "technology": ["tech", "ai", "software", "coding", "programming"],
            "business": ["business", "startup", "marketing", "sales", "entrepreneur"],
            "lifestyle": ["life", "health", "fitness", "food", "travel"],
            "entertainment": ["movie", "music", "game", "tv", "celebrity"],
            "education": ["learn", "study", "course", "tutorial", "guide"],
            "finance": ["money", "investing", "crypto", "stock", "finance"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in content for keyword in keywords):
                return category
        
        return "general"
    
    def _store_trending_content(self, posts: List[Dict]):
        db = SessionLocal()
        try:
            for post_data in posts:
                # Check if already exists
                existing = db.query(TrendingContent).filter(
                    TrendingContent.content_id == post_data["content_id"],
                    TrendingContent.platform == "reddit"
                ).first()
                
                if not existing:
                    trending_content = TrendingContent(**post_data)
                    db.add(trending_content)
            
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing trending content: {str(e)}")
        finally:
            db.close()