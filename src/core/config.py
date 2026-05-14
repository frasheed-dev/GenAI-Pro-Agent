import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_ORG_ID = os.getenv("LINKEDIN_ORG_ID")  # Optional: For posting to a company page

FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")

# Application Modes
AUTONOMOUS_MODE = os.getenv("AUTONOMOUS_MODE", "False").lower() in ("true", "1", "yes")

# Target RSS Feeds
RSS_FEEDS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Anthropic": "https://www.anthropic.com/feed.xml",
    "Google AI": "https://blog.research.google/feeds/posts/default?alt=rss",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
    "The Verge AI": "https://www.theverge.com/rss/artificial-intelligence/index.xml",
    "Wired AI": "https://www.wired.com/feed/category/ai/latest/rss",
    "AI News": "https://www.artificialintelligence-news.com/feed/",
    "MIT Tech Review AI": "https://www.technologyreview.com/topic/artificial-intelligence/feed/"
}
