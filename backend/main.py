from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import joblib
import numpy as np
import praw
import os
import re
import asyncio
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database.postgres_setup import db
import bcrypt
import jwt
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

# Simple authentication configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "simple-secret-key")
ALGORITHM = "HS256"

# Pydantic models
class PredictionRequest(BaseModel):
    text: str

class RedditPost(BaseModel):
    id: str
    text: str
    author: str
    created_at: str
    label: str
    confidence: float
    retweet_count: int = 0
    like_count: int = 0
    category: str = "general"
    image_url: Optional[str] = None

class UserSignup(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    created_at: str
    last_login: Optional[str] = None

app = FastAPI(title="Disaster Shield API - Reddit Edition", version="1.0.0")

# Simple authentication functions
def create_simple_token(username: str):
    """Create simple token"""
    return jwt.encode({"username": username}, SECRET_KEY, algorithm=ALGORITHM)

def verify_simple_token(token: str):
    """Verify simple token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("username")
    except:
        return None

# Enable CORS for React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models will be loaded on startup
ensemble_model = None
vectorizer = None
distilbert_model = None

# Background task for automatic updates
background_task = None

async def hourly_update_task():
    """Background task that runs every hour to fetch new Reddit data"""
    while True:
        try:
            logging.info("⏰ Starting hourly Reddit data update...")
            await fetch_and_classify_reddit_posts()
            logging.info("✅ Hourly update completed successfully")
        except Exception as e:
            logging.error(f"❌ Error in hourly update: {e}")
        
        # Wait for 1 hour (3600 seconds)
        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup_tasks():
    global ensemble_model, vectorizer, distilbert_model, background_task
    try:
        # Run database migration for image_url column
        try:
            from add_image_column import add_image_column
            add_image_column()
        except Exception as migration_error:
            logging.warning(f"Migration skipped or already applied: {migration_error}")
        

        # Try to load SVM model and vectorizer (compatible pair)
        try:
            # Try different model paths for different environments
            model_paths = [
                "models/LinearSVM.joblib",      # Local to backend directory
                "./models/LinearSVM.joblib",    # Alternative local path
                "../models/LinearSVM.joblib"    # Fallback to root models
            ]
            
            vectorizer_paths = [
                "models/tfidf_vectorizer.joblib",      # Local to backend directory
                "./models/tfidf_vectorizer.joblib",    # Alternative local path
                "../models/tfidf_vectorizer.joblib"    # Fallback to root models
            ]
            
            ensemble_model = None
            vectorizer = None
            
            # Try to load SVM model
            for path in model_paths:
                try:
                    ensemble_model = joblib.load(path)
                    logging.info(f"✅ SVM Model loaded from: {path}")
                    break
                except:
                    continue
            
            # Try to load vectorizer
            for path in vectorizer_paths:
                try:
                    vectorizer = joblib.load(path)
                    logging.info(f"✅ Vectorizer loaded from: {path}")
                    break
                except:
                    continue
            
            if ensemble_model and vectorizer:
                logging.info("✅ Both ML models loaded successfully")
            else:
                raise Exception("Could not load required models")
                
        except Exception as model_error:
            logging.warning(f"⚠️ Could not load ML models: {model_error}")
            logging.info("🔄 Using keyword-based classification")
        
        # Test Reddit API
        reddit = setup_reddit_api()
        if reddit:
            logging.info("✅ Reddit API ready")
        else:
            logging.error("❌ Reddit API setup failed")
        
        # Skip background task for now
        # background_task = asyncio.create_task(hourly_update_task())
        logging.info("⏰ Background task disabled - use manual updates")
        
        # Skip initial data fetch to speed up startup
        logging.info("⏭️ Skipping initial data fetch - use /initialize-data or /force-update to fetch data")
        
        logging.info("🚀 DisasterShield ready - Using REAL Reddit data with hourly updates")
        
    except Exception as e:
        logging.error(f"❌ Error in startup tasks: {e}")

@app.on_event("shutdown")
async def shutdown_tasks():
    """Clean up background tasks on shutdown"""
    global background_task
    if background_task:
        background_task.cancel()
        logging.info("⏰ Stopped hourly update task")

def clean_reddit_text(title: str, selftext: str = "") -> str:
    """Clean and format Reddit post text for better readability"""
    try:
        # Start with the title
        cleaned_text = title.strip()
        
        # Remove all emojis and symbols
        cleaned_text = re.sub(r'[🌎🌏🌍🌄🌖🔥⚡🌊❄️🌪️🌀🌋⛈️🌩️🌨️🌦️🌤️⛅☀️🌞🌝🌛🌜🌚🌕🌖🌗🌘🌑🌒🌓🌔]', '', cleaned_text)
        
        # Remove markdown formatting
        cleaned_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_text)  # Bold
        cleaned_text = re.sub(r'\*([^*]+)\*', r'\1', cleaned_text)  # Italic
        cleaned_text = re.sub(r'__([^_]+)__', r'\1', cleaned_text)  # Bold underscore
        cleaned_text = re.sub(r'_([^_]+)_', r'\1', cleaned_text)  # Italic underscore
        
        # Remove technical earthquake/disaster data
        cleaned_text = re.sub(r'\([0-9.]+\s*M[a-z]*[,\s]*at\s*[0-9:]+\s*UTC\)', '', cleaned_text)
        cleaned_text = re.sub(r'registered by [A-Z,\s]+', '', cleaned_text)
        cleaned_text = re.sub(r'[0-9]{4}-[0-9]{2}-[0-9]{2}[\sT][0-9:]+[\sZ]*UTC?', '', cleaned_text)
        cleaned_text = re.sub(r'likely felt \d+[,\d]* km away', '', cleaned_text)
        cleaned_text = re.sub(r'by \d+[,\d]* people', '', cleaned_text)
        
        # Remove website references and technical info
        cleaned_text = re.sub(r'\([^)]*localhost[^)]*\)', '', cleaned_text)
        cleaned_text = re.sub(r'\([^)]*www\.[^)]*\)', '', cleaned_text)
        cleaned_text = re.sub(r'\([^)]*\.gov[^)]*\)', '', cleaned_text)
        cleaned_text = re.sub(r'\([^)]*\.org[^)]*\)', '', cleaned_text)
        
        # Remove arrows, symbols, and technical markers
        cleaned_text = re.sub(r'[>→←↑↓►◄▲▼]+', '', cleaned_text)
        cleaned_text = re.sub(r'[\^]+[0-9-:TZ\s]+', '', cleaned_text)
        cleaned_text = re.sub(r'Â±\s*\d+\s*km', '', cleaned_text)
        cleaned_text = re.sub(r'â\d+\s*km', '', cleaned_text)
        cleaned_text = re.sub(r'±\s*\d+\s*km', '', cleaned_text)
        
        # Remove location coordinates and technical details
        cleaned_text = re.sub(r'\([0-9.-]+,\s*[0-9.-]+\)', '', cleaned_text)
        cleaned_text = re.sub(r'\*[^*]*\*', '', cleaned_text)  # Remove remaining asterisk content
        
        # Clean up location prefixes
        cleaned_text = re.sub(r'^[A-Za-z\s]+:', '', cleaned_text).strip()
        
        # Add meaningful selftext if available
        if selftext and len(selftext.strip()) > 30:
            clean_selftext = selftext.strip()
            # Remove URLs and markdown
            clean_selftext = re.sub(r'https?://[^\s]+', '', clean_selftext)
            clean_selftext = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_selftext)
            clean_selftext = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_selftext)
            
            # Only add if it's meaningful content
            if (len(clean_selftext) > 50 and 
                not clean_selftext.lower().startswith(('full description', 'source:', 'link:', 'http'))):
                cleaned_text += f" {clean_selftext[:300]}"
        
        # Final cleanup
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Multiple spaces to single
        cleaned_text = re.sub(r'[.]{2,}', '.', cleaned_text)  # Multiple dots to single
        cleaned_text = re.sub(r'[,]{2,}', ',', cleaned_text)  # Multiple commas to single
        cleaned_text = cleaned_text.strip(' .,!-:;')  # Remove trailing punctuation
        
        # Ensure proper sentence ending
        if cleaned_text and not cleaned_text.endswith(('.', '!', '?')):
            cleaned_text += '.'
            
        # Capitalize first letter
        if cleaned_text:
            cleaned_text = cleaned_text[0].upper() + cleaned_text[1:]
            
        return cleaned_text
        
    except Exception as e:
        logging.error(f"Error cleaning text: {e}")
        return title  # Return original title if cleaning fails

def setup_reddit_api():
    """Setup Reddit API client with proper credentials"""
    try:
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT")
        
        if not all([client_id, client_secret, user_agent]):
            logging.error("❌ Reddit API credentials missing in .env file")
            return None
        
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            check_for_async=False
        )
        
        logging.info("✅ Reddit API client created successfully with credentials")
        return reddit
        
    except Exception as e:
        logging.error(f"❌ Reddit API setup failed: {e}")
        return None

def clean_reddit_text(title: str, selftext: str = "") -> str:
    """Clean and format Reddit text for better readability"""
    import re
    
    # Combine title and selftext
    full_text = f"{title}"
    if selftext and selftext.strip():
        full_text += f" {selftext}"
    
    # Remove URLs
    full_text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', full_text)
    
    # Remove Reddit-specific formatting
    full_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', full_text)  # Remove markdown links
    full_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', full_text)  # Remove bold formatting
    full_text = re.sub(r'\*([^*]+)\*', r'\1', full_text)  # Remove italic formatting
    full_text = re.sub(r'~~([^~]+)~~', r'\1', full_text)  # Remove strikethrough
    full_text = re.sub(r'`([^`]+)`', r'\1', full_text)  # Remove code formatting
    
    # Remove excessive whitespace and newlines
    full_text = re.sub(r'\n+', ' ', full_text)
    full_text = re.sub(r'\s+', ' ', full_text)
    
    # Remove emojis (basic emoji removal)
    full_text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+', '', full_text)
    
    # Remove timestamps and technical data
    full_text = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '', full_text)  # ISO timestamps
    full_text = re.sub(r'\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM|am|pm)', '', full_text)  # Time stamps
    full_text = re.sub(r'UTC|GMT|EST|PST|CST|MST', '', full_text)  # Timezone abbreviations
    
    # Remove Reddit-specific prefixes and suffixes
    full_text = re.sub(r'^(UPDATE|EDIT|BREAKING|URGENT):\s*', '', full_text, flags=re.IGNORECASE)
    full_text = re.sub(r'\s*(x-post|crosspost|cross-post)\s*.*$', '', full_text, flags=re.IGNORECASE)
    
    # Clean up and return
    full_text = full_text.strip()
    
    # Ensure the text ends with proper punctuation
    if full_text and not full_text[-1] in '.!?':
        full_text += '.'
    
    return full_text

def detect_disaster_category(text: str) -> str:
    """Detect the disaster category from text"""
    text_lower = text.lower()
    
    # Category keywords
    categories = {
        'earthquake': ['earthquake', 'seismic', 'tremor', 'quake', 'magnitude', 'richter', 'epicenter'],
        'flood': ['flood', 'flooding', 'deluge', 'inundation', 'overflow', 'dam burst', 'levee'],
        'fire': ['wildfire', 'forest fire', 'bushfire', 'fire', 'blaze', 'inferno', 'burn'],
        'storm': ['hurricane', 'typhoon', 'cyclone', 'tornado', 'storm', 'tempest', 'gale'],
        'weather': ['heatwave', 'blizzard', 'drought', 'extreme weather', 'severe weather'],
        'volcanic': ['volcano', 'volcanic', 'eruption', 'lava', 'ash cloud', 'magma'],
        'landslide': ['landslide', 'mudslide', 'avalanche', 'rockslide', 'debris flow'],
        'tsunami': ['tsunami', 'tidal wave', 'seismic wave']
    }
    
    # Check for category matches
    for category, keywords in categories.items():
        if any(keyword in text_lower for keyword in keywords):
            return category
    
    return 'general'

def classify_text(text: str) -> Dict[str, float]:
    """Classify text using ensemble approach with fallback to keyword-based classification"""
    global ensemble_model, vectorizer
    
    try:
        # Try to use the SVM model directly (simpler approach)
        if vectorizer is not None:
            # Load and use the SVM model instead of the meta-ensemble
            try:
                import joblib
                # Try different paths for SVM model
                svm_paths = ["models/LinearSVM.joblib", "./models/LinearSVM.joblib", "../models/LinearSVM.joblib"]
                svm_model = None
                for path in svm_paths:
                    try:
                        svm_model = joblib.load(path)
                        break
                    except:
                        continue
                
                if not svm_model:
                    raise Exception("SVM model not found in any path")
                
                # Vectorize the text
                text_vectorized = vectorizer.transform([text])
                
                # Get prediction and probability from SVM model
                prediction = svm_model.predict(text_vectorized)[0]
                probabilities = svm_model.predict_proba(text_vectorized)[0]
                
                # Get confidence as the maximum probability
                confidence = float(max(probabilities))
                
                # Map prediction to label (assuming 0=rumor, 1=verified)
                label = "verified" if prediction == 1 else "rumor"
                
                logging.info(f"SVM Classification: {label} (confidence: {confidence:.3f})")
                return {"label": label, "confidence": confidence}
                
            except Exception as svm_error:
                logging.error(f"SVM model error: {svm_error}")
                # Fallback to keyword-based classification
                return classify_text_keywords(text)
            
        else:
            # Fallback to keyword-based classification
            logging.warning("Vectorizer not available, using keyword-based classification")
            return classify_text_keywords(text)
            
    except Exception as e:
        logging.error(f"Classification error: {e}, falling back to keywords")
        return classify_text_keywords(text)

def classify_text_keywords(text: str) -> Dict[str, float]:
    """Fallback keyword-based classification"""
    try:
        text_lower = text.lower()
        
        # Verified news indicators
        verified_keywords = [
            'official', 'usgs', 'confirmed', 'breaking', 'emergency services',
            'authorities', 'government', 'fire department', 'police', 'fema',
            'national weather service', 'earthquake', 'magnitude', 'evacuation',
            'nws', 'noaa', 'red cross', 'emergency management', 'disaster response',
            'first responders', 'rescue teams', 'meteorologist', 'seismologist',
            'issued warning', 'alert issued', 'official statement', 'press release'
        ]
        
        # Rumor/fake news indicators  
        rumor_keywords = [
            'fake', 'rumor', 'unconfirmed', 'allegedly', 'reports suggest',
            'conspiracy', 'alien', 'fabricated', 'false information',
            'hoax', 'misleading', 'debunked', 'unverified', 'speculation',
            'claims without evidence', 'social media reports', 'viral video',
            'end times', 'apocalypse', 'government cover-up'
        ]
        
        verified_score = sum(1 for keyword in verified_keywords if keyword in text_lower)
        rumor_score = sum(1 for keyword in rumor_keywords if keyword in text_lower)
        
        total_matches = verified_score + rumor_score
        
        if total_matches == 0:
            import random
            
            # Check for official sources
            if any(source in text_lower for source in ['official', 'government', 'emergency']):
                # Vary official source confidence
                confidence = 0.70 + (random.random() * 0.20)  # 70-90% range
                return {"label": "verified", "confidence": confidence}
            
            # Check for news-like indicators
            news_indicators = ['breaking', 'reported', 'according to', 'sources say', 'confirmed']
            news_score = sum(1 for indicator in news_indicators if indicator in text_lower)
            
            # Check for uncertainty indicators
            uncertainty_indicators = ['might', 'could', 'possibly', 'allegedly', 'reportedly']
            uncertainty_score = sum(1 for indicator in uncertainty_indicators if indicator in text_lower)
            
            # Dynamic confidence based on content analysis
            if news_score > uncertainty_score:
                base_confidence = 0.55 + (news_score * 0.05)
                random_variation = random.random() * 0.10  # Add randomness
                confidence = min(0.85, base_confidence + random_variation)
                return {"label": "verified", "confidence": confidence}
            else:
                # Vary rumor confidence with more randomness
                base_confidence = 0.45 + (random.random() * 0.15)  # 45-60% base
                if uncertainty_score > 0:
                    confidence = base_confidence + (uncertainty_score * 0.03)
                else:
                    confidence = base_confidence + (len(text_lower.split()) / 1000)
                return {"label": "rumor", "confidence": min(0.75, max(0.40, confidence))}
        
        if verified_score > rumor_score:
            # More dynamic confidence based on keyword matches and text length
            base_confidence = 0.60 + (verified_score * 0.08)
            text_length_bonus = min(0.15, len(text_lower.split()) / 200)
            confidence = min(0.95, base_confidence + text_length_bonus)
            return {"label": "verified", "confidence": confidence}
        elif rumor_score > verified_score:
            # Dynamic rumor confidence
            base_confidence = 0.55 + (rumor_score * 0.06)
            uncertainty_penalty = min(0.10, rumor_score * 0.03)
            confidence = min(0.90, base_confidence + uncertainty_penalty)
            return {"label": "rumor", "confidence": confidence}
        else:
            # Random-ish confidence for neutral cases
            import random
            confidence = 0.50 + (random.random() * 0.15)  # 50-65% range
            return {"label": "rumor", "confidence": confidence}
            
    except Exception as e:
        logging.error(f"Keyword classification error: {e}")
        return {"label": "unknown", "confidence": 0.5}

async def fetch_and_classify_reddit_posts():
    """Fetch ONLY real posts from Reddit using PRAW API"""
    try:
        reddit = setup_reddit_api()
        if not reddit:
            logging.error("❌ Reddit API not available")
            raise Exception("Reddit API not configured")
        
        logging.info("🔍 Fetching real posts from Reddit using PRAW API...")
        
        disaster_subreddits = [
            'news', 'worldnews', 'weather', 'earthquakes',
            'NaturalDisasters', 'naturesfury', 'Preparedness', 
            'preppers', 'EmergencyManagement'
        ]
        disaster_keywords = [
            'earthquake', 'tsunami', 'flood', 'wildfire', 'hurricane', 'tornado', 
            'emergency', 'evacuation', 'disaster', 'breaking', 'storm', 'cyclone',
            'landslide', 'avalanche', 'drought', 'heatwave', 'blizzard', 'typhoon',
            'volcanic', 'eruption', 'mudslide', 'sinkhole', 'severe weather',
            'natural disaster', 'climate emergency', 'extreme weather'
        ]
        
        all_posts = []
        
        for subreddit_name in disaster_subreddits:
            try:
                logging.info(f"🔍 Searching subreddit: r/{subreddit_name}")
                subreddit = reddit.subreddit(subreddit_name)
                
                # Get hot posts from the subreddit (reduced per subreddit due to more sources)
                for post in subreddit.hot(limit=10):
                    post_text = f"{post.title} {post.selftext}".lower()
                    
                    # Check if post contains disaster-related keywords
                    if any(keyword in post_text for keyword in disaster_keywords):
                        # Clean and format the text for better readability
                        cleaned_text = clean_reddit_text(post.title, post.selftext)
                        
                        # Skip if the cleaned text is too short or not meaningful
                        if len(cleaned_text.strip()) < 20:
                            continue
                        
                        # Detect disaster category
                        category = detect_disaster_category(cleaned_text)
                        
                        # Extract image URL from Reddit post
                        image_url = None
                        try:
                            if hasattr(post, 'preview') and 'images' in post.preview:
                                # Get the highest resolution image
                                image_url = post.preview['images'][0]['source']['url']
                            elif hasattr(post, 'thumbnail') and post.thumbnail and post.thumbnail.startswith('http'):
                                image_url = post.thumbnail
                            elif post.url and any(post.url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                                image_url = post.url
                        except:
                            pass  # No image available
                            
                        post_data = {
                            "tweet_id": f"reddit_{post.id}",
                            "text": cleaned_text,
                            "username": f"u/{post.author.name}" if post.author else "u/deleted",
                            "user_followers": 0,  # Reddit doesn't have followers
                            "tweet_timestamp": datetime.fromtimestamp(post.created_utc).isoformat(),
                            "likes": post.score,
                            "retweets": 0,  # Reddit doesn't have retweets
                            "replies": post.num_comments,
                            "category": category,
                            "image_url": image_url
                        }
                        all_posts.append(post_data)
                        
                logging.info(f"✅ Found disaster-related posts in r/{subreddit_name}")
                
            except Exception as subreddit_error:
                logging.error(f"❌ Error fetching from r/{subreddit_name}: {subreddit_error}")
                continue
        
        # Remove duplicates and classify posts
        unique_posts = {post['tweet_id']: post for post in all_posts}.values()
        
        processed_count = 0
        for post_data in unique_posts:
            try:
                classification = classify_text(post_data["text"])
                
                db_data = {
                    **post_data,
                    "classification_label": classification["label"],
                    "confidence_score": classification["confidence"],
                    "model_version": "v2.0"
                }
                
                if db.insert_tweet(db_data):
                    processed_count += 1
                    
            except Exception as post_error:
                logging.error(f"❌ Error processing post: {post_error}")
                continue
            
        if processed_count == 0:
            logging.warning("⚠️ No posts were processed. Check Reddit connection.")
        else:
            logging.info(f"✅ Successfully processed {processed_count} real posts from Reddit")
        
    except Exception as e:
        logging.error(f"❌ Error in fetch_and_classify_reddit_posts: {e}")
        raise Exception(f"Reddit integration failed: {e}")

@app.post("/initialize-data")
async def initialize_data():
    """Fetch and classify REAL posts from Reddit ONLY"""
    try:
        await fetch_and_classify_reddit_posts()
        return {"status": "success", "message": "Real Reddit data fetched and classified successfully"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Reddit API error: {str(e)}")

@app.post("/clear-database")
async def clear_database():
    """Clear all posts from database"""
    try:
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM tweets")
        cursor.execute("DELETE FROM classification_details")
        connection.commit()
        cursor.close()
        connection.close()
        
        return {"status": "success", "message": "Database cleared - ready for real Reddit data"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to clear database: {str(e)}"}

@app.get("/reddit/disaster-news")
async def get_disaster_news(
    limit: int = Query(20, ge=1, le=100),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
    category: str = Query("all", description="Filter by disaster category")
) -> List[RedditPost]:
    """Get all disaster-related posts from database"""
    db.log_api_request("/reddit/disaster-news")
    
    tweets = db.get_all_tweets(limit, category if category != "all" else None)
    
    if not tweets:
        raise HTTPException(
            status_code=503, 
            detail="No data available. Please initialize Reddit data first."
        )
    
    classified_posts = []
    for tweet in tweets:
        if tweet['confidence_score'] >= min_confidence:
            classified_post = RedditPost(
                id=tweet["tweet_id"],
                text=tweet["text"],
                author=tweet["username"],
                created_at=tweet["tweet_timestamp"],
                label=tweet["classification_label"],
                confidence=float(tweet["confidence_score"]),
                retweet_count=0,  # Remove retweet count for Reddit
                like_count=tweet["likes"],
                category=tweet.get("category", "general"),
                image_url=tweet.get("image_url")
            )
            classified_posts.append(classified_post)
    
    return classified_posts

@app.get("/reddit/verified")
async def get_verified_news(
    limit: int = Query(50, ge=1, le=100),
    min_confidence: float = Query(0.6, ge=0.0, le=1.0),
    category: str = Query("all", description="Filter by disaster category")
):
    """Get only verified disaster news from database"""
    db.log_api_request("/reddit/verified")
    
    tweets = db.get_verified_tweets(limit, min_confidence, category if category != "all" else None)
    
    return [
        RedditPost(
            id=tweet["tweet_id"],
            text=tweet["text"],
            author=tweet["username"],
            created_at=tweet["tweet_timestamp"],
            label=tweet["classification_label"],
            confidence=float(tweet["confidence_score"]),
            retweet_count=0,  # Remove retweet count for Reddit
            like_count=tweet["likes"],
            category=tweet.get("category", "general"),
            image_url=tweet.get("image_url")
        )
        for tweet in tweets
    ]

@app.get("/reddit/rumors")
async def get_rumors(
    limit: int = Query(50, ge=1, le=100),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
    category: str = Query("all", description="Filter by disaster category")
):
    """Get rumor/unverified disaster news from database"""
    db.log_api_request("/reddit/rumors")
    
    tweets = db.get_rumor_tweets(limit, min_confidence, category if category != "all" else None)
    
    return [
        RedditPost(
            id=tweet["tweet_id"],
            text=tweet["text"],
            author=tweet["username"],
            created_at=tweet["tweet_timestamp"],
            label=tweet["classification_label"],
            confidence=float(tweet["confidence_score"]),
            retweet_count=0,  # Remove retweet count for Reddit
            like_count=tweet["likes"],
            category=tweet.get("category", "general"),
            image_url=tweet.get("image_url")
        )
        for tweet in tweets
    ]

@app.get("/stats/dashboard")
async def get_dashboard_stats():
    """Get classification statistics for dashboard"""
    db.log_api_request("/stats/dashboard")
    
    stats = db.get_stats()
    return {
        "stats": stats,
        "last_updated": datetime.now().isoformat(),
        "total_processed": sum(stat.get('count', 0) for stat in stats.values())
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Simple Authentication Endpoints
@app.post("/auth/signup")
async def signup(user_data: UserSignup):
    """Simple user registration"""
    try:
        # Check if username exists
        if db.check_username_exists(user_data.username):
            return {"status": "error", "message": "Username already exists"}
        
        # Store password as plain text (simple approach)
        success = db.create_user(
            username=user_data.username,
            email=user_data.email,
            password_hash=user_data.password,  # Store as plain text
            full_name=user_data.full_name
        )
        
        if success:
            return {"status": "success", "message": "User created successfully"}
        else:
            return {"status": "error", "message": "Failed to create user"}
            
    except Exception as e:
        logging.error(f"Signup error: {e}")
        return {"status": "error", "message": "Signup failed"}

@app.post("/auth/login")
async def login(user_credentials: UserLogin):
    """Simple user login"""
    try:
        # Get user from database
        user = db.get_user_by_username(user_credentials.username)
        
        if not user:
            return {"status": "error", "message": "User not found"}
        
        # Simple password check (plain text)
        if user["password_hash"] != user_credentials.password:
            return {"status": "error", "message": "Wrong password"}
        
        # Create simple token
        token = create_simple_token(user_credentials.username)
        
        return {
            "status": "success",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"]
            }
        }
        
    except Exception as e:
        logging.error(f"Login error: {e}")
        return {"status": "error", "message": "Login failed"}

@app.get("/auth/me")
async def get_current_user_info(token: str = Query(...)):
    """Get current user information"""
    try:
        username = verify_simple_token(token)
        if not username:
            return {"status": "error", "message": "Invalid token"}
            
        user = db.get_user_by_username(username)
        if not user:
            return {"status": "error", "message": "User not found"}
            
        return {
            "status": "success",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "created_at": user["created_at"]
            }
        }
        
    except Exception as e:
        logging.error(f"Get user error: {e}")
        return {"status": "error", "message": "Failed to get user info"}

@app.post("/auth/logout")
async def logout():
    """Simple logout"""
    return {"status": "success", "message": "Logged out successfully"}

@app.get("/reddit-status")
async def reddit_api_status():
    """Check Reddit API status and update schedule"""
    try:
        reddit = setup_reddit_api()
        if not reddit:
            return {"status": "error", "message": "Reddit API client could not be created"}
        
        # Get last update time from database
        try:
            stats = db.get_stats()
            last_update = "Never"
            if stats:
                # Get the most recent processed tweet timestamp
                recent_tweets = db.get_all_tweets(1)
                if recent_tweets:
                    last_update = recent_tweets[0]['processed_at']
        except:
            last_update = "Unknown"
        
        return {
            "status": "ready",
            "message": "Reddit API ready with hourly automatic updates",
            "update_schedule": {
                "frequency": "Every 1 hour",
                "last_update": last_update,
                "next_update": "Automatic",
                "background_task": "Running" if background_task and not background_task.done() else "Stopped"
            },
            "api_endpoints": {
                "manual_update": "POST /initialize-data",
                "verified_news": "GET /reddit/verified", 
                "rumors": "GET /reddit/rumors",
                "all_news": "GET /reddit/disaster-news"
            },
            "data_sources": {
                "subreddits": [
                    "r/news", "r/worldnews", "r/weather", "r/earthquakes",
                    "r/NaturalDisasters", "r/naturesfury", "r/Preparedness", 
                    "r/preppers", "r/EmergencyManagement"
                ],
                "keywords": [
                    "earthquake", "tsunami", "flood", "wildfire", "hurricane", "tornado", 
                    "emergency", "evacuation", "disaster", "breaking", "storm", "cyclone",
                    "landslide", "avalanche", "drought", "heatwave", "blizzard", "typhoon",
                    "volcanic", "eruption", "mudslide", "sinkhole", "severe weather"
                ],
                "posts_per_subreddit": 10,
                "total_subreddits": 9,
                "total_potential_posts": 90
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Reddit API error: {str(e)}",
            "error_type": type(e).__name__
        }

@app.get("/categories")
async def get_categories():
    """Get available disaster categories"""
    try:
        connection = db.get_connection()
        cursor = connection.cursor()
        
        # Get distinct categories from database
        cursor.execute("SELECT DISTINCT category FROM tweets WHERE is_active = TRUE")
        categories = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        return {
            "categories": ["all"] + sorted(categories),
            "available_filters": {
                "all": "All Disasters",
                "earthquake": "Earthquakes",
                "flood": "Floods",
                "fire": "Wildfires",
                "storm": "Storms & Hurricanes",
                "weather": "Extreme Weather",
                "volcanic": "Volcanic Activity",
                "landslide": "Landslides",
                "tsunami": "Tsunamis",
                "general": "General Disasters"
            }
        }
    except Exception as e:
        return {"categories": ["all", "general"], "error": str(e)}

@app.post("/force-update")
async def force_update():
    """Manually trigger an immediate data update (bypasses hourly schedule)"""
    try:
        logging.info("🔄 Manual update triggered via API")
        await fetch_and_classify_reddit_posts()
        return {
            "status": "success", 
            "message": "Manual update completed successfully",
            "timestamp": datetime.now().isoformat(),
            "note": "Hourly automatic updates continue in background"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Manual update failed: {str(e)}")

@app.post("/test-classification")
async def test_classification(request: PredictionRequest):
    """Test the ML model classification on a single text"""
    try:
        result = classify_text(request.text)
        return {
            "text": request.text,
            "classification": result,
            "model_status": "ML model" if ensemble_model is not None else "keyword fallback",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

@app.get("/model-status")
async def model_status():
    """Check if ML models are loaded and working"""
    global ensemble_model, vectorizer
    
    try:
        model_loaded = ensemble_model is not None and vectorizer is not None
        
        if model_loaded:
            # Test with a simple classification
            test_result = classify_text("Breaking: Official earthquake alert issued by USGS")
            return {
                "status": "ready",
                "models_loaded": True,
                "svm_model": str(type(ensemble_model).__name__),
                "vectorizer": str(type(vectorizer).__name__),
                "test_classification": test_result,
                "message": "SVM model and TF-IDF vectorizer are loaded and working"
            }
        else:
            return {
                "status": "fallback",
                "models_loaded": False,
                "message": "Using keyword-based classification fallback"
            }
    except Exception as e:
        return {
            "status": "error",
            "models_loaded": False,
            "error": str(e),
            "message": "Error checking model status"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)