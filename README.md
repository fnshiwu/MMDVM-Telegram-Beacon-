这是一份为您精心整理的 **中英文双语版** `README.md` 教程。它采用了国际通用的开源项目排版风格，非常适合上传到 GitHub。

---

# MMDVM Telegram & WeChat Notifier 📡

### Pi-Star 通联实时监控助手

[English](https://www.google.com/search?q=%23english) | [中文说明](https://www.google.com/search?q=%23chinese)

---

<a name="english"></a>

## English Version

### ✨ Features

* **Dual Platform Notification**: Real-time alerts to both **Telegram** (Rich Markdown) and **WeChat** (via PushPlus).
* **Smart QSO Filtering**: Only notifies when transmission duration is **> 5 seconds**, effectively filtering out "kerchunking" or short pings.
* **Mode Recognition**: Automatically distinguishes between 🎙️ **Voice** and 💾 **Data** transmissions.
* **Timezone Correction**: Automatically converts MMDVM UTC logs to **Local Time (Beijing Time)**.
* **Zero Maintenance**: Supports automatic log rotation (daily logs) without service restarts.
* **Self-Call Filtering**: Automatically ignores your own callsign to prevent notification loops.

### 🛠️ Installation

#### 1. Prepare Environment

Enable write mode on your Pi-Star:

```bash
rpi-rw

```

#### 2. Get Your Tokens

* **Telegram**: Create a bot via `@BotFather` to get `TOKEN`. Get your `CHAT_ID` via `@userinfobot`.
* **WeChat**: Follow the WeChat Official Account `pushplus推送加` to get your `Token`.

#### 3. Deploy Script

Create the Python script:

```bash
nano ~/mmdvm_notify.py

```

*(Paste the provided full code and update your Tokens/Callsign)*

#### 4. Configure Service (Auto-start)

Create a systemd service:

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
ExecStart=/usr/bin/python3 /home/pi-star/mmdvm_notify.py
Restart=always

[Install]
WantedBy=multi-user.target

```

Start it:

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

#### 3. 创建脚本

创建 Python 脚本：

```bash
nano ~/mmdvm_notify.py

```

*(在此处粘贴完整代码，并修改配置区域的 Token 和个人呼号)*

#### 4. 配置开机自启

创建系统服务文件：

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

### ⚙️ Commands / 常用命令

* **Status / 状态**: `sudo systemctl status mmdvm_notify.service`
* **Logs / 日志**: `sudo journalctl -u mmdvm_notify.service -f`

**73 de BA4SMQ**

---
