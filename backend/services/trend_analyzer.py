from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from models import TrendingContent, ViralityPattern
from typing import List, Dict, Optional
import logging
from collections import Counter
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrendAnalyzer:
    def __init__(self):
        self.viral_threshold = 70.0  # Virality score threshold
    
    def get_trending_content(self, db: Session, limit: int = 50, platform: Optional[str] = None) -> List[Dict]:
        query = db.query(TrendingContent).order_by(desc(TrendingContent.virality_score))
        
        if platform:
            query = query.filter(TrendingContent.platform == platform)
        
        trending = query.limit(limit).all()
        
        return [self._content_to_dict(content) for content in trending]
    
    def analyze_viral_patterns(self, db: Session, min_virality_score: float = 70.0) -> Dict:
        viral_content = db.query(TrendingContent).filter(
            TrendingContent.virality_score >= min_virality_score
        ).all()
        
        if not viral_content:
            return {"message": "No viral content found", "patterns": []}
        
        patterns = {
            "hook_patterns": self._analyze_hooks([c.title for c in viral_content]),
            "timing_patterns": self._analyze_timing(viral_content),
            "emotion_patterns": self._analyze_emotions(viral_content),
            "format_patterns": self._analyze_formats(viral_content),
            "topic_trends": self._analyze_topic_trends(viral_content),
            "platform_insights": self._analyze_platform_performance(viral_content)
        }
        
        # Store patterns in database
        self._store_patterns(db, patterns)
        
        return {
            "total_viral_content": len(viral_content),
            "analysis_threshold": min_virality_score,
            "patterns": patterns
        }
    
    def get_virality_analytics(self, db: Session, days: int = 7) -> Dict:
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_content = db.query(TrendingContent).filter(
            TrendingContent.created_at >= cutoff_date
        ).all()
        
        if not recent_content:
            return {"message": "No recent content found"}
        
        analytics = {
            "total_content": len(recent_content),
            "avg_virality_score": sum(c.virality_score for c in recent_content) / len(recent_content),
            "viral_content_count": len([c for c in recent_content if c.virality_score >= self.viral_threshold]),
            "platform_breakdown": self._get_platform_breakdown(recent_content),
            "top_topics": self._get_top_topics(recent_content),
            "engagement_trends": self._get_engagement_trends(recent_content),
            "sentiment_distribution": self._get_sentiment_distribution(recent_content)
        }
        
        return analytics
    
    def get_content_recommendations(self, db: Session, topic: str, content_type: str) -> List[Dict]:
        # Find high-performing content in the specified topic
        similar_content = db.query(TrendingContent).filter(
            TrendingContent.topic_cluster == topic,
            TrendingContent.virality_score >= 60.0
        ).order_by(desc(TrendingContent.virality_score)).limit(10).all()
        
        recommendations = []
        for content in similar_content:
            rec = self._content_to_dict(content)
            rec["recommendation_reason"] = self._get_recommendation_reason(content, content_type)
            recommendations.append(rec)
        
        return recommendations
    
    def _analyze_hooks(self, titles: List[str]) -> Dict:
        hook_patterns = {
            "question_hooks": 0,
            "number_hooks": 0,
            "emotional_hooks": 0,
            "how_to_hooks": 0,
            "list_hooks": 0,
            "urgency_hooks": 0
        }
        
        question_words = ["how", "why", "what", "when", "where", "which", "who"]
        emotional_words = ["amazing", "shocking", "incredible", "secret", "revealed", "exposed"]
        urgency_words = ["now", "today", "urgent", "breaking", "just", "finally"]
        
        for title in titles:
            title_lower = title.lower()
            
            # Question hooks
            if any(word in title_lower for word in question_words) and "?" in title:
                hook_patterns["question_hooks"] += 1
            
            # Number hooks
            if re.search(r'\d+', title):
                hook_patterns["number_hooks"] += 1
            
            # Emotional hooks
            if any(word in title_lower for word in emotional_words):
                hook_patterns["emotional_hooks"] += 1
            
            # How-to hooks
            if "how to" in title_lower:
                hook_patterns["how_to_hooks"] += 1
            
            # List hooks
            if any(word in title_lower for word in ["ways", "tips", "reasons", "things"]):
                hook_patterns["list_hooks"] += 1
            
            # Urgency hooks
            if any(word in title_lower for word in urgency_words):
                hook_patterns["urgency_hooks"] += 1
        
        total = len(titles)
        return {pattern: (count / total * 100) for pattern, count in hook_patterns.items()}
    
    def _analyze_timing(self, content: List[TrendingContent]) -> Dict:
        hour_performance = {}
        day_performance = {}
        
        for item in content:
            hour = item.created_at.hour
            day = item.created_at.strftime("%A")
            
            if hour not in hour_performance:
                hour_performance[hour] = []
            hour_performance[hour].append(item.virality_score)
            
            if day not in day_performance:
                day_performance[day] = []
            day_performance[day].append(item.virality_score)
        
        # Calculate average performance by time
        best_hours = {hour: sum(scores)/len(scores) for hour, scores in hour_performance.items()}
        best_days = {day: sum(scores)/len(scores) for day, scores in day_performance.items()}
        
        return {
            "best_hours": sorted(best_hours.items(), key=lambda x: x[1], reverse=True)[:5],
            "best_days": sorted(best_days.items(), key=lambda x: x[1], reverse=True)[:3],
            "timing_insights": self._generate_timing_insights(best_hours, best_days)
        }
    
    def _analyze_emotions(self, content: List[TrendingContent]) -> Dict:
        sentiment_performance = {}
        
        for item in content:
            sentiment = item.sentiment
            if sentiment not in sentiment_performance:
                sentiment_performance[sentiment] = []
            sentiment_performance[sentiment].append(item.virality_score)
        
        avg_performance = {
            sentiment: sum(scores)/len(scores) 
            for sentiment, scores in sentiment_performance.items()
        }
        
        return {
            "sentiment_performance": avg_performance,
            "best_sentiment": max(avg_performance.items(), key=lambda x: x[1])[0],
            "emotion_insights": self._generate_emotion_insights(avg_performance)
        }
    
    def _analyze_formats(self, content: List[TrendingContent]) -> Dict:
        platform_formats = {}
        
        for item in content:
            platform = item.platform
            if platform not in platform_formats:
                platform_formats[platform] = {"short_form": 0, "long_form": 0, "visual": 0}
            
            # Classify content format based on description length and platform
            desc_length = len(item.description or "")
            
            if platform == "youtube":
                platform_formats[platform]["visual"] += 1
            elif desc_length < 100:
                platform_formats[platform]["short_form"] += 1
            else:
                platform_formats[platform]["long_form"] += 1
        
        return platform_formats
    
    def _analyze_topic_trends(self, content: List[TrendingContent]) -> Dict:
        topic_performance = {}
        
        for item in content:
            topic = item.topic_cluster
            if topic not in topic_performance:
                topic_performance[topic] = {
                    "count": 0,
                    "total_score": 0,
                    "avg_engagement": 0
                }
            
            topic_performance[topic]["count"] += 1
            topic_performance[topic]["total_score"] += item.virality_score
            topic_performance[topic]["avg_engagement"] += item.engagement_rate
        
        # Calculate averages
        for topic in topic_performance:
            count = topic_performance[topic]["count"]
            topic_performance[topic]["avg_virality"] = topic_performance[topic]["total_score"] / count
            topic_performance[topic]["avg_engagement"] = topic_performance[topic]["avg_engagement"] / count
        
        # Sort by average virality
        sorted_topics = sorted(
            topic_performance.items(), 
            key=lambda x: x[1]["avg_virality"], 
            reverse=True
        )
        
        return {
            "top_topics": sorted_topics[:10],
            "topic_insights": self._generate_topic_insights(sorted_topics)
        }
    
    def _analyze_platform_performance(self, content: List[TrendingContent]) -> Dict:
        platform_stats = {}
        
        for item in content:
            platform = item.platform
            if platform not in platform_stats:
                platform_stats[platform] = {
                    "count": 0,
                    "total_virality": 0,
                    "total_engagement": 0,
                    "avg_score": 0
                }
            
            platform_stats[platform]["count"] += 1
            platform_stats[platform]["total_virality"] += item.virality_score
            platform_stats[platform]["total_engagement"] += item.engagement_rate
            platform_stats[platform]["avg_score"] += item.score
        
        # Calculate averages
        for platform in platform_stats:
            count = platform_stats[platform]["count"]
            platform_stats[platform]["avg_virality"] = platform_stats[platform]["total_virality"] / count
            platform_stats[platform]["avg_engagement"] = platform_stats[platform]["total_engagement"] / count
            platform_stats[platform]["avg_score"] = platform_stats[platform]["avg_score"] / count
        
        return platform_stats
    
    def _content_to_dict(self, content: TrendingContent) -> Dict:
        return {
            "id": content.id,
            "platform": content.platform,
            "title": content.title,
            "description": content.description,
            "url": content.url,
            "author": content.author,
            "score": content.score,
            "comments_count": content.comments_count,
            "engagement_rate": content.engagement_rate,
            "virality_score": content.virality_score,
            "tags": content.tags,
            "sentiment": content.sentiment,
            "topic_cluster": content.topic_cluster,
            "created_at": content.created_at.isoformat(),
            "fetched_at": content.fetched_at.isoformat()
        }
    
    def _get_platform_breakdown(self, content: List[TrendingContent]) -> Dict:
        platform_count = Counter([c.platform for c in content])
        return dict(platform_count)
    
    def _get_top_topics(self, content: List[TrendingContent]) -> List[Dict]:
        topic_count = Counter([c.topic_cluster for c in content])
        return [{"topic": topic, "count": count} for topic, count in topic_count.most_common(10)]
    
    def _get_engagement_trends(self, content: List[TrendingContent]) -> Dict:
        engagement_rates = [c.engagement_rate for c in content]
        return {
            "avg_engagement": sum(engagement_rates) / len(engagement_rates),
            "max_engagement": max(engagement_rates),
            "min_engagement": min(engagement_rates)
        }
    
    def _get_sentiment_distribution(self, content: List[TrendingContent]) -> Dict:
        sentiment_count = Counter([c.sentiment for c in content])
        return dict(sentiment_count)
    
    def _get_recommendation_reason(self, content: TrendingContent, content_type: str) -> str:
        reasons = []
        
        if content.virality_score >= 90:
            reasons.append("Extremely viral content")
        elif content.virality_score >= 80:
            reasons.append("High viral potential")
        
        if content.engagement_rate > 5:
            reasons.append("High engagement rate")
        
        if content_type in ["tweet", "linkedin"] and len(content.title) < 100:
            reasons.append("Good length for social media")
        
        return " | ".join(reasons) if reasons else "Similar topic performance"
    
    def _generate_timing_insights(self, best_hours: Dict, best_days: Dict) -> List[str]:
        insights = []
        
        peak_hour = max(best_hours.items(), key=lambda x: x[1])[0]
        peak_day = max(best_days.items(), key=lambda x: x[1])[0]
        
        insights.append(f"Peak performance hour: {peak_hour}:00")
        insights.append(f"Best day for virality: {peak_day}")
        
        return insights
    
    def _generate_emotion_insights(self, sentiment_performance: Dict) -> List[str]:
        insights = []
        
        if "positive" in sentiment_performance and sentiment_performance["positive"] > 70:
            insights.append("Positive content performs significantly better")
        
        if "negative" in sentiment_performance and sentiment_performance["negative"] > sentiment_performance.get("positive", 0):
            insights.append("Negative content generates higher engagement")
        
        return insights
    
    def _generate_topic_insights(self, sorted_topics: List) -> List[str]:
        insights = []
        
        if sorted_topics:
            top_topic = sorted_topics[0][0]
            insights.append(f"'{top_topic}' is the highest performing topic cluster")
        
        if len(sorted_topics) >= 3:
            trending = [topic[0] for topic in sorted_topics[:3]]
            insights.append(f"Trending topics: {', '.join(trending)}")
        
        return insights
    
    def _store_patterns(self, db: Session, patterns: Dict):
        try:
            for pattern_type, pattern_data in patterns.items():
                viral_pattern = ViralityPattern(
                    pattern_type=pattern_type,
                    pattern_data=pattern_data,
                    success_rate=self._calculate_pattern_success_rate(pattern_data),
                    platforms=["reddit", "youtube"],  # Update based on analysis
                    topic_clusters=list(patterns.get("topic_trends", {}).get("top_topics", []))
                )
                db.add(viral_pattern)
            
            db.commit()
            logger.info("Stored virality patterns in database")
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing patterns: {str(e)}")
    
    def _calculate_pattern_success_rate(self, pattern_data) -> float:
        # Simple success rate calculation - can be enhanced
        if isinstance(pattern_data, dict) and "avg_virality" in str(pattern_data):
            return 75.0  # Placeholder
        return 50.0