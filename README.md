# MMDVM Telegram & WeChat Notifier 📡

### Pi-Star Hotspot Real-time Monitoring Assistant / Pi-Star 热点实时监控助手

[English](https://www.google.com/search?q=%23english) | [中文说明](https://www.google.com/search?q=%23chinese)

---

<a name="english"></a>

## English Version

### ✨ Features

* **Dual Platform Notification**: Real-time alerts to both **Telegram** (Markdown card) and **WeChat** (via PushPlus).
* **Smart QSO Filtering**: Only notifies when transmission duration is **> 5 seconds**, filtering out pings and kerchunking.
* **Mode Recognition**: Distinguishes between 🎙️ **Voice** and 💾 **Data** transmissions.
* **Timezone Correction**: Automatically converts UTC logs to **Local Time (Beijing Time)**.
* **Zero Maintenance**: Supports automatic log rotation without service restarts.
* **Self-Call Filtering**: Automatically ignores your own callsign to prevent notification loops.

### 🛠️ Deployment Steps

#### 1. Prepare Environment

Enable write mode on your Pi-Star:

```bash
rpi-rw

```

#### 2. Get Your Tokens

* **Telegram**: Create a bot via `@BotFather` to get `TOKEN`. Get your `CHAT_ID` via `@userinfobot`.
* **WeChat**: Follow the WeChat Official Account `pushplus推送加` to get your `Token`.

#### 3. Create the Script

```bash
nano ~/mmdvm_notify.py

```

Copy and paste the **Full Python Code** (provided below), then update your Tokens and Callsign in the config section.

#### 4. Configure Auto-start

```bash
sudo nano /etc/systemd/system/mmdvm_notify.service

```

Paste the following:

```ini
[Unit]
Description=MMDVM Notifier
After=network.target mmdvmhost.service

[Service]
User=root
WorkingDirectory=/home/pi-star
ExecStart=/usr/bin/python3 /home/pi-star/mmdvm_notify.py
Restart=always

[Install]
WantedBy=multi-user.target

```

Enable and start:

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now mmdvm_notify.service

```

---

<a name="chinese"></a>

## 中文说明

### ✨ 功能特性

* **双平台同步推送**：支持 **Telegram** (精美卡片) 与 **微信** (通过 PushPlus) 实时提醒。
* **智能通联判定**：仅推送时长 **> 5 秒** 的有效通联，自动过滤掉握手、测机等短信号。
* **模式识别**：自动识别 🎙️ **话音(Voice)** 与 💾 **数据(Data)** 传输。
* **时区自动转换**：将日志中的 UTC 时间自动转换为 **北京时间**。
* **零维护运行**：支持跨天日志自动切换，无需每日手动重启。
* **呼号过滤**：自动隐藏您自己呼号的发射记录，避免消息重复。

### 🛠️ 部署步骤

#### 1. 环境准备

确保 Pi-Star 处于可读写模式：

```bash
rpi-rw

```

#### 2. 获取推送 Token

* **Telegram**: 找 `@BotFather` 获取 `TOKEN`，找 `@userinfobot` 获取 `CHAT_ID`。
* **微信**: 微信关注公众号 `pushplus推送加`，在菜单栏获取您的 `Token`。

#### 3. 创建监控脚本

```bash
nano ~/mmdvm_notify.py

```

粘贴下方的 **完整 Python 代码**，并在配置区域填入您的 Token 和呼号。

#### 4. 配置开机自启

```bash
sudo nano /etc/systemd/system/mmdvm_notify.service

```

粘贴以下内容：

```ini
[Unit]
Description=MMDVM Telegram & WeChat Notifier
After=network.target mmdvmhost.service

[Service]
User=root
WorkingDirectory=/home/pi-star
ExecStart=/usr/bin/python3 /home/pi-star/mmdvm_notify.py
Restart=always

[Install]
WantedBy=multi-user.target

```

最后启动服务：

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now mmdvm_notify.service

```

---

### 📜 Full Python Code / 完整代码内容

```python
import time
import requests
import os
import glob
import re
from datetime import datetime, timedelta

# ================= [配置区域] =================
# 1. Telegram 配置
TG_TOKEN = "your token"
TG_CHAT_ID = "your id"

# 2. 微信推送配置 (PushPlus Token)
WX_TOKEN = "your token" 

# 3. 个人配置
MY_CALLSIGN = "你的呼号"  
LOG_DIR = "/var/log/pi-star/"
MIN_DURATION = 5.0  # 设定：仅推送大于 5 秒的通联
# =============================================

def send_tg(text):
    """发送消息到 Telegram"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    params = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.get(url, params=params, timeout=10)
    except:
        pass

def send_wx(title, content):
    """发送消息到微信 (PushPlus)"""
    # 检查 Token 是否填写（只判断是否为空）
    if not WX_TOKEN or "YOUR_" in WX_TOKEN:
        return

    url = 'http://www.pushplus.plus/send'
    data = {
        "token": WX_TOKEN,
        "title": title,
        "content": content,
        "template": "html"
    }
    try:
        res = requests.post(url, data=data, timeout=10)
        # 增加反馈打印，方便调试
        if res.status_code == 200:
            print(f"📡 微信接口反馈: {res.text}")
        else:
            print(f"❌ 微信接口异常，状态码: {res.status_code}")
    except Exception as e:
        print(f"❌ 微信推送连接失败: {e}")

def get_latest_log():
    """获取最新的 MMDVM 日志文件"""
    log_files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
    return max(log_files, key=os.path.getmtime) if log_files else None

def monitor_log():
    current_log_path = get_latest_log()
    if not current_log_path:
        print("❌ 错误：未找到日志文件")
        return
    
    print(f"🚀 监控已启动: {current_log_path}")
    print(f"设定：仅推送时长 > {MIN_DURATION} 秒的通联")
    
    while True:
        with open(current_log_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, 2)  # 跳到文件末尾
            while True:
                # 检查日期更替，自动切换日志文件
                new_log_path = get_latest_log()
                if new_log_path != current_log_path:
                    current_log_path = new_log_path
                    print(f"📅 自动切换至新日志: {current_log_path}")
                    break 

                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                
                # 匹配通联结束行
                if "end of" in line and "transmission" in line:
                    # 过滤掉自己的呼号
                    if MY_CALLSIGN.upper() in line.upper():
                        continue

                    # 1. 提取时长
                    duration_match = re.search(r'(\d+\.?\d*)\s+seconds', line)
                    duration_val = float(duration_match.group(1)) if duration_match else 0.0
                    
                    # --- 阈值判断：大于 5 秒才推送 ---
                    if duration_val > MIN_DURATION:
                        # 2. 提取呼号
                        call_match = re.search(r'from\s+([A-Z0-9/]+)', line)
                        remote_call = call_match.group(1) if call_match else "未知"
                        
                        # 3. 提取群组 (TG/PC)
                        tg_match = re.search(r'to\s+(TG\s*\d+|PC\s*\d+|Reflector\s*\d+)', line)
                        target_tg = tg_match.group(1) if tg_match else "未知"

                        # 4. 时间处理 (UTC 转北京时间)
                        try:
                            log_time_str = line[3:22]
                            utc_time = datetime.strptime(log_time_str, "%Y-%m-%d %H:%M:%S")
                            bj_now = utc_time + timedelta(hours=8)
                            bj_date = bj_now.strftime("%Y-%m-%d")
                            bj_time = bj_now.strftime("%H:%M:%S")
                        except:
                            bj_now = datetime.now()
                            bj_date = bj_now.strftime("%Y-%m-%d")
                            bj_time = bj_now.strftime("%H:%M:%S")

                        slot = "1" if "Slot 1" in line else "2"
                        mode_icon = "🎙️" if "voice" in line.lower() else "💾"
                        mode_text = "话音通联" if "voice" in line.lower() else "数据传输"

                        # --- 执行 Telegram 推送 ---
                        tg_msg = (
                            f"{mode_icon} *{mode_text}结束*\n"
                            f"---\n"
                            f"👤 *呼号*: `{remote_call}`\n"
                            f"👥 *群组*: `{target_tg}`\n"
                            f"📅 *日期*: `{bj_date}`\n"
                            f"⏰ *时间*: `{bj_time}`\n"
                            f"📡 *时隙*: `{slot}`\n"
                            f"⏳ *时长*: `{duration_val} 秒`"
                        )
                        send_tg(tg_msg)

                        # --- 执行微信推送 ---
                        wx_title = f"有效通联: {remote_call}"
                        wx_content = (
                            f"<b>模式:</b> {mode_text}<br>"
                            f"<b>呼号:</b> {remote_call}<br>"
                            f"<b>群组:</b> {target_tg}<br>"
                            f"<b>时间:</b> {bj_date} {bj_time}<br>"
                            f"<b>时隙:</b> {slot}<br>"
                            f"<b>时长:</b> {duration_val} 秒"
                        )
                        send_wx(wx_title, wx_content)
                        
                        print(f"✅ 推送成功: {remote_call} ({duration_val}s)")
                    else:
                        # 如果不满足 5 秒，仅在后台静默记录
                        print(f"⏭️ 忽略短信号: {line[23:45].strip()}... ({duration_val}s)")

if __name__ == "__main__":
    # 启动时发送上线提醒
    bj_start = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    start_msg = f"🤖 *MMDVM 监控已上线*\n⏰ 时间: `{bj_start}`\n⚙️ 设定: `>{MIN_DURATION}s 推送`"
    send_tg(start_msg)
    send_wx("MMDVM 监控上线", f"机器人已启动<br>当前时间: {bj_start}<br>推送阈值: {MIN_DURATION}秒")
    
    monitor_log()

```

---

### ⚙️ Useful Commands / 常用命令

* **Check Status / 查看状态**: `sudo systemctl status mmdvm_notify.service`
* **View Real-time Logs / 查看实时日志**: `sudo journalctl -u mmdvm_notify.service -f`
* **Stop Service / 停止服务**: `sudo systemctl stop mmdvm_notify.service`

**73 de BA4SMQ**

---
