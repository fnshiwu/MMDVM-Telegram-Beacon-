#!/bin/bash
# =============================================================
# MMDVM 推送工具 - 极简稳定安装版
# =============================================================

# 1. 强制进入读写模式
rpi-rw

echo ">> 正在同步核心文件..."
CUR_DIR=$(pwd)
sudo cp "$CUR_DIR/push_script.py" /home/pi-star/
sudo chmod +x /home/pi-star/push_script.py

# 部署 PHP 页面
sudo cp "$CUR_DIR/push_admin.php" /var/www/dashboard/admin/
sudo chown www-data:www-data /var/www/dashboard/admin/push_admin.php
sudo chmod 644 /var/www/dashboard/admin/push_admin.php

# 2. 菜单挂载 (使用最原始、之前成功过的逻辑)
echo ">> 正在注入菜单链接..."
ADMIN_INDEX="/var/www/dashboard/admin/index.php"

# 先清理所有包含 push_admin.php 的行，确保干净
sudo sed -i '/push_admin.php/d' "$ADMIN_INDEX"

# 核心注入：在包含 href="/admin/" 的行后面插入链接
# 注意：使用双引号和转义，确保兼容 PHP 语法
sudo sed -i '/href="\/admin\/"/a \ <a href="/admin/push_admin.php" style="color: #ffffff;">推送设置</a> |' "$ADMIN_INDEX"

# 3. 初始化配置与权限
echo ">> 正在初始化配置..."
if [ ! -f "/etc/mmdvm_push.json" ]; then
    echo '{"push_tg_enabled":false,"push_wx_enabled":false,"my_callsign":"","tg_token":"","tg_chat_id":"","wx_token":"","ignore_list":[],"focus_list":[],"quiet_mode":{"enabled":false,"start_time":"23:00","end_time":"07:00"}}' | sudo tee /etc/mmdvm_push.json
fi
sudo chmod 666 /etc/mmdvm_push.json

# 4. 重启服务
echo ">> 正在重启服务..."
if [ -f "$CUR_DIR/mmdvm-push.service" ]; then
    sudo cp "$CUR_DIR/mmdvm-push.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable mmdvm-push.service
    sudo systemctl restart mmdvm-push.service
fi

echo "✅ 安装已完成！请立即刷新浏览器页面。"
