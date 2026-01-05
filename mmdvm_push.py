import os, time, json, glob, re, urllib.request, urllib.parse
from datetime import datetime
from threading import Thread

# --- 配置路径 ---
CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"

# --- 1. 预编译正则表达式 (性能核心) ---
RE_LINE_TYPE = re.compile(r'end of.*transmission')
RE_CALL = re.compile(r'from\s+([A-Z0-9/]+)')
RE_DUR = re.compile(r'(\d+\.?\d*)\s+seconds')
RE_TARGET = re.compile(r'to\s+(TG\s*\d+|PC\s*\d+|\d+)')
RE_TIME = re.compile(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}')

def load_config():
    """安全加载配置"""
    default_conf = {
        "my_callsign": "N0CALL", "min_duration": 3.0,
        "quiet_mode": {"enabled": False, "start": "23:00", "end": "07:00"},
        "push_tg_enabled": False, "tg_token": "", "tg_chat_id": "",
        "push_wx_enabled": False, "wx_token": "",
        "ignore_list": [], "focus_list": []
    }
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                default_conf.update(data)
    except: pass
    return default_conf

def async_post(url, data=None, is_json=False):
    """异步任务：在子线程中处理网络请求，防止阻塞主循环"""
    def task():
        try:
            if is_json:
                req = urllib.request.Request(url, data=data, method='POST')
                req.add_header('Content-Type', 'application/json')
                urllib.request.urlopen(req, timeout=8)
            else:
                urllib.request.urlopen(url, timeout=8)
        except: pass 
    Thread(target=task).start()

def send_msg(text, config, is_focus=False):
    """构建推送任务"""
    # Telegram
    if config.get('push_tg_enabled') and config.get('tg_token'):
        params = urllib.parse.urlencode({"chat_id": config.get('tg_chat_id'), "text": text, "parse_mode": "Markdown"})
        url = f"https://api.telegram.org/bot{config.get('tg_token')}/sendMessage?{params}"
        async_post(url)

    # WeChat (PushPlus)
    if config.get('push_wx_enabled') and config.get('wx_token'):
        token = config.get('wx_token')
        if len(token) > 10: # 简单校验
            title = "🌟 Focus Call" if is_focus else "🎙️ MMDVM Activity"
            post_data = json.dumps({
                "token": token, "title": title, 
                "content": text.replace("\n", "<br>"), "template": "html"
            }).encode('utf-8')
            async_post("http://www.pushplus.plus/send", data=post_data, is_json=True)

def is_quiet_time(config):
    qm = config.get('quiet_mode', {})
    if not qm.get('enabled', False): return False
    now = datetime.now().strftime("%H:%M")
    s, e = qm.get('start', '23:00'), qm.get('end', '07:00')
    return (now >= s or now <= e) if s > e else (s <= now <= e)

def get_latest_log():
    files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
    return max(files, key=os.path.getmtime) if files else None

def monitor():
    print("🚀 MMDVM Push Pro v2.2 (Async & Pre-compiled) Started.")
    current_path = get_latest_log()
    if not current_path: return

    with open(current_path, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                # 检查跨天日志切换
                new_path = get_latest_log()
                if new_path and new_path != current_path:
                    current_path = new_path
                    f = open(current_path, "r", encoding="utf-8", errors="ignore")
                    f.seek(0, 2)
                time.sleep(0.4) # 稍微降低轮询频率，平衡性能
                continue

            # 使用预编译正则快速匹配
            if RE_LINE_TYPE.search(line):
                config = load_config()
                try:
                    call_match = RE_CALL.search(line)
                    dur_match = RE_DUR.search(line)
                    if not call_match or not dur_match: continue
                    
                    call = call_match.group(1).upper()
                    dur = float(dur_match.group(1))
                    
                    # 过滤逻辑
                    focus_list = config.get('focus_list', [])
                    ignore_list = config.get('ignore_list', [])
                    is_focus = call in focus_list
                    
                    if focus_list and not is_focus: continue
                    if is_quiet_time(config) and not is_focus: continue
                    if dur < config.get('min_duration', 3.0): continue
                    if call == config.get('my_callsign') or call in ignore_list: continue

                    # 提取其他信息
                    tg_match = RE_TARGET.search(line)
                    target = tg_match.group(1) if tg_match else "Unknown"
                    slot = "Slot 1" if "Slot 1" in line else "Slot 2"
                    
                    # 时间转换
                    t_match = RE_TIME.search(line)
                    display_time = time.strftime("%H:%M:%S", time.localtime(time.mktime(time.strptime(t_match.group(), "%Y-%m-%d %H:%M:%S")))) if t_match else datetime.now().strftime("%H:%M:%S")

                    # 构建消息
                    msg = (f"*MMDVM Activity*\n---\n👤 **Call**: {call}\n👥 **Target**: {target}\n"
                           f"⏳ **Dur**: {dur}s  |  📡 **{slot}**\n⏰ **Time**: {display_time}")

                    # 发送 (异步)
                    send_msg(msg, config, is_focus)
                    print(f"[{display_time}] Pushed: {call} ({dur}s)")

                except Exception as e:
                    print(f"Parsing error: {e}")

if __name__ == "__main__":
    monitor()
