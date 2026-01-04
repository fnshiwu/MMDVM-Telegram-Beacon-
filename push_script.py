import time
import requests
import os
import glob
import re
import json
from datetime import datetime, timedelta

# ================= [配置区域] =================
CONFIG_PATH = '/etc/mmdvm_push.json'
LOG_DIR = "/var/log/pi-star/"
# =============================================

def load_config():
    """从 Web 端生成的 JSON 加载配置"""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ 读取配置失败: {e}")
    return {}

def send_push(text, config):
    """统一发送入口"""
    # Telegram 推送
    if config.get('push_tg_enabled') and config.get('tg_token'):
        url = f"https://api.telegram.org/bot{config['tg_token']}/sendMessage"
        params = {"chat_id": config['tg_chat_id'], "text": text, "parse_mode": "Markdown"}
        try:
            requests.get(url, params=params, timeout=10)
        except: pass

    # 微信 PushPlus 推送
    if config.get('push_wx_enabled') and config.get('wx_token'):
        url = 'http://www.pushplus.plus/send'
        data = {"token": config['wx_token'], "title": "🎙️ MMDVM 通联提醒", "content": text.replace('\n', '<br>'), "template": "html"}
        try:
            requests.post(url, json=data, timeout=10)
        except: pass

def get_latest_log():
    """获取最新的 MMDVM 日志文件"""
    log_files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
    return max(log_files, key=os.path.getmtime) if log_files else None

def is_quiet_time(start_str, end_str):
    """判断是否在静音时段"""
    now = datetime.now().strftime("%H:%M")
    if start_str <= end_str:
        return start_str <= now <= end_str
    else:  # 跨天
        return now >= start_str or now <= end_str

def monitor_log():
    current_log_path = get_latest_log()
    if not current_log_path:
        print("❌ 错误：未找到日志文件")
        return
    
    print(f"🚀 MMDVM 监控已启动: {current_log_path}")
    
    while True:
        try:
            # 实时载入 Web 端配置
            config = load_config()
            my_callsign = config.get('my_callsign', '').upper()
            
            with open(current_log_path, "r", encoding="utf-8", errors="ignore") as f:
                # 关键：启动时跳到末尾，防止历史消息轰炸
                f.seek(0, 2) 
                
                while True:
                    # 检查是否跨天（产生新日志）
                    new_log_path = get_latest_log()
                    if new_log_path and new_log_path != current_log_path:
                        current_log_path = new_log_path
                        print(f"📅 自动切换日志: {current_log_path}")
                        break 

                    line = f.readline()
                    if not line:
                        time.sleep(1) # 降低 CPU 占用
                        continue
                    
                    # --- 核心解析逻辑 ---
                    # 匹配话音或数据结束行
                    if "end of" in line and "transmission" in line:
                        # 1. 区分业务类型
                        if "voice" in line.lower():
                            msg_type = "🎙️ 话音通联结束"
                        elif "data" in line.lower():
                            msg_type = "📟 数据业务结束"
                        else:
                            continue

                        # 2. 提取呼号 (from ...)
                        call_match = re.search(r'from\s+([A-Z0-9/-]+)', line)
                        remote_call = call_match.group(1).upper() if call_match else "未知"
                        
                        # 过滤逻辑：过滤自己、黑名单、静音模式
                        if remote_call == my_callsign: continue
                        if remote_call in [c.upper() for c in config.get('ignore_list', [])]: continue
                        
                        is_focus = remote_call in [c.upper() for c in config.get('focus_list', [])]
                        quiet_cfg = config.get('quiet_mode', {})
                        if quiet_cfg.get('enabled') and not is_focus:
                            if is_quiet_time(quiet_cfg.get('start_time'), quiet_cfg.get('end_time')):
                                continue

                        # 3. 提取其他信息
                        target_match = re.search(r'to\s+(TG\s*\d+|PC\s*\d+|Reflector\s*\d+|\d+)', line)
                        target_tg = target_match.group(1) if target_match else "未知"
                        
                        duration_match = re.search(r'(\d+\.?\d*)\s+seconds', line)
                        duration_val = duration_match.group(1) if duration_match else "0.0"
                        
                        slot = "1" if "Slot 1" in line else "2"
                        
                        # 4. 提取并转换时间 (Pi-Star 日志通常是 UTC)
                        time_match = re.search(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', line)
                        if time_match:
                            utc_time = datetime.strptime(time_match.group(), "%Y-%m-%d %H:%M:%S")
                            bj_now = utc_time + timedelta(hours=8) # 转换为北京时间
                        else:
                            bj_now = datetime.now()

                        bj_date = bj_now.strftime("%Y-%m-%d")
                        bj_time = bj_now.strftime("%H:%M:%S")

                        # 5. 按照您要求的格式组装推送
                        push_text = (
                            f"{msg_type}\n"
                            f"---\n"
                            f"👤 呼号: {remote_call}\n"
                            f"👥 群组: {target_tg}\n"
                            f"📅 日期: {bj_date}\n"
                            f"⏰ 时间: {bj_time}\n"
                            f"📡 时隙: {slot}\n"
                            f"⏳ 时长: {duration_val}s"
                        )

                        print(f"✅ 发送推送: {remote_call}")
                        send_push(push_text, config)

        except Exception as e:
            print(f"⚠️ 运行时异常: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_log()
