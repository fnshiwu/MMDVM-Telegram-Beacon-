import os
import time
import json
import glob
import re
import requests
from datetime import datetime, timedelta

# ================= [路径配置] =================
CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"
MIN_DURATION = 0.5  # 设置较低的阈值以确保捕捉
# =============================================

def load_config():
    """动态读取 JSON 配置文件"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ 配置文件读取异常: {e}")
    return None

def send_tg(text, config):
    if not config or not config.get('push_tg_enabled'): return
    token = config.get('tg_token')
    chat_id = config.get('tg_chat_id')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.get(url, params=params, timeout=10)
    except Exception as e:
        print(f"❌ TG 发送失败: {e}")

def send_wx(title, content, config):
    if not config or not config.get('push_wx_enabled'): return
    token = config.get('wx_token')
    url = 'http://www.pushplus.plus/send'
    data = {"token": token, "title": title, "content": content, "template": "html"}
    try:
        res = requests.post(url, json=data, timeout=10)
        print(f"📡 微信反馈: {res.text}")
    except Exception as e:
        print(f"❌ 微信推送连接失败: {e}")

def get_latest_log():
    """获取最后修改的 MMDVM 日志文件"""
    log_files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
    if not log_files: return None
    return max(log_files, key=os.path.getmtime)

def monitor_log():
    current_log_path = get_latest_log()
    if not current_log_path:
        print("❌ 错误：未找到日志文件")
        return
    
    print(f"🚀 监控已启动: {current_log_path}")
    
    while True:
        try:
            config = load_config()
            if not config:
                time.sleep(5)
                continue

            with open(current_log_path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(0, 2) # 移至末尾开始监听
                while True:
                    # 自动检测跨天日志切换
                    new_log_path = get_latest_log()
                    if new_log_path and new_log_path != current_log_path:
                        current_log_path = new_log_path
                        print(f"📅 切换到新日志: {current_log_path}")
                        break 

                    line = f.readline()
                    if not line:
                        time.sleep(0.4)
                        continue
                    
                    # 识别通联结束标志
                    if "end of" in line and "transmission" in line:
                        # 排除自己的通联
                        my_call = config.get('my_callsign', 'NONE').upper()
                        if my_call in line.upper():
                            continue

                        # 1. 区分 语音 或 数据
                        is_voice = "voice" in line.lower()
                        mode_label = "🎙️ 语音通联" if is_voice else "💾 数据传输"

                        # 2. 提取时长
                        duration_match = re.search(r'(\d+\.?\d*)\s+seconds', line)
                        duration_val = float(duration_match.group(1)) if duration_match else 0.0
                        
                        # 3. 提取呼号 (From)
                        call_match = re.search(r'from\s+([A-Z0-9/]+)', line)
                        remote_call = call_match.group(1) if call_match else "未知"
                        
                        # 黑名单过滤
                        if remote_call in config.get('ignore_list', []):
                            continue

                        # 4. 提取群组/目标 (To)
                        tg_match = re.search(r'to\s+(TG\s*\d+|PC\s*\d+|Reflector\s*\d+|\d+)', line)
                        target_tg = tg_match.group(1) if tg_match else "未知"

                        # 5. 处理时间 (UTC转北京时间)
                        time_match = re.search(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', line)
                        if time_match:
                            utc_time = datetime.strptime(time_match.group(), "%Y-%m-%d %H:%M:%S")
                            bj_now = utc_time + timedelta(hours=8)
                        else:
                            bj_now = datetime.now()

                        date_str = bj_now.strftime("%Y-%m-%d")
                        time_str = bj_now.strftime("%H:%M:%S")

                        # 6. 识别时隙 (Slot)
                        slot = "1" if "Slot 1" in line else "2"

                        # --- 构建消息 ---
                        msg_title = f"{mode_label}: {remote_call}"
                        msg_content = (
                            f"呼号: {remote_call}\n"
                            f"群组: {target_tg}\n"
                            f"日期: {date_str}\n"
                            f"时间: {time_str}\n"
                            f"时隙: Slot {slot}\n"
                            f"时长: {duration_val}s"
                        )

                        # 执行推送
                        send_tg(f"*{msg_title}*\n{msg_content}", config)
                        send_wx(msg_title, msg_content.replace('\n', '<br>'), config)
                        print(f"✅ 已推送: {remote_call} 目标 {target_tg} ({duration_val}s)")

        except Exception as e:
            print(f"⚠️ 运行时异常: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_log()
