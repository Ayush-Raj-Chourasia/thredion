import httpx
import os

def run():
    token = os.popen('az account get-access-token --query accessToken -o tsv').read().strip()
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    url = "https://thredion-api-staging.scm.azurewebsites.net/api/command"
    payload = {
        "command": "sqlite3 /home/data/thredion.db \"INSERT OR IGNORE INTO users (phone, name, is_active) VALUES ('+918707701003', 'Ayush', 1);\"",
        "dir": "/home/site/wwwroot"
    }
    
    print("Executing command via Kudu API for +918707701003...")
    r = httpx.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")

if __name__ == "__main__":
    run()
