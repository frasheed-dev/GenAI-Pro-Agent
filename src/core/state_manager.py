import os
import json
from datetime import datetime, timezone

STATE_FILE = "data/articles_state.json"

def load_state():
    """Load the article state database from disk."""
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_state(state):
    """Save the article state database to disk."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4, ensure_ascii=False)

def add_articles(articles):
    """
    Takes a list of article dictionaries and adds them to the database.
    If the article URL already exists, it is ignored.
    """
    state = load_state()
    added_count = 0
    
    for article in articles:
        link = article["link"]
        if link not in state:
            # Handle datetime objects for JSON serialization
            pub_date = article["published_date"]
            if isinstance(pub_date, datetime):
                pub_date = pub_date.isoformat()
                
            state[link] = {
                "title": article["title"],
                "source": article["source"],
                "published_date": pub_date,
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "status": "PENDING"
            }
            added_count += 1
            
    if added_count > 0:
        save_state(state)
    return added_count

def get_pending_articles():
    """Returns a list of all articles that are waiting to be reviewed/published."""
    state = load_state()
    return [
        {"link": link, **data} 
        for link, data in state.items() 
        if data.get("status") == "PENDING"
    ]

def update_status(link, status):
    """
    Update the status of an article. 
    Valid statuses: 'PENDING', 'PUBLISHED', 'IGNORED'
    """
    state = load_state()
    if link in state:
        state[link]["status"] = status
        state[link]["updated_at"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        return True
    return False

def mark_as_published(link, platform):
    """
    Mark an article as published and record the specific platform and timestamp.
    """
    state = load_state()
    if link in state:
        state[link]["status"] = "PUBLISHED"
        if "publish_history" not in state[link]:
            state[link]["publish_history"] = {}
        state[link]["publish_history"][platform] = datetime.now(timezone.utc).isoformat()
        state[link]["updated_at"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        return True
    return False

def get_article_by_link(link):
    """Fetch metadata for a specific article URL."""
    return load_state().get(link)
