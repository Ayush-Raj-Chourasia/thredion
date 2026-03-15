import httpx
import jwt
import datetime

def run_test():
    staging_url = "https://thredion-api-staging.azurewebsites.net/api/process-batch"
    secret = "thredion-prod-secret-2024"

    # Use the user's phone number as added in DB
    payload = {
        "sub": "+918707701003",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=60)
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 1 youtube short (previously degraded to caption_only)
    # 1 instagram reel (previously degraded to metadata_only)
    test_urls = [
        "https://www.youtube.com/shorts/Edl-l88L-C4",
        "https://www.instagram.com/reel/DU5j-QdDPi8/"
    ]

    print(f"Testing premium APIs with {len(test_urls)} URLs to conserve credits...")
    try:
        # Increase timeout because paid APIs take a few seconds
        r = httpx.post(staging_url, json={"urls": test_urls}, headers=headers, timeout=120)
        import json
        
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            for res in results:
                url = res.get("url")
                quality = res.get("content_quality", "N/A")
                success = res.get("success", False)
                print(f"URL: {url} -> Quality: {quality} (Success: {success})")
                
                # We want to see if it specifically says 'supadata_api' or 'socialkit_api' for quality if we check DB
                # Actually, our API returns content_quality. Let's see what is returned.
        else:
            print(r.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_test()
