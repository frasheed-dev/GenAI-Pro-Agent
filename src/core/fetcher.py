import feedparser
from datetime import datetime, timezone, timedelta
import time
from core.config import RSS_FEEDS
from core.state_manager import add_articles, load_state

def fetch_latest_news(hours_ago=72):
    """
    Fetches news from configured RSS feeds published within the last `hours_ago` hours.
    By default we look back 72 hours to ensure we catch recent news.
    """
    recent_articles = []
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_ago)

    for source_name, url in RSS_FEEDS.items():
        print(f"Fetching from {source_name} ({url})...")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # Parse published date
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed), timezone.utc)
                else:
                    print(f"Skipping article '{entry.title}' due to missing date.")
                    continue

                if published_date > cutoff_time:
                    recent_articles.append({
                        "source": source_name,
                        "title": entry.title,
                        "link": entry.link,
                        "published_date": published_date,
                        "summary": entry.get('summary', 'No summary available.')
                    })
        except Exception as e:
            print(f"Error fetching from {source_name}: {e}")

    # Add all found articles to the State Manager (duplicates are automatically ignored)
    new_count = add_articles(recent_articles)
    print(f"--- Discovered {new_count} brand new articles to track in the database ---")
    
    # Filter out anything that has already been PUBLISHED or IGNORED in the past
    state = load_state()
    pending_articles = [
        art for art in recent_articles 
        if state.get(art["link"], {}).get("status", "PENDING") == "PENDING"
    ]

    # Sort pending articles by date descending
    pending_articles.sort(key=lambda x: x['published_date'], reverse=True)
    return pending_articles

if __name__ == "__main__":
    # Test execution: let's fetch news from the last 7 days to see if it works
    articles = fetch_latest_news(hours_ago=24 * 7) 
    print(f"--- Founds {len(articles)} recent articles in the last 7 days ---")
    for idx, article in enumerate(articles, 1):
        print(f"\n{idx}. [{article['source']}] {article['title']}")
        print(f"   Date: {article['published_date'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"   Link: {article['link']}")
