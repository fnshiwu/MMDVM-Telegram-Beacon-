
### 📖 GitHub 教程 (README.md - 双语版)

# MMDVM Push Notification Tool for Pi-Star

[中文版](https://www.google.com/search?q=%23chinese-version) | [English Version](https://www.google.com/search?q=%23english-version)

---

<a name="chinese-version"></a>

## 中文版教程

这是一个为 Pi-Star 设计的实时通联推送工具，支持通过 Telegram 和 微信 (PushPlus) 发送提醒。

### 🌟 功能

* **原生集成**：在 Pi-Star 管理页面导航栏直接添加“推送设置”链接。
* **双平台**：支持 Telegram Bot 和 微信 PushPlus 接口。
* **智能策略**：支持黑名单（忽略）、白名单（关注）以及夜间静音模式。
* **可视化管理**：无需修改代码，在网页端即可设置 Token 和 过滤列表。

### 🚀 快速安装

1. **运行环境初始化**：
```bash
rpi-rw
wget -qO- [https://github.com/1b95633f-ad90-4832-8c3e-3621373a0ae2](https://github.com/fnshiwu/MMDVM-Telegram-WeChat-Notifier/blob/main/install.sh)

```


2. **部署 Web 页面**：
将本仓库的 `push_admin.php` 上传到盒子的 `/var/www/dashboard/admin/` 目录。
3. **启动监控**：
运行后台 Python 脚本 `python3 push_script.py &`。

### ⚙️ 设置说明

1. 登录 Pi-Star，点击菜单栏新增的 **“推送设置”**。
2. 填写 Token 后点击 **“保存所有配置”**。
3. 点击 **“🧪 发送测试”** 确保配置正确。

---

<a name="english-version"></a>

## English Version

A real-time notification tool for Pi-Star, allowing users to receive MMDVM activity alerts via Telegram and WeChat (PushPlus).

### 🌟 Features

* **Seamless Integration**: Adds a "Push Setting" link directly to the Pi-Star admin navigation bar.
* **Dual Platforms**: Supports Telegram Bot and WeChat (via PushPlus API).
* **Smart Filtering**: Custom Callign Focus (Whitelist), Ignore (Blacklist), and Quiet Mode (DND).
* **Web UI Management**: Manage Tokens and filters via the web interface without touching the console.

### 🚀 Quick Start

1. **Initialization**:
```bash
rpi-rw
wget -qO- [blob:https://github.com/1b95633f-ad90-4832-8c3e-3621373a0ae2](https://github.com/fnshiwu/MMDVM-Telegram-WeChat-Notifier/blob/main/install.sh)

```


2. **Deploy Web Interface**:
Upload `push_admin.php` to your Pi-Star at `/var/www/dashboard/admin/`.
3. **Run Monitor**:
Execute the background service: `python3 push_script.py &`.

### ⚙️ Configuration

1. Open Pi-Star dashboard and click **"Push Setting"** in the top menu.
2. Enter your Tokens and click **"Save All Settings"**.
3. Click **"🧪 Send Test"** to verify the connection.

---

**Would you like me to help you create a `systemd` service file so that the Python script starts automatically every time you power on your Pi-Star?**
