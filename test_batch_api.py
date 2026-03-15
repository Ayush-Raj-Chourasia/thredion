import httpx
import json
import asyncio
from datetime import datetime, timedelta
import os
import sys

# Add current dir to path to import local modules (for token generation)
sys.path.insert(0, os.path.abspath("c:/Users/iters/Downloads/thredion/thredion-engine"))
import jwt

JWT_SECRET = "thredion-prod-secret-2024"
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

URLS = [
    "https://www.youtube.com/shorts/Edl-l88L-C4",
    "https://www.youtube.com/shorts/rJhJ9xlRyTA",
    "https://www.youtube.com/shorts/2akQMc37or4",
    "https://www.youtube.com/shorts/gX-72MXld8s",
    "https://m.youtube.com/shorts/vNz4yzVtVYY",
    "https://www.instagram.com/reel/DMaFnTWog_E/",
    "https://www.instagram.com/reel/DU5j-QdDPi8/",
    "https://www.instagram.com/reel/DTh5eqGCa5A/",
    "https://www.instagram.com/reel/DVBUTbUj9--/",
    "https://www.instagram.com/reel/DOWcWNnk891/"
]

STAGING_URL = "https://thredion-api-staging.azurewebsites.net/api/process-batch"
DOCS_URL = "https://thredion-api-staging.azurewebsites.net/docs"

async def run_test():
    print(f"Generating test token...")
    token = create_access_token({"sub": "+1234567890"})
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "urls": URLS
    }
    
    print(f"Sending batch request with {len(URLS)} URLs to staging...")
    print("This may take 1-2 minutes due to rate limits and external APIs...")
    
    async with httpx.AsyncClient(timeout=180.0, follow_redirects=True) as client:
        try:
            start_time = datetime.now()
            response = await client.post(STAGING_URL, json=payload, headers=headers)
            end_time = datetime.now()
            
            print(f"Status Code: {response.status_code}")
            print(f"Time Taken: {(end_time - start_time).total_seconds():.1f} seconds")
            print(f"Server response logic:")
            print(response.text[:2000])
                
        except Exception as e:
            print(f"Error during request: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())

