import os, time, json, glob, re, urllib.request, urllib.parse, sys
from datetime import datetime
from threading import Thread

CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"
_last_conf_time = 0
_cached_config = {}

# --- 预编译正则 (保持原逻辑不变) ---
RE_LINE_TYPE = re.compile(r'end of.*transmission', re.IGNORECASE)
RE_CALL = re.compile(r'from\s+([A-Z0-9/]+)')
RE_DUR = re.compile(r'(\d+\.?\d*)\s+seconds')
RE_TARGET = re.compile(r'to\s+(TG\s*\d+|PC\s*\d+|\d+)')
RE_TIME = re.compile(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}')

def get_config():
    global _last_conf_time, _cached_config
    try:
        mtime = os.path.getmtime(CONFIG_FILE)
        if mtime > _last_conf_time:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                _cached_config = json.load(f)
            _last_conf_time = mtime
    except: pass
    return _cached_config

def async_post(url, data=None, is_json=False):
    def task():
        try:
            req = urllib.request.Request(url, data=data, method='POST') if data else urllib.request.Request(url)
            if is_json: req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=5) as r: pass 
        except: pass
    Thread(target=task, daemon=True).start()

def send_payload(config, type_label, body_text):
    msg_header = "━━━━━━━━━━━━━━━\n"
    if config.get('push_wx_enabled') and config.get('wx_token'):
        wx_body = body_text.replace("\n", "<br>").replace("**", "<b>").replace("**", "</b>")
        d = json.dumps({"token": config['wx_token'], "title": f"{type_label}: {config.get('my_callsign','BA4SMQ')}", 
                        "content": f"<b>{type_label}</b><br>{wx_body}", "template": "html"}).encode()
        async_post("http://www.pushplus.plus/send", data=d, is_json=True)
    
    if config.get('push_tg_enabled') and config.get('tg_token'):
        params = urllib.parse.urlencode({"chat_id": config['tg_chat_id'], 
                                         "text": f"*{type_label}*\n{msg_header}{body_text}", "parse_mode": "Markdown"})
        async_post(f"https://api.telegram.org/bot{config['tg_token']}/sendMessage?{params}")

def monitor():
    log_files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
    if not log_files: return
    current_log = max(log_files, key=os.path.getmtime)
    f = open(current_log, "r", encoding="utf-8", errors="ignore")
    f.seek(0, 2)

    while True:
        line = f.readline()
        if not line:
            if os.path.exists(current_log) and os.path.getsize(current_log) < f.tell():
                new_log = max(glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log")), key=os.path.getmtime)
                if new_log != current_log:
                    f.close()
                    current_log = new_log
                    f = open(current_log, "r", encoding="utf-8", errors="ignore")
                    f.seek(0, 2)
            time.sleep(0.5); continue
        
        if RE_LINE_TYPE.search(line):
            conf = get_config()
            try:
                call = RE_CALL.search(line).group(1).upper()
                dur = float(RE_DUR.search(line).group(1))
                if dur < conf.get('min_duration', 1.0) or call == conf.get('my_callsign'): continue
                
                is_data = "data" in line.lower()
                is_cn = conf.get('ui_lang', 'cn') == 'cn'
                type_label = ("💾 数据通联" if is_data else "🎙️ 语音通联") if is_cn else ("💾 Data" if is_data else "🎙️ Voice")
                labels = ["呼号", "群组", "日期", "时间", "时隙", "时长"] if is_cn else ["Callsign", "Group", "Date", "Time", "Slot", "Duration"]
                
                t_m = RE_TIME.search(line)
                dt = t_m.group().split() if t_m else [datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S")]
                
                body = (f"👤 **{labels[0]}**: {call}\n👥 **{labels[1]}**: {RE_TARGET.search(line).group(1) if RE_TARGET.search(line) else 'Unknown'}\n"
                        f"📅 **{labels[2]}**: {dt[0]}\n⏰ **{labels[3]}**: {dt[1]}\n"
                        f"📡 **{labels[4]}**: {'Slot 1' if 'Slot 1' in line else 'Slot 2'}\n⏳ **{labels[5]}**: {dur}{'秒' if is_cn else 's'}")
                send_payload(conf, type_label, body)
            except: pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        c = get_config()
        send_payload(c, "🔔 测试推送", f"呼号: {c.get('my_callsign','BA4SMQ')}\n测试成功！")
    else: monitor()
