import os, time, json, glob, re, urllib.request, urllib.parse
from datetime import datetime

# 配置路径
CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"

def load_config():
    """安全加载 JSON 配置，防止格式损坏导致脚本崩溃"""
    default_conf = {
        "my_callsign": "N0CALL",
        "min_duration": 3.0,
        "quiet_mode": {"enabled": False, "start": "23:00", "end": "07:00"},
        "push_tg_enabled": False, "tg_token": "", "tg_chat_id": "",
        "push_wx_enabled": False, "wx_token": "",
        "ignore_list": [], "focus_list": []
    }
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 合并默认配置，确保缺失字段时不会报错
                default_conf.update(data)
                return default_conf
    except Exception as e:
        print(f"⚠️ [Config Error] JSON format is broken: {e}")
    return default_conf

def is_quiet_time(config):
    """判断当前时间是否处于静音时段"""
    qm = config.get('quiet_mode', {})
    if not qm.get('enabled', False): return False
    now = datetime.now().strftime("%H:%M")
    s, e = qm.get('start', '23:00'), qm.get('end', '07:00')
    return (now >= s or now <= e) if s > e else (s <= now <= e)

def send_msg(text, config, is_focus=False):
    """发送消息至 TG 和 微信"""
    # Telegram 推送逻辑
    if config.get('push_tg_enabled') and config.get('tg_token'):
        params = urllib.parse.urlencode({
            "chat_id": config.get('tg_chat_id'), 
            "text": text, 
            "parse_mode": "Markdown"
        })
        try:
            urllib.request.urlopen(f"https://api.telegram.org/bot{config.get('tg_token')}/sendMessage?{params}", timeout=10)
            print(f"✅ TG Sent: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"❌ TG Error: {e}")

    # 微信 (PushPlus) 推送逻辑
    if config.get('push_wx_enabled') and config.get('wx_token'):
        title = "🌟 Focus Call" if is_focus else "🎙️ MMDVM Activity"
        # 简单校验 Token 格式，防止填入 shell 命令
        if len(config.get('wx_token')) < 10:
            print("❌ WX Error: Invalid Token format.")
            return

        data = json.dumps({
            "token": config.get('wx_token'), 
            "title": title, 
            "content": text.replace("\n", "<br>"), 
            "template": "html"
        }).encode('utf-8')
        try:
            req = urllib.request.Request("http://www.pushplus.plus/send", data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
            urllib.request.urlopen(req, timeout=10)
            print(f"✅ WX Sent: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"❌ WX Error: {e}")

def get_latest_log():
    """获取最新的 MMDVM 日志文件"""
    files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
    return max(files, key=os.path.getmtime) if files else None

def monitor_log():
    print("🚀 MMDVM Push Service v2.1 Started (Timezone Adaptive).")
    current_log_path = get_latest_log()
    if not current_log_path:
        print("❌ No MMDVM log files found!")
        return
    
    # 以追加模式打开最新的日志
    with open(current_log_path, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2) # 移动到文件末尾
        while True:
            config = load_config()
            line = f.readline()
            
            if not line:
                # 检查是否切换了日期（产生了新日志）
                new_log = get_latest_log()
                if new_log and new_log != current_log_path:
                    print(f"📅 Log rotated to: {new_log}")
                    current_log_path = new_log
                    f = open(current_log_path, "r", encoding="utf-8", errors="ignore")
                    f.seek(0, 2)
                time.sleep(0.5)
                continue
            
            # 匹配通话结束行
            if "end of" in line and "transmission" in line:
                try:
                    # 解析基础信息
                    call = re.search(r'from\s+([A-Z0-9/]+)', line).group(1).upper()
                    dur = float(re.search(r'(\d+\.?\d*)\s+seconds', line).group(1))
                    target = re.search(r'to\s+(TG\s*\d+|PC\s*\d+|\d+)', line).group(1) if "to" in line else "Unknown"
                    slot = "S1" if "Slot 1" in line else "S2"
                    
                    # 时区自适应解析
                    t_match = re.search(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', line)
                    if t_match:
                        # 将日志时间字符串转为本地显示时间
                        log_ts = time.mktime(time.strptime(t_match.group(), "%Y-%m-%d %H:%M:%S"))
                        display_time = time.strftime("%H:%M:%S", time.localtime(log_ts))
                    else:
                        display_time = datetime.now().strftime("%H:%M:%S")

                    # 逻辑过滤
                    focus_list = config.get('focus_list', [])
                    ignore_list = config.get('ignore_list', [])
                    is_focus = call in focus_list
                    
                    if focus_list and not is_focus: continue
                    if is_quiet_time(config) and not is_focus: continue
                    if dur < config.get('min_duration', 3.0): continue
                    if call == config.get('my_callsign') or call in ignore_list: continue

                    # 格式化消息内容
                    msg = (f"*MMDVM Activity*\n---\n👤 **Call**: {call}\n👥 **Target**: {target}\n"
                           f"⏳ **Dur**: {dur}s  |  📡 **Slot**: {slot}\n⏰ **Time**: {display_time}")

                    print(f"🔔 Detected: {call} to {target} ({dur}s)")
                    send_msg(msg, config, is_focus)
                    
                except Exception as e:
                    print(f"⚠️ Parsing Error: {e}")

if __name__ == "__main__":
    try:
        monitor_log()
    except KeyboardInterrupt:
        print("\n👋 Service stopped by user.")
