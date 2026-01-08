
---

# MMDVM-Push-Notifier (v2.98.1)

**Real-time Activity Notifications for Pi-Star via Telegram & WeChat** **基于 Pi-Star 的 MMDVM 通联实时推送系统 (Telegram & 微信 & 飞书)**

---

## 📖 Introduction / 简介

**MMDVM-Push-Notifier** is a lightweight tool for Pi-Star users to receive real-time radio activity notifications. It features a built-in web management panel, allowing you to configure push services, filters, and quiet hours directly from your browser.

**MMDVM-Push-Notifier** 是一款专为 Pi-Star 用户设计的轻量级通联推送工具。它集成了网页管理面板，您可以直接在浏览器中配置推送服务、过滤规则及静音时段。

### ✨ Features / 功能特性

* **Web Admin Panel**: Manage everything at `http://pi-star.local/admin/push_admin.php`.
* **Dual Channels**: Supports Telegram Bot and WeChat (via PushPlus).
* **Smart Filtering**: Filter by callsign (Blacklist/Whitelist) and minimum duration.
* **Quiet Mode**: Schedule "Do Not Disturb" hours (supports overnight range).
* **Pi-Star Integrated**: Native Pi-Star CSS style and bilingual support (CN/EN).
* **网页管理面板**: 在 `http://pi-star.local/admin/push_admin.php` 轻松配置。
* **多通道推送**: 支持 Telegram 机器人及微信 (通过 PushPlus)，飞书机器人。
* **智能过滤**: 支持呼号黑白名单过滤，以及自定义最小通联时长过滤。
* **静音模式**: 支持设置免打扰时段（支持跨天设置）。
* **深度集成**: 采用 Pi-Star 原生样式，支持中英文双语切换。
* **实时温度**: 实时温度显示。
* **MMDVM启动**: 设备上线提示包括IP,温度，内存，CPU占用。
* **高温预警**: 设备高温预警，提醒通风降温。
---

## 🛠️ Installation / 安装步骤

### 1. Download / 下载

Log in to your Pi-Star via SSH and run:

登录 Pi-Star 的 SSH 终端并执行：

```bash
rpi-rw
cd /home/pi-star
git clone https://github.com/fnshiwu/MMDVM-Push-Notifier.git
cd MMDVM-Push-Notifier

```

### 2. Fast Install / 一键安装

Run the installer script to set permissions and register the service:

运行安装脚本以自动设置权限并注册服务：

```bash
sudo bash install.sh

```

---

## 🔑 Token Setup / 获取 Token

### Telegram

1. **Bot Token**: Message [@BotFather](https://t.me/botfather) on TG, send `/newbot`, and follow the steps to get your API Token.
2. **Chat ID**: Message [@userinfobot](https://t.me/userinfobot) to get your numerical User ID.
3. **设置**: 将获取的 Token 和 ID 填入管理页面。

### WeChat (PushPlus)

1. Visit [PushPlus Official](http://www.pushplus.plus/) and login via WeChat.
2. Copy your **Token** from the "One-to-One Push" section.
3. **设置**: 将 Token 填入管理页面并确保已关注 PushPlus 公众号。

### 飞书机器人

1.打开群聊：在飞书电脑端，选择一个您希望接收推送消息的群组。
2.添加机器人：点击群组右上角的“设置”（三个点或设置图标） -> 群机器人 -> 添加机器人。
3.选择机器人类型：在弹出列表中选择 “自定义机器人”。
4.设置机器人信息：
    机器人名称：例如“MMDVM 监控助手”。
    描述：可填“接收 MMDVM 语音与数据推送”。
5.获取 Webhook 地址：点击“添加”后，系统会生成一个 Webhook 地址。
    重要：请复制并保存该地址，它类似于 https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxxxxx。
6.安全设置：选择“签名校验”
    重要：请复制并保存密钥。
     
---

## 📖 Usage / 使用说明

1. Open your browser: `http://pi-star.local/admin/push_admin.php`.
2. Enter your **Callsign** and **Tokens**.
3. Set **Min Duration** (e.g., 3.0s) to filter out short keying.
4. Click **SAVE SETTINGS**, then click **RESTART** to apply.
5. Use the **SEND TEST** button to verify the connection.
6. 浏览器访问: `http://pi-star.local/admin/push_admin.php`。
7. 输入您的 **呼号** 和 **Token**。
8. 设置 **最小推送时长** (建议 3.0s) 以过滤误触。
9. 点击 **SAVE SETTINGS** 保存，然后点击 **RESTART** 使其生效。
10. 点击 **SEND TEST** 按钮验证推送是否正常。

---

## 📂 File Structure / 文件说明

* `mmdvm_push.py`: The core backend script monitoring logs. (后端核心脚本)
* `push_admin.php`: Web-based management interface. (网页管理面板)
* `install.sh`: Automated installation & permission script. (一键安装脚本)
* `mmdvm_push.service`: Systemd service configuration. (系统服务配置)

---

## 卸载步骤

# 1. 切换到可读写模式
rpi-rw

# 2. 停止并禁用旧服务
sudo systemctl stop mmdvm_push.service
sudo systemctl disable mmdvm_push.service

# 3. 删除服务文件
sudo rm -f /etc/systemd/system/mmdvm_push.service
sudo systemctl daemon-reload

# 4. 删除 Web 页面链接
sudo rm -f /var/www/dashboard/admin/push_admin.php

# 5. 删除旧的项目文件夹 
sudo rm -rf /home/pi-star/MMDVM-Push-Notifier

# 6. (可选) 如果想完全重置配置，可以删除 JSON 配置文件
# 如果想保留之前的 Token 方便测试，可以跳过这一步
# sudo rm -f /etc/mmdvm_push.json

## 🤝 Contributing & 73

Contributions are welcome! If you have suggestions for new features, feel free to open an issue or pull request.

欢迎提供建议或提交代码！

**73! DE BA4SMQ**

---
