import requests
import os
from dotenv import load_dotenv

load_dotenv()
user_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')

url = f"https://graph.facebook.com/v19.0/me/accounts?access_token={user_token}"
response = requests.get(url).json()

print("=== YOUR FACEBOOK PAGES ===")
if 'data' in response:
    for page in response['data']:
        print(f"Page Name: {page.get('name')}")
        print(f"Page ID: {page.get('id')}")
        print(f"PERMANENT PAGE TOKEN:\n{page.get('access_token')}\n")
        print("-" * 40)
else:
    print("Error fetching pages. Is the token valid?")
    print(response)
