import requests
from core.config import LINKEDIN_ACCESS_TOKEN, LINKEDIN_ORG_ID

def get_linkedin_user_urn():
    """
    Fetches the authenticated user's URN (required to post).
    Uses the OpenID Connect endpoint which is the standard mechanism.
    """
    url = "https://api.linkedin.com/v2/userinfo"
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return f"urn:li:person:{data.get('sub')}" # 'sub' is the unique identifier
    else:
        print(f"Error fetching User URN: {response.text}")
        return None

def post_to_linkedin(text_content):
    """
    Publishes a text post to either a Company Page or Personal feed.
    """
    if not LINKEDIN_ACCESS_TOKEN or LINKEDIN_ACCESS_TOKEN == "YOUR_LINKEDIN_TOKEN_HERE":
        print("LINKEDIN_ACCESS_TOKEN is not correctly set. Please generate it from the Developer Portal.")
        return False
        
    author_urn = None
    if LINKEDIN_ORG_ID:
        author_urn = f"urn:li:organization:{LINKEDIN_ORG_ID}"
        print(f"Targeting Company Page: {author_urn}")
    else:
        author_urn = get_linkedin_user_urn()
        print(f"Targeting Personal Profile: {author_urn}")

    if not author_urn:
        return False

    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    
    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": text_content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print(f"Successfully posted to LinkedIn! Post ID: {response.headers.get('x-restli-id')}")
        return True
    else:
        print(f"Failed to post. Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
