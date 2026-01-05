import os, time, json, glob, re, urllib.request, urllib.parse
from datetime import datetime, timedelta

CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def is_quiet_time(config):
    qm = config.get('quiet_mode', {})
    if not qm.get('enabled', False): return False
    now = datetime.now().strftime("%H:%M")
    s, e = qm.get('start', '23:00'), qm.get('end', '07:00')
    return (now >= s or now <= e) if s > e else (s <= now <= e)

def send_msg(text, config, is_focus=False):
    # Telegram
    if config.get('push_tg_enabled'):
        params = urllib.parse.urlencode({"chat_id": config.get('tg_chat_id'), "text": text, "parse_mode": "Markdown"})
        try: urllib.request.urlopen(f"https://api.telegram.org/bot{config.get('tg_token')}/sendMessage?{params}", timeout=5)
        except: pass
    # WeChat
    if config.get('push_wx_enabled'):
        title = "🌟 Focus Call" if is_focus else "🎙️ MMDVM Activity"
        data = json.dumps({"token":config.get('wx_token'), "title":title, "content":text.replace("\n","<br>"), "template":"html"}).encode('utf-8')
        try:
            req = urllib.request.Request("http://www.pushplus.plus/send", data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
            urllib.request.urlopen(req, timeout=5)
        except: pass

def get_latest_log():
    files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
    return max(files, key=os.path.getmtime) if files else None

def main():
    log_path = get_latest_log()
    if not log_path: return
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2)
        while True:
            config = load_config()
            line = f.readline()
            if not line:
                time.sleep(0.5); continue
            if "end of" in line and "transmission" in line:
                call = re.search(r'from\s+([A-Z0-9/]+)', line).group(1).upper() if "from" in line else "UNKNOWN"
                dur = float(re.search(r'(\d+\.?\d*)\s+seconds', line).group(1)) if "seconds" in line else 0
                
                focus_list = config.get('focus_list', [])
                is_focus = call in focus_list
                
                if focus_list and not is_focus: continue
                if is_quiet_time(config) and not is_focus: continue
                if dur < config.get('min_duration', 3.0): continue
                if call == config.get('my_callsign') or call in config.get('ignore_list', []): continue

                target = re.search(r'to\s+(TG\s*\d+|\d+)', line).group(1) if "to" in line else "Unknown"
                msg = f"*MMDVM Activity*\nCall: {call}\nTarget: {target}\nDuration: {dur}s\nTime: {datetime.now().strftime('%H:%M:%S')}"
                send_msg(msg, config, is_focus)

if __name__ == "__main__":
    main()
