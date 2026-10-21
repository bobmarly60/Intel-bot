# Python 3.10+, GitHub Actions — ScriptBlox → Discord
import os
import time
from datetime import datetime, timezone
import requests

# --- SCRIPTBLOX WEBHOOK ---
SCRIPTBLOX_WEBHOOK = "https://discord.com/api/webhooks/1562447233448808678/UStaM23-ly7p_v6kfZ8VaE2PYxSj6CTLGLNvswsGvCkS74kGBmtJNlxGTbBjKfNlFsHa"

SCRIPTBLOX_API = "https://scriptblox.com/api/script/fetch"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

SB_SEEN = "sb_seen.txt"

def load_seen(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_seen(path, seen):
    with open(path, "w") as f:
        f.write("\n".join(sorted(seen)) + ("\n" if seen else ""))

def send_discord(webhook_url, title, description, url, color, footer):
    payload = {"embeds": [{
        "title": title[:256], "url": url,
        "description": description[:2048],
        "color": color, "footer": {"text": footer},
    }]}
    try:
        r = requests.post(webhook_url, json=payload, headers=HEADERS, timeout=15)
        print("[hook]", r.status_code, "::", title[:60])
        time.sleep(2)
    except Exception as e:
        print("[hook] error:", e)

def check_scriptblox():
    seen = load_seen(SB_SEEN)
    baseline = not seen
    
    # Fetch 3 pages (60 scripts) from the DEFAULT front-page feed
    # This ensures newly approved scripts are caught even if originally posted days ago
    for page in range(1, 4):
        try:
            url = SCRIPTBLOX_API + "?page=" + str(page) + "&max=20"
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200: break
                
            scripts = r.json().get("result", {}).get("scripts", [])
            if not scripts: break
                
            for s in scripts:
                sid = s.get("_id") or s.get("id")
                if not sid or sid in seen: continue
                
                if baseline:
                    seen.add(sid)
                    continue
                
                title = s.get("title", "Unknown Script")
                game = (s.get("game") or {}).get("name", "Unknown")
                slug = s.get("slug", "")
                
                if slug:
                    link = "https://scriptblox.com/script/" + slug
                else:
                    link = "https://scriptblox.com/script/" + sid
                    
                desc = "**Game:** " + game + "\n**Views:** " + str(s.get('views',0)) + "\n**Key:** `" + str(s.get('key',False)) + "`"
                send_discord(SCRIPTBLOX_WEBHOOK, title, desc, link, 0x3498DB, "ScriptBlox")
                
                seen.add(sid)
                
        except Exception as e:
            print("[sb] error on page", page, ":", e)
            break
            
    if baseline:
        print("[sb] baseline:", len(seen), "cached")
    save_seen(SB_SEEN, seen)

if __name__ == "__main__":
    print("Starting 1-minute loop. Will run for ~5 hours 50 minutes...")
    start_time = time.time()
    while time.time() - start_time < 21000:
        print("Checking ScriptBlox...")
        check_scriptblox()
        print("Sleeping for 60 seconds...")
        time.sleep(60)
