# FORCED TEST SCRIPT
import requests
import time

# YOUR WEBHOOK
WEBHOOK_URL = "https://discord.com/api/webhooks/1562443293395132566/TK090DqpvlA6nLw42hwg_5Bhn2u-wNZys_r9Ig3KIrr1-hcVN0XgTsMPboHiqT2QqK-W"
SCRIPTBLOX_API = "https://scriptblox.com/api/script/fetch"

print("Fetching latest script for test...")
try:
    # Get the absolute latest script
    r = requests.get(SCRIPTBLOX_API + "?page=1&max=1&sortBy=createdAt&order=desc", timeout=15)
    r.raise_for_status()
    scripts = r.json().get("result", {}).get("scripts", [])
    
    if not scripts:
        print("No scripts found on ScriptBlox API.")
    else:
        s = scripts[0]
        title = s.get("title", "Test Script")
        game = (s.get("game") or {}).get("name", "Test Game")
        sid = s.get("_id") or s.get("id")
        slug = s.get("slug", "")
        link = "https://scriptblox.com/script/" + slug + "-" + sid if slug else "https://scriptblox.com/script/" + sid
        
        print(f"Sending TEST to Discord: {title}")
        
        payload = {
            "embeds": [{
                "title": "TEST: " + title,
                "url": link,
                "description": "**This is a forced test message.**\n**Game:** " + game,
                "color": 16711680
            }]
        }
        
        # Send to Discord
        post = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        print(f"Discord response code: {post.status_code}")
        if post.status_code == 204:
            print("SUCCESS! Check your Discord channel.")
        else:
            print(f"FAILED. Discord says: {post.text}")
            
except Exception as e:
    print(f"Error: {e}")
