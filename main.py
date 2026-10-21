# Python 3.10+, GitHub Actions — ScriptBlox → Discord
import os
import time
from datetime import datetime, timezone, timedelta
import requests

# --- SCRIPTBLOX WEBHOOK ---
SCRIPTBLOX_WEBHOOK = "https://discord.com/api/webhooks/1562443293395132566/TK090DqpvlA6nLw42hwg_5Bhn2u-wNZys_r9Ig3KIrr1-hcVN0XgTsMPboHiqT2QqK-W"

SCRIPTBLOX_API = "https://scriptblox.com/api/script/fetch"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

SB_SEEN = "sb_seen.txt"
FRESH_WINDOW = timedelta(minutes=15)

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
        time.sleep(1)
    except Exception as e:
        print("[hook] error:", e)

def check_scriptblox():
    print("[sb] checking...")
    seen = load_seen(SB_SEEN)
    baseline = not seen
    now = datetime.now(timezone.utc)
    
    # Check if this was manually triggered via the "Run workflow" button
    is_manual_run = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
    
    for page in range(1, 4):
        try:
            url = SCRIPTBLOX_API + "?page=" + str(page) + "&max=20&sortBy=createdAt&order=desc"
            r = requests.get(url, headers=HEADERS, timeout=20)
            print("[sb] page", page, "status:", r.status_code)
            if r.status_code != 200: break
                
            scripts = r.json().get("result", {}).get("scripts", [])
            if not scripts: break
                
            for s in scripts:
                sid = s.get("_id") or s.get("id")
                if not sid: continue
                
                title = s.get("title", "Unknown Script")
                game = (s.get("game") or {}).get("name", "Unknown")
                slug = s.get("slug", "")
                link = "https://scriptblox.com/script/" + slug + "-" + sid if slug else "https://scriptblox.com/script/" + sid
                desc = "**Game:** " + game + "\n**Views:** " + str(s.get('views',0)) + "\n**Key:** `" + str(s.get('key',False)) + "`"
                
                # FORCE TEST MESSAGE IF MANUALLY RUN
                if is_manual_run:
                    print("[TEST MODE] Sending test ping to Discord...")
                    send_discord(SCRIPTBLOX_WEBHOOK, "TEST: " + title, desc, link, 0xFF0000, "ScriptBlox TEST")
                    return # Stop running after sending the test
                
                # NORMAL SCHEDULE LOGIC
                if sid in seen: continue
                if baseline:
                    seen.add(sid)
                    continue
                
                fresh = True
                raw = s.get("createdAt")
                if raw:
                    try:
                        clean = raw.split(".")[0].rstrip("Z") + "Z"
                        created = datetime.strptime(clean, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        fresh = (now - created) <= FRESH_WINDOW
                    except Exception: pass
                
                if fresh:
                    send_discord(SCRIPTBLOX_WEBHOOK, title, desc, link, 0x3498DB, "ScriptBlox")
                seen.add(sid)
                
        except Exception as e:
            print("[sb] error on page", page, ":", e)
            break
            
    if baseline and not is_manual_run:
        print("[sb] baseline:", len(seen), "cached")
        save_seen(SB_SEEN, seen)

if __name__ == "__main__":
    check_scriptblox()
