没问题，GitHub 仓库通常需要中英文双语对照（或是纯英文 README）来获得更好的兼容性。我为你整理了一份**中英双语版**的 `README.md`，你可以直接复制到 GitHub 仓库中。

---

# MMDVM-Telegram-WeChat-Notifier

[中文版](https://www.google.com/search?q=%23%E4%B8%AD%E6%96%87%E7%89%88) | [English Version](https://www.google.com/search?q=%23english-version)

---

## 中文版

这是一个专为 **Pi-Star** 设计的轻量级通联推送工具。它能够实时监控 MMDVMHost 日志，并将通联记录以精美的格式推送至 **Telegram** 或 **微信 (PushPlus)**。

### ✨ 主要功能

* **实时监控**：毫秒级解析日志，松开 PTT 即刻收到通知。
* **双平台支持**：同时支持 Telegram Bot 和微信 PushPlus。
* **集成界面**：提供 Pi-Star 风格的双语管理网页。
* **零依赖**：Python 脚本采用原生库编写，无需安装任何第三方库。
* **自动运行**：支持开机自启和后台崩溃自动重启。

### 🛠️ 安装步骤

1. **获取代码**：
```bash
cd /home/pi-star
git clone https://github.com/你的用户名/MMDVM-Telegram-WeChat-Notifier.git
cd MMDVM-Telegram-WeChat-Notifier
chmod +x mmdvm_push.py

```


2. **部署 Web 管理界面**：
```bash
sudo touch /etc/mmdvm_push.json
sudo chmod 666 /etc/mmdvm_push.json
sudo cp push_admin.php /var/www/dashboard/admin/

```


3. **权限授权**（执行 `sudo visudo`）：
```text
www-data ALL=(ALL) NOPASSWD: /bin/systemctl start mmdvm_push.service, /bin/systemctl stop mmdvm_push.service, /bin/systemctl restart mmdvm_push.service, /bin/systemctl status mmdvm_push.service

```


4. **启动服务**：
```bash
sudo cp mmdvm_push.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mmdvm_push.service
sudo systemctl start mmdvm_push.service

```



---

## English Version

A lightweight notification tool designed for **Pi-Star**. It monitors MMDVMHost logs in real-time and pushes QSO records to **Telegram** or **WeChat (PushPlus)** with a clean, formatted style.

### ✨ Key Features

* **Real-time Monitoring**: Millisecond-level log parsing; get notified immediately after releasing PTT.
* **Dual-Platform Support**: Supports both Telegram Bot and WeChat (via PushPlus).
* **Integrated Web UI**: Bilingual management page designed with the Pi-Star dashboard style.
* **Zero Dependencies**: Pure Python script using native libraries; no `pip` or `requests` required.
* **Service Management**: Fully managed via Systemd for auto-start and crash recovery.

### 🛠️ Installation

1. **Clone the Repository**:
```bash
cd /home/pi-star
git clone https://github.com/YourUsername/MMDVM-Telegram-WeChat-Notifier.git
cd MMDVM-Telegram-WeChat-Notifier
chmod +x mmdvm_push.py

```


2. **Deploy Web Management UI**:
```bash
sudo touch /etc/mmdvm_push.json
sudo chmod 666 /etc/mmdvm_push.json
sudo cp push_admin.php /var/www/dashboard/admin/

```


3. **Authorize Permissions** (via `sudo visudo`):
```text
www-data ALL=(ALL) NOPASSWD: /bin/systemctl start mmdvm_push.service, /bin/systemctl stop mmdvm_push.service, /bin/systemctl restart mmdvm_push.service, /bin/systemctl status mmdvm_push.service

```


4. **Activate System Service**:
```bash
sudo cp mmdvm_push.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mmdvm_push.service
sudo systemctl start mmdvm_push.service

```



---

## 📝 Preview / 效果预览

> ## **🎙️ Voice Transmission Ended / 话音通联结束**
> 
> 
> 👤 **Callsign**: BG6DFN
> 👥 **Target**: TG 46001
> 📅 **Date**: 2026-01-05
> ⏰ **Time**: 19:43:48
> 📡 **Slot**: 1
> ⏳ **Duration**: 24.0s

---

## 🤝 Credits

* Pi-Star Dashboard by MW0MWZ
* Mod by **BA4SMQ**

---

**还需要我针对 GitHub 上的具体文件描述提供建议，或者帮你把 Python 脚本里的输出日志也改成中英双语吗？**
