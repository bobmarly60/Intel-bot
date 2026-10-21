# Python 3.10+, GitHub Actions — ScriptBlox + V3rm roblox.19 → Discord
import os
import time
import random
from datetime import datetime, timezone, timedelta
import requests
import feedparser

# --- WEBHOOKS ---
V3RM_WEBHOOK = "https://discord.com/api/webhooks/1562394916653367417/ItV37v1r4LwP1twjlGLM1_hICp9Ju1-eCNNqgVcW7ytl27TqVIyEmTNSZ5mrhtdWlmCl"
SCRIPTBLOX_WEBHOOK = "https://discord.com/api/webhooks/1562395084971057152/aFM9z7Z352KMHPNMfXaC4t-h-h_iuK-6eV08zW5Ttw-vKHqTAxnkqwCwfkL0pO26-AAv"

V3RM_RSS = "https://v3rm.net/forums/roblox.19/index.rss"
SCRIPTBLOX_API = "https://scriptblox.com/api/script/fetch"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5"
}

V3RM_SEEN = "v3rm_seen.txt"
SB_SEEN = "sb_seen.txt"
PROXY_FILE = "working_proxy.txt"
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
        print(f"[hook] {r.status_code} :: {title[:60]}")
        time.sleep(1)
    except Exception as e:
        print(f"[hook] error: {e}")

def fetch_v3rm_rss():
    # 1. Try the saved proxy first
    if os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, "r") as f:
            saved_proxy = f.read().strip()
            if saved_proxy:
                print(f"[v3rm] testing saved proxy: {saved_proxy}")
                try:
                    r = requests.get(V3RM_RSS, headers=HEADERS, proxies={"http": saved_proxy, "https": saved_proxy}, timeout=10)
                    if r.status_code == 200 and b"<?xml" in r.content:
                        print("[v3rm] saved proxy works!")
                        return r.content
                except Exception:
                    pass

    # 2. If saved proxy fails, hunt for a new one
    print("[v3rm] hunting for a new proxy...")
    try:
        # Get a huge list of free public proxies
        res = requests.get("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", timeout=10)
        proxy_list = res.text.splitlines()
        random.shuffle(proxy_list)
        
        for p in proxy_list[:100]: # Try up to 100 proxies
            proxy_url = f"http://{p}"
            try:
                r = requests.get(V3RM_RSS, headers=HEADERS, proxies={"http": proxy_url, "https": proxy_url}, timeout=5)
                if r.status_code == 200 and b"<?xml" in r.content:
                    print(f"[v3rm] FOUND WORKING PROXY: {proxy_url}")
                    with open(PROXY_FILE, "w") as f:
                        f.write(proxy_url)
                    return r.content
            except Exception:
                continue # Try the next one
    except Exception as e:
        print(f"[v3rm] Proxy hunt error: {e}")
    
    return None

def check_v3rm():
    print("[v3rm] checking...")
    seen = load_seen(V3RM_SEEN)
    baseline = not seen
    
    content = fetch_v3rm_rss()
    if not content:
        print("[v3rm] all proxies failed this run. will try again later.")
        return
        
    feed = feedparser.parse(content)
    for e in feed.entries:
        link = e.get("link", "").strip()
        title = e.get("title", "Untitled").strip()
        if not link or link in seen:
            continue
        if baseline:
            seen.add(link); continue
        
        send_discord(V3RM_WEBHOOK, title, f"**Author:** {e.get('author','?')}\n**Posted:** {e.get('published','')}",
                     link, 0xE74C3C, "V3rm · roblox.19")
        seen.add(link)
    if baseline:
        print(f"[v3rm] baseline: {len(seen)} cached, no pings")
    save_seen(V3RM_SEEN, seen)

def check_scriptblox():
    print("[sb] checking...")
    seen = load_seen(SB_SEEN)
    baseline = not seen
    now = datetime.now(timezone.utc)
    
    for page in range(1, 4):
        try:
            url = f"{SCRIPTBLOX_API}?page={page}&max=20&sortBy=createdAt&order=desc"
            r = requests.get(url, headers=HEADERS, timeout=20)
            print(f"[sb] page {page} status: {r.status_code}")
            if r.status_code != 200:
                break
                
            scripts = r.json().get("result", {}).get("scripts", [])
            if not scripts:
                break
                
            for s in scripts:
                sid = s.get("_id") or s.get("id")
                if not sid or sid in seen:
                    continue
                if baseline:
                    seen.add(sid); continue
                
                fresh = True
                raw = s.get("createdAt")
                if raw:
                    try:
                        clean = raw.split(".")[0].rstrip("Z") + "Z"
                        created = datetime.strptime(clean, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        fresh = (now - created) <= FRESH_WINDOW
                    except Exception:
                        pass
                
                if fresh:
                    title = s.get("title", "Unknown Script")
                    game = (s.get("game") or {}).get("name", "Unknown")
                    slug = s.get("slug", "")
                    url = f"https://scriptblox.com/script/{slug}-{sid}" if slug else f"https://scriptblox.com/script/{sid}"
                    
                    send_discord(SCRIPTBLOX_WEBHOOK, title, f"**Game:** {game}\n**Views:** {s.get('views',0)}\n**Key:** `{s.get('key',False)}`",
                                 url, 0x3498DB, "ScriptBlox")
                seen.add(sid)
                
        except Exception as e:
            print(f"[sb] error on page {page}: {e}")
            break
            
    if baseline:
        print(f"[sb] baseline: {len(seen)} cached, no pings")
    save_seen(SB_SEEN, seen)

if __name__ == "__main__":
    check_v3rm()
    check_scriptblox()
