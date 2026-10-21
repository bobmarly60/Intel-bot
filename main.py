# Python 3.10+, GitHub Actions — ScriptBlox → Discord
import os
import time
import requests

# --- SCRIPTBLOX WEBHOOK ---
SCRIPTBLOX_WEBHOOK = "https://discord.com/api/webhooks/1562447233448808678/UStaM23-ly7p_v6kfZ8VaE2PYxSj6CTLGLNvswsGvCkS74kGBmtJNlxGTbBjKfNlFsHa"

SCRIPTBLOX_API = "https://scriptblox.com/api/script/fetch"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

# Fresh memory file so it doesn't spam the old stuff
SB_SEEN = "sb_seen_v7.txt"

def load_seen(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_seen(path, seen):
    with open(path, "w") as f:
        f.write("\n".join(sorted(seen)) + ("\n" if seen else ""))

def send_discord(title, description, url):
    payload = {"embeds": [{
        "title": title[:256], "url": url,
        "description": description[:2048],
        "color": 0x3498DB, "footer": {"text": "ScriptBlox"}
    }]}
    try:
        r = requests.post(SCRIPTBLOX_WEBHOOK, json=payload, headers=HEADERS, timeout=15)
        print("[hook]", r.status_code, "::", title[:60])
        time.sleep(2)
    except Exception as e:
        print("[hook] error:", e)

def check_scriptblox():
    seen = load_seen(SB_SEEN)
    baseline = not seen
    
    # Sort by updatedAt to catch week-old approvals. Fetch 100 scripts to be safe.
    try:
        url = SCRIPTBLOX_API + "?page=1&max=100&sortBy=updatedAt&order=desc"
        r = requests.get(url, headers=HEADERS, timeout=15)
        
        if r.status_code != 200:
            return
            
        scripts = r.json().get("result", {}).get("scripts", [])
        
        for s in scripts:
            sid = s.get("_id") or s.get("id")
            if not sid or sid in seen: 
                continue
            
            if baseline:
                seen.add(sid)
                continue
            
            # MAGIC FILTER: Ignore anything with over 400 views
            views = s.get("views", 0)
            if views > 400:
                continue
                
            title = s.get("title", "Unknown Script")
            game = (s.get("game") or {}).get("name", "Unknown")
            slug = s.get("slug", "")
            
            link = "https://scriptblox.com/script/" + slug if slug else "https://scriptblox.com/script/" + sid
            desc = "**Game:** " + game + "\n**Views:** " + str(views) + "\n**Key:** `" + str(s.get('key',False)) + "`"
            
            send_discord(title, desc, link)
            seen.add(sid)
            
    except Exception as e:
        print("[sb] error:", e)
        
    if baseline:
        print("[sb] baseline cached:", len(seen))
    save_seen(SB_SEEN, seen)

if __name__ == "__main__":
    print("Starting 1-minute loop. Catching week-old approvals.")
    start_time = time.time()
    while time.time() - start_time < 21000:
        print("Checking ScriptBlox for new approvals...")
        check_scriptblox()
        print("Sleeping for 60 seconds...")
        time.sleep(60)
