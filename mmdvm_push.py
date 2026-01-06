import os, time, json, glob, re, urllib.request, urllib.parse, sys
from datetime import datetime, timezone, timedelta
from threading import Thread

CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"

# 1. 修复重复推送：定义全局缓存
LAST_MSG = {"call": "", "ts": 0}

# 2. 修复正则匹配：增强对私聊呼号和特殊符号的兼容
RE_VOICE = re.compile(r'end of (?:voice )?transmission', re.IGNORECASE)
RE_DATA = re.compile(r'end of data transmission', re.IGNORECASE)
RE_CALL = re.compile(r'from\s+([A-Z0-9/\-]+)')
RE_DUR = re.compile(r'(\d+\.?\d*)\s+seconds')
# 允许 target 包含字母（呼号）
RE_TARGET = re.compile(r'to\s+([A-Z0-9/\-\s]+?)(?:,|$)', re.IGNORECASE)
RE_TIME = re.compile(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}')

def async_post(url, data=None, is_json=False):
    def task():
        try:
            req = urllib.request.Request(url, data=data, method='POST') if data else urllib.request.Request(url)
            if is_json: req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=3) as r:
                if "--test" in sys.argv: print("发送成功 (Success)")
        except Exception as e:
            if "--test" in sys.argv: print(f"发送失败 (Error): {str(e)}")
    
    if "--test" in sys.argv: task()
    else: Thread(target=task, daemon=True).start()

def send_payload(config, type_label, body_text):
    msg_header = "━━━━━━━━━━━━━━━\n"
    if config.get('push_wx_enabled') and config.get('wx_token'):
        wx_body = body_text.replace("\n", "<br>").replace("**", "<b>").replace("**", "</b>")
        d = json.dumps({"token": config['wx_token'], "title": f"{type_label}", 
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
    
    # 记录当前监听的文件日期，用于跨天判断
    file_date = os.path.basename(current_log).split('-')[1:4] # 提取 YYYY-MM-DD
    
    with open(current_log, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2)
        while True:
            # 3. 修复跨天失效：检查日期是否变更
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            if today_str not in current_log:
                # 如果系统日期已变，但还在读旧文件，立即跳出重找新文件
                return 

            line = f.readline()
            if not line:
                if os.path.getsize(current_log) < f.tell(): return
                time.sleep(0.5); continue
            
            is_v = RE_VOICE.search(line)
            is_d = RE_DATA.search(line)
            
            if is_v or is_d:
                try:
                    with open(CONFIG_FILE, 'r') as cf: conf = json.load(cf)
                    
                    call_m = RE_CALL.search(line)
                    if not call_m: continue
                    call = call_m.group(1).upper()
                    
                    # 4. 修复重复推送：3秒防抖逻辑
                    curr_ts = time.time()
                    if call == LAST_MSG["call"] and (curr_ts - LAST_MSG["ts"]) < 3:
                        continue
                    
                    dur_m = RE_DUR.search(line)
                    dur = float(dur_m.group(1)) if dur_m else 0.0
                    
                    if is_v and (dur < conf.get('min_duration', 1.0) or call == conf.get('my_callsign')): continue
                    if is_d and call == conf.get('my_callsign'): continue
                    
                    # 更新防抖缓存
                    LAST_MSG["call"] = call
                    LAST_MSG["ts"] = curr_ts
                    
                    t_m = RE_TIME.search(line)
                    if t_m:
                        utc_time = datetime.strptime(t_m.group(), "%Y-%m-%d %H:%M:%S")
                        local_time = utc_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
                        date_str = local_time.strftime("%Y-%m-%d")
                        time_str = local_time.strftime("%H:%M:%S")
                    else:
                        date_str = now.strftime("%Y-%m-%d")
                        time_str = now.strftime("%H:%M:%S")
                    
                    is_cn = conf.get('ui_lang', 'cn') == 'cn'
                    type_label = ("🎙️ 语音通联" if is_v else "💾 数据传输") if is_cn else ("🎙️ Voice" if is_v else "💾 Data")
                    
                    target_m = RE_TARGET.search(line)
                    target = target_m.group(1).strip() if target_m else 'Unknown'
                    slot = 'Slot 1' if 'Slot 1' in line else 'Slot 2'
                    
                    body = (f"👤 **呼号**: {call}\n"
                            f"👥 **群组**: {target}\n"
                            f"📅 **日期**: {date_str}\n"
                            f"⏰ **时间**: {time_str}\n"
                            f"📡 **时隙**: {slot}\n"
                            f"⏳ **时长**: {dur}秒")
                    send_payload(conf, type_label, body)
                except: pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        try:
            with open(CONFIG_FILE, 'r') as cf: c = json.load(cf)
            n = datetime.now()
            body = (f"👤 **呼号**: {c.get('my_callsign','BA4SMQ')}\n"
                    f"👥 **群组**: TG 460\n"
                    f"📅 **日期**: {n.strftime('%Y-%m-%d')}\n"
                    f"⏰ **时间**: {n.strftime('%H:%M:%S')}\n"
                    f"📡 **时隙**: Slot 2\n"
                    f"⏳ **时长**: 0.0秒")
            send_payload(c, "🔔 测试推送", body)
        except: print("错误: 配置文件读取失败")
    else:
        # 外部大循环，配合内部 return 实现跨天重新定位日志
        while True:
            try: monitor()
            except: time.sleep(5)
