import openai
import os
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models import GeneratedContent, BrandVoice, TrendingContent
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI()
    
    async def generate_content(self, db: Session, trend_id: int, content_type: str, 
                             brand_voice: str, target_audience: str) -> Dict:
        try:
            # Get the trending content
            trend = db.query(TrendingContent).filter(TrendingContent.id == trend_id).first()
            if not trend:
                raise ValueError("Trend not found")
            
            # Get brand voice profile if exists
            brand_profile = db.query(BrandVoice).filter(BrandVoice.brand_name == brand_voice).first()
            
            # Generate content based on type
            generated_text = await self._generate_by_type(trend, content_type, brand_voice, target_audience, brand_profile)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(generated_text, content_type)
            
            # Store generated content
            generated_content = GeneratedContent(
                trend_id=trend_id,
                content_type=content_type,
                generated_text=generated_text,
                brand_voice=brand_voice,
                target_audience=target_audience,
                quality_score=quality_score,
                topic_cluster=trend.topic_cluster,
                performance_prediction=self._predict_performance(trend, generated_text)
            )
            
            db.add(generated_content)
            db.commit()
            
            return {
                "id": generated_content.id,
                "content": generated_text,
                "quality_score": quality_score,
                "performance_prediction": generated_content.performance_prediction,
                "inspiration_source": {
                    "title": trend.title,
                    "platform": trend.platform,
                    "virality_score": trend.virality_score
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            raise e
    
    async def _generate_by_type(self, trend: TrendingContent, content_type: str, 
                               brand_voice: str, target_audience: str, brand_profile: Optional[BrandVoice]) -> str:
        
        # Build context from trending content
        context = f"""
        Inspiration Source:
        - Title: {trend.title}
        - Platform: {trend.platform}
        - Topic: {trend.topic_cluster}
        - Virality Score: {trend.virality_score}
        - Engagement Rate: {trend.engagement_rate}%
        
        Target Audience: {target_audience}
        Brand Voice: {brand_voice}
        """
        
        if brand_profile:
            context += f"\nBrand Characteristics: {json.dumps(brand_profile.characteristics)}"
        
        # Content type specific prompts
        prompts = {
            "tweet": self._get_tweet_prompt(context, trend),
            "linkedin": self._get_linkedin_prompt(context, trend),
            "script": self._get_script_prompt(context, trend),
            "carousel": self._get_carousel_prompt(context, trend)
        }
        
        if content_type not in prompts:
            raise ValueError(f"Unsupported content type: {content_type}")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert content creator who specializes in creating viral, engaging content across social media platforms. You analyze trends and create original content inspired by successful patterns."},
                    {"role": "user", "content": prompts[content_type]}
                ],
                temperature=0.8,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise e
    
    def _get_tweet_prompt(self, context: str, trend: TrendingContent) -> str:
        return f"""
        {context}
        
        Create an original Twitter thread (1-3 tweets) inspired by the above trending content. 
        
        Requirements:
        - Maximum 280 characters per tweet
        - Use engaging hooks and viral patterns
        - Include relevant hashtags
        - Make it original - do NOT copy the source content
        - Focus on the underlying pattern that made it viral
        - Match the specified brand voice
        - Appeal to the target audience
        
        Format as: 
        Tweet 1: [content]
        Tweet 2: [content] (if applicable)
        Tweet 3: [content] (if applicable)
        """
    
    def _get_linkedin_prompt(self, context: str, trend: TrendingContent) -> str:
        return f"""
        {context}
        
        Create an original LinkedIn post inspired by the above trending content.
        
        Requirements:
        - Professional yet engaging tone
        - 1300 characters or less
        - Include a compelling hook
        - Add value to professional network
        - Use relevant hashtags (3-5)
        - Include a call-to-action
        - Make it original - extract the viral pattern, not the content
        - Match the specified brand voice
        
        Format as a complete LinkedIn post.
        """
    
    def _get_script_prompt(self, context: str, trend: TrendingContent) -> str:
        return f"""
        {context}
        
        Create an original video script inspired by the above trending content.
        
        Requirements:
        - 30-60 second video script
        - Strong hook in first 3 seconds
        - Clear structure: Hook → Value → Call-to-action
        - Include visual cues and timing
        - Make it original - focus on the viral elements
        - Match the specified brand voice
        - Suitable for platforms like TikTok, Instagram Reels, YouTube Shorts
        
        Format:
        [HOOK - 0-3 seconds]
        [MAIN CONTENT - 3-45 seconds]
        [CALL TO ACTION - 45-60 seconds]
        """
    
    def _get_carousel_prompt(self, context: str, trend: TrendingContent) -> str:
        return f"""
        {context}
        
        Create an original Instagram carousel post inspired by the above trending content.
        
        Requirements:
        - 5-7 slides
        - Each slide should have a clear headline and 2-3 bullet points
        - Strong hook on slide 1
        - Clear progression and value
        - Call-to-action on final slide
        - Make it original - extract valuable patterns
        - Match the specified brand voice
        
        Format:
        Slide 1: [Headline] - [Content]
        Slide 2: [Headline] - [Content]
        ... etc
        """
    
    async def train_brand_voice(self, sample_content: List[str], brand_name: str, tone: str) -> Dict:
        try:
            # Analyze brand voice characteristics
            analysis_prompt = f"""
            Analyze the following content samples to identify the brand voice characteristics:
            
            Content Samples:
            {chr(10).join([f"- {content}" for content in sample_content])}
            
            Brand: {brand_name}
            Stated Tone: {tone}
            
            Identify:
            1. Writing style patterns
            2. Vocabulary preferences
            3. Sentence structure
            4. Personality traits
            5. Key messaging themes
            6. Humor style (if any)
            7. Technical level
            8. Emotional tone patterns
            
            Return as structured analysis.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a brand voice analysis expert. Analyze content to identify unique voice characteristics and patterns."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            analysis = response.choices[0].message.content.strip()
            
            # Parse analysis into structured format
            characteristics = self._parse_voice_analysis(analysis)
            
            # Store brand voice in database
            db = Session()
            try:
                # Check if brand voice already exists
                existing = db.query(BrandVoice).filter(BrandVoice.brand_name == brand_name).first()
                
                if existing:
                    existing.characteristics = characteristics
                    existing.sample_content = sample_content
                    existing.tone = tone
                else:
                    brand_voice = BrandVoice(
                        brand_name=brand_name,
                        tone=tone,
                        characteristics=characteristics,
                        sample_content=sample_content,
                        voice_embedding={}  # Could store vector embeddings for advanced matching
                    )
                    db.add(brand_voice)
                
                db.commit()
                logger.info(f"Trained brand voice for {brand_name}")
                
                return {
                    "brand_name": brand_name,
                    "characteristics": characteristics,
                    "training_samples": len(sample_content),
                    "status": "trained"
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error training brand voice: {str(e)}")
            raise e
    
    def _parse_voice_analysis(self, analysis: str) -> Dict:
        # Simple parsing - in production, you'd want more sophisticated NLP
        characteristics = {
            "style": "conversational",
            "vocabulary": "accessible",
            "personality": "friendly",
            "technical_level": "moderate",
            "humor": "light",
            "formality": "casual"
        }
        
        analysis_lower = analysis.lower()
        
        # Style detection
        if "formal" in analysis_lower:
            characteristics["style"] = "formal"
        elif "casual" in analysis_lower:
            characteristics["style"] = "casual"
        
        # Personality detection
        if "professional" in analysis_lower:
            characteristics["personality"] = "professional"
        elif "playful" in analysis_lower:
            characteristics["personality"] = "playful"
        elif "authoritative" in analysis_lower:
            characteristics["personality"] = "authoritative"
        
        # Technical level
        if "technical" in analysis_lower or "expert" in analysis_lower:
            characteristics["technical_level"] = "high"
        elif "beginner" in analysis_lower or "simple" in analysis_lower:
            characteristics["technical_level"] = "low"
        
        return characteristics
    
    def _calculate_quality_score(self, content: str, content_type: str) -> float:
        quality_score = 50.0  # Base score
        
        # Length checks
        if content_type == "tweet":
            if 100 <= len(content) <= 280:
                quality_score += 20
        elif content_type == "linkedin":
            if 500 <= len(content) <= 1300:
                quality_score += 20
        
        # Engagement elements
        if "?" in content:  # Questions increase engagement
            quality_score += 10
        if "#" in content:  # Hashtags
            quality_score += 5
        if any(word in content.lower() for word in ["how", "why", "what", "when"]):
            quality_score += 10
        
        # Hook strength (first sentence)
        first_sentence = content.split('.')[0] if '.' in content else content.split('\n')[0]
        if len(first_sentence) < 50 and any(word in first_sentence.lower() for word in ["secret", "revealed", "shocking", "amazing"]):
            quality_score += 15
        
        return min(quality_score, 100.0)
    
    def _predict_performance(self, trend: TrendingContent, generated_content: str) -> float:
        # Simple performance prediction based on source trend and content characteristics
        base_score = trend.virality_score * 0.6  # Inherit some virality from source
        
        # Content factors
        if len(generated_content) > 50:  # Substantial content
            base_score += 10
        if "?" in generated_content:  # Questions
            base_score += 5
        if "#" in generated_content:  # Hashtags
            base_score += 5
        
        return min(base_score, 100.0)
    
    def get_generated_content(self, db: Session, limit: int = 50, topic: Optional[str] = None) -> List[Dict]:
        query = db.query(GeneratedContent).order_by(GeneratedContent.performance_prediction.desc())
        
        if topic:
            query = query.filter(GeneratedContent.topic_cluster == topic)
        
        content = query.limit(limit).all()
        
        result = []
        for item in content:
            # Get trend info
            trend = db.query(TrendingContent).filter(TrendingContent.id == item.trend_id).first()
            
            content_dict = {
                "id": item.id,
                "content_type": item.content_type,
                "generated_text": item.generated_text,
                "brand_voice": item.brand_voice,
                "target_audience": item.target_audience,
                "quality_score": item.quality_score,
                "topic_cluster": item.topic_cluster,
                "performance_prediction": item.performance_prediction,
                "is_used": item.is_used,
                "created_at": item.created_at.isoformat(),
                "inspiration_source": {
                    "title": trend.title if trend else "Unknown",
                    "platform": trend.platform if trend else "Unknown",
                    "virality_score": trend.virality_score if trend else 0
                }
            }
            result.append(content_dict)
        
        return result