#!/usr/bin/env python3
"""
Test Thredion Frontend Deployments on Vercel
Tests all three branch deployments: production, extension, staging
"""

import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
import time

# Deployment URLs
DEPLOYMENTS = {
    "production": "https://thredion.vercel.app/",
    "extension": "https://thredion-git-extension-sup-9343dc-ayush-raj-chourasias-projects.vercel.app/",
    "staging": "https://thredion-git-staging-ayush-raj-chourasias-projects.vercel.app/",
}

TIMEOUT = 10

def test_deployment(name, url):
    """Test a single deployment"""
    print(f"\n{'='*80}")
    print(f"Testing: {name.upper()}")
    print(f"URL: {url}")
    print(f"{'='*80}")
    
    result = {
        "name": name,
        "url": url,
        "status_code": None,
        "response_time": 0,
        "title": None,
        "framework": None,
        "errors": [],
        "features_detected": [],
        "is_deployed": False,
    }
    
    try:
        start = time.time()
        print(f"→ Sending GET request...")
        response = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
        elapsed = time.time() - start
        
        result["response_time"] = elapsed
        result["status_code"] = response.status_code
        
        print(f"✓ Status Code: {response.status_code}")
        print(f"✓ Response Time: {elapsed:.2f}s")
        
        # Check if deployed
        if response.status_code == 200:
            result["is_deployed"] = True
            print(f"✓ DEPLOYED AND ACCESSIBLE")
        else:
            result["errors"].append(f"HTTP {response.status_code}")
            print(f"⚠ Status: {response.status_code} (may indicate error page)")
        
        # Parse HTML
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get title
            title_tag = soup.find('title')
            if title_tag:
                result["title"] = title_tag.string
                print(f"✓ Page Title: {result['title']}")
            
            # Check for React
            if 'React' in response.text or 'react' in response.text or '<div id="__next">' in response.text or '<div id="root">' in response.text:
                result["framework"] = "React/NextJS"
                print(f"✓ Framework: React/NextJS")
            
            # Look for key features
            if any(keyword in response.text.lower() for keyword in ['memory', 'cognitive', 'embedding', 'dashboard']):
                result["features_detected"].append("Cognitive Memory Engine")
                print(f"✓ Feature: Cognitive Memory Engine detected")
            
            if 'auth' in response.text.lower() or 'login' in response.text.lower():
                result["features_detected"].append("Authentication")
                print(f"✓ Feature: Authentication detected")
            
            if 'whatsapp' in response.text.lower() or 'twilio' in response.text.lower():
                result["features_detected"].append("WhatsApp Integration")
                print(f"✓ Feature: WhatsApp Integration detected")
            
            if 'instagram' in response.text.lower() or 'youtube' in response.text.lower():
                result["features_detected"].append("Content Extraction")
                print(f"✓ Feature: Content Extraction detected")
            
            # Check for common error patterns
            if 'error' in response.text.lower() and '404' not in response.text.lower():
                result["errors"].append("Error message found in page")
            
            # Get content length
            content_length = len(response.text)
            print(f"✓ Content Length: {content_length} bytes")
            
            # Check for scripts (React bundles)
            scripts = soup.find_all('script')
            print(f"✓ Scripts loaded: {len(scripts)}")
            
            # Check for CSS
            stylesheets = soup.find_all('link', rel='stylesheet')
            print(f"✓ Stylesheets loaded: {len(stylesheets)}")
            
        except Exception as e:
            result["errors"].append(f"Parse error: {str(e)}")
            print(f"⚠ Could not parse HTML: {e}")
        
        # Check for essential endpoints
        print(f"\n→ Checking essential endpoints...")
        
        essential_endpoints = [
            "/api/health",
            "/docs",
            "/health",
        ]
        
        # These are backend endpoints, but let's check root endpoints
        root_endpoints = [
            "/",
            "/docs",
            "/api",
        ]
        
        for endpoint in root_endpoints:
            try:
                ep_url = url.rstrip('/') + endpoint
                ep_response = requests.head(ep_url, timeout=5, allow_redirects=True)
                if ep_response.status_code == 200:
                    result["features_detected"].append(f"Endpoint {endpoint}")
                    print(f"  ✓ {endpoint}: {ep_response.status_code}")
            except:
                pass
        
    except requests.exceptions.Timeout:
        result["errors"].append("Request timeout")
        print(f"✗ TIMEOUT: Server not responding within {TIMEOUT}s")
        print(f"  May indicate: Site offline, network issues, or slow deployment")
    
    except requests.exceptions.ConnectionError as e:
        result["errors"].append(f"Connection error: {str(e)}")
        print(f"✗ CONNECTION ERROR: {e}")
        print(f"  May indicate: Site offline, DNS issue, or deployment failed")
    
    except requests.exceptions.RequestException as e:
        result["errors"].append(f"Request error: {str(e)}")
        print(f"✗ REQUEST ERROR: {e}")
    
    except Exception as e:
        result["errors"].append(f"Unexpected error: {str(e)}")
        print(f"✗ UNEXPECTED ERROR: {e}")
    
    return result


def compare_deployments(results):
    """Compare all three deployments"""
    print(f"\n{'='*80}")
    print("COMPARISON SUMMARY")
    print(f"{'='*80}")
    
    table = """
    Deployment    | Status | Response Time | Framework        | Features
    --------------|--------|---------------|------------------|-------------------
    """
    
    for result in results:
        status = "✓ Live" if result["is_deployed"] else "✗ Down"
        time_str = f"{result['response_time']:.2f}s" if result["response_time"] else "—"
        framework = result["framework"] or "Unknown"
        features = len(result["features_detected"])
        
        print(f"    {result['name']:12} | {status:6} | {time_str:13} | {framework:16} | {features} features")
    
    print()


def main():
    print("")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "THREDION VERCEL FRONTEND DEPLOYMENTS TEST" + " " * 22 + "║")
    print("╚" + "=" * 78 + "╝")
    print(f"Start Time: {datetime.now().isoformat()}")
    print(f"Timeout: {TIMEOUT}s per request")
    print("")
    
    results = []
    
    # Test each deployment
    for name, url in DEPLOYMENTS.items():
        result = test_deployment(name, url)
        results.append(result)
        time.sleep(0.5)  # Brief pause between requests
    
    # Compare results
    compare_deployments(results)
    
    # Detailed report
    print(f"{'='*80}")
    print("DETAILED RESULTS")
    print(f"{'='*80}\n")
    
    for result in results:
        status = "✅ LIVE" if result["is_deployed"] else "❌ OFFLINE"
        print(f"Branch: {result['name'].upper()}")
        print(f"  Status: {status}")
        print(f"  URL: {result['url']}")
        print(f"  Response Time: {result['response_time']:.2f}s" if result["response_time"] else "  Response Time: —")
        print(f"  Status Code: {result['status_code']}" if result["status_code"] else "  Status Code: —")
        print(f"  Title: {result['title']}" if result["title"] else "  Title: —")
        print(f"  Framework: {result['framework']}" if result["framework"] else "  Framework: Unknown")
        
        if result["features_detected"]:
            print(f"  Features Detected:")
            for feature in result["features_detected"]:
                print(f"    • {feature}")
        
        if result["errors"]:
            print(f"  Errors:")
            for error in result["errors"]:
                print(f"    ⚠ {error}")
        
        print()
    
    # Summary
    print(f"{'='*80}")
    print("SUMMARY AND RECOMMENDATIONS")
    print(f"{'='*80}\n")
    
    live_count = sum(1 for r in results if r["is_deployed"])
    
    print(f"Deployments Live: {live_count}/3")
    
    if live_count == 3:
        print("✅ ALL THREE DEPLOYMENTS ARE LIVE AND WORKING!")
        print("\nRecommendations:")
        print("  • Production (thredion.vercel.app): Main user-facing site")
        print("  • Staging: Test new features before production")
        print("  • Extension: Test new branch features (Supabase + Railway integration)")
    
    elif live_count > 0:
        print(f"✅ {live_count} deployment(s) live, {3-live_count} offline")
        dead = [r for r in results if not r["is_deployed"]]
        print("\nOffline deployments:")
        for r in dead:
            print(f"  • {r['name']}: {r['errors'][0] if r['errors'] else 'Unknown reason'}")
    
    else:
        print("❌ NO DEPLOYMENTS RESPONDING - Check network or Vercel status")
    
    # Check if production is production-ready
    prod = [r for r in results if r['name'] == 'production'][0]
    if prod["is_deployed"] and "React" in (prod.get("framework") or ""):
        print("\n✅ PRODUCTION READY: Main site is deployed and accessible")
    
    print(f"\nEnd Time: {datetime.now().isoformat()}\n")
    
    return 0 if live_count > 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
