import os, time, json, glob, re, urllib.request, urllib.parse, sys
from datetime import datetime
from threading import Thread

CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"

# 预编译正则：包含语音和数据通联的识别
RE_VOICE = re.compile(r'end of (?:voice )?transmission', re.IGNORECASE)
RE_DATA = re.compile(r'end of data transmission', re.IGNORECASE)
RE_CALL = re.compile(r'from\s+([A-Z0-9/]+)')
RE_DUR = re.compile(r'(\d+\.?\d*)\s+seconds')
RE_TARGET = re.compile(r'to\s+(TG\s*\d+|PC\s*\d+|\d+)')
RE_TIME = re.compile(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}')

def async_post(url, data=None, is_json=False):
    def task():
        try:
            req = urllib.request.Request(url, data=data, method='POST') if data else urllib.request.Request(url)
            if is_json: req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=3) as r: pass
        except: pass
    Thread(target=task, daemon=True).start()

def send_payload(config, type_label, body_text):
    msg_header = "━━━━━━━━━━━━━━━\n"
    # PushPlus (微信)
    if config.get('push_wx_enabled') and config.get('wx_token'):
        wx_body = body_text.replace("\n", "<br>").replace("**", "<b>").replace("**", "</b>")
        d = json.dumps({"token": config['wx_token'], "title": f"{type_label}", 
                        "content": f"<b>{type_label}</b><br>{wx_body}", "template": "html"}).encode()
        async_post("http://www.pushplus.plus/send", data=d, is_json=True)
    
    # Telegram
    if config.get('push_tg_enabled') and config.get('tg_token'):
        params = urllib.parse.urlencode({"chat_id": config['tg_chat_id'], 
                                         "text": f"*{type_label}*\n{msg_header}{body_text}", "parse_mode": "Markdown"})
        async_post(f"https://api.telegram.org/bot{config['tg_token']}/sendMessage?{params}")

def monitor():
    log_files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
    if not log_files: return
    current_log = max(log_files, key=os.path.getmtime)
    
    with open(current_log, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                if os.path.getsize(current_log) < f.tell(): return
                time.sleep(0.5); continue
            
            # 判断是语音还是数据通联
            is_voice = RE_VOICE.search(line)
            is_data = RE_DATA.search(line)
            
            if is_voice or is_data:
                try:
                    with open(CONFIG_FILE, 'r') as cf: conf = json.load(cf)
                    call = RE_CALL.search(line).group(1).upper()
                    
                    # 语音模式下解析时长，数据模式下默认为 0
                    dur_match = RE_DUR.search(line)
                    dur = float(dur_match.group(1)) if dur_match else 0.0
                    
                    # 过滤逻辑
                    if is_voice and (dur < conf.get('min_duration', 1.0) or call == conf.get('my_callsign')): continue
                    if is_data and call == conf.get('my_callsign'): continue
                    
                    is_cn = conf.get('ui_lang', 'cn') == 'cn'
                    if is_voice:
                        type_label = "🎙️ 语音通联" if is_cn else "🎙️ Voice"
                    else:
                        type_label = "📡 数据传输" if is_cn else "📡 Data"
                        
                    t_m = RE_TIME.search(line)
                    dt = t_m.group().split() if t_m else [datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S")]
                    target = RE_TARGET.search(line).group(1) if RE_TARGET.search(line) else 'Unknown'
                    slot = 'Slot 1' if 'Slot 1' in line else 'Slot 2'
                    
                    # 保持 6 行严格样式
                    body = (f"👤 **呼号**: {call}\n👥 **群组**: {target}\n"
                            f"📅 **日期**: {dt[0]}\n⏰ **时间**: {dt[1]}\n"
                            f"📡 **时隙**: {slot}\n⏳ **时长**: {dur}秒")
                    send_payload(conf, type_label, body)
                except: pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        try:
            with open(CONFIG_FILE, 'r') as cf: c = json.load(cf)
            send_payload(c, "🔔 测试推送", f"呼号: {c.get('my_callsign')}\n这是一条来自 Pi-Star 的测试消息。")
            time.sleep(2) 
        except: pass
    else:
        while True:
            try: monitor()
            except: time.sleep(5)
