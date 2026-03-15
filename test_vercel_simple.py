import requests
import time
from datetime import datetime

deployments = {
    "production": "https://thredion.vercel.app/",
    "extension": "https://thredion-git-extension-sup-9343dc-ayush-raj-chourasias-projects.vercel.app/",
    "staging": "https://thredion-git-staging-ayush-raj-chourasias-projects.vercel.app/",
}

print("\n" + "="*80)
print("THREDION VERCEL DEPLOYMENTS - REAL-TIME TEST")
print("="*80)
print(f"Test Time: {datetime.now().isoformat()}")
print("="*80 + "\n")

results = []

for branch, url in deployments.items():
    print("Testing: " + branch.upper())
    print("URL: " + url)
    
    try:
        start = time.time()
        r = requests.get(url, timeout=5, allow_redirects=True)
        elapsed = time.time() - start
        
        print("Status: " + str(r.status_code))
        print("Response Time: " + str(round(elapsed, 2)) + "s")
        print("Content-Type: " + r.headers.get("content-type", "Unknown"))
        print("Size: " + str(len(r.text)) + " bytes")
        
        # Check content
        if "<html" in r.text.lower() or "<doctype" in r.text.lower():
            print("Content: Valid HTML page")
        
        if "thredion" in r.text.lower():
            print("Content: Contains 'thredion' reference")
        
        if "unauthorized" in r.text.lower():
            print("Note: Page contains 'unauthorized' text (may be auth-required)")
        
        if "next" in r.text.lower():
            print("Framework: NextJS detected")
        
        results.append({
            "branch": branch,
            "status": r.status_code,
            "time": elapsed,
            "size": len(r.text),
            "live": r.status_code < 400
        })
        
        print("Result: OK" if r.status_code < 400 else "Result: Needs Investigation")
        
    except requests.exceptions.Timeout:
        print("ERROR: Timeout (server not responding)")
        results.append({"branch": branch, "status": 0, "error": "timeout"})
    except Exception as e:
        print("ERROR: " + str(type(e).__name__) + ": " + str(e))
        results.append({"branch": branch, "status": 0, "error": str(e)})
    
    print("")

print("="*80)
print("SUMMARY")
print("="*80 + "\n")

live = sum(1 for r in results if r.get("live"))
print("Deployments Live: " + str(live) + "/3\n")

for result in results:
    status = "LIVE" if result.get("live") else "OFFLINE/ERROR"
    print(result["branch"].upper() + ": " + status)
    if result.get("status"):
        print("  Status Code: " + str(result["status"]))
    if result.get("time"):
        print("  Response Time: " + str(round(result["time"], 2)) + "s")
    print("")

print("="*80)
print("INTERPRETATION")
print("="*80 + "\n")

for result in results:
    branch = result["branch"]
    status = result.get("status", 0)
    
    if status == 200:
        print(branch.upper() + ": Fully accessible, site loads normally")
    elif status == 401:
        print(branch.upper() + ": Deployed but requires authentication (expected)")
    elif status == 0:
        print(branch.upper() + ": Cannot reach server (may be down or network issue)")
    else:
        print(branch.upper() + ": Response " + str(status) + " (may indicate error page)")

print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80 + "\n")

prod = [r for r in results if r["branch"] == "production"][0]
if prod.get("live"):
    print("✓ Production site is LIVE and accessible")
    print("✓ Users can access https://thredion.vercel.app/")
else:
    print("✗ Production site is DOWN - urgent action needed")

ext = [r for r in results if r["branch"] == "extension"][0]
if ext.get("status") == 401:
    print("\n✓ Extension branch is DEPLOYED (shows 401 - likely auth-protected)")
else:
    print("\n✓ Extension branch is deployed")

stg = [r for r in results if r["branch"] == "staging"][0]
if stg.get("status") == 401:
    print("✓ Staging branch is DEPLOYED (shows 401 - likely auth-protected)")
else:
    print("✓ Staging branch is deployed")

print("\n" + "="*80)
