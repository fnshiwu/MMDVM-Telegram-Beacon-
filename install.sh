#!/bin/bash
rpi-rw

# --- 1. 权限解锁 ---
echo ">> 解锁目录权限..."
sudo chmod +w /var/www/dashboard/admin/

# --- 2. 部署 PHP 页面 ---
CUR_DIR=$(pwd)
if [ -f "$CUR_DIR/push_admin.php" ]; then
    sudo cp "$CUR_DIR/push_admin.php" /var/www/dashboard/admin/
    sudo chown www-data:www-data /var/www/dashboard/admin/push_admin.php
    sudo chmod 644 /var/www/dashboard/admin/push_admin.php
fi

# --- 3. 菜单注入 (带防御逻辑) ---
ADMIN_INDEX="/var/www/dashboard/admin/index.php"
sudo sed -i '/push_admin.php/d' "$ADMIN_INDEX"

# 优先匹配 PHP echo 模式，次选 HTML 模式
if grep -q "update.php" "$ADMIN_INDEX"; then
    sudo sed -i '/update.php/a \  echo \" <a href=\\\"/admin/push_admin.php\\\" style=\\\"color: #ffffff;\\\">推送设置</a> | \";' "$ADMIN_INDEX"
elif grep -q "href=\"/admin/\"" "$ADMIN_INDEX"; then
    sudo sed -i '/href="\/admin\/"/a <a href="/admin/push_admin.php" style="color: #ffffff;">推送设置</a> |' "$ADMIN_INDEX"
fi

# --- 4. 权限锁定还原 ---
sudo chmod -w /var/www/dashboard/admin/

# --- 5. 初始化配置 ---
if [ ! -f "/etc/mmdvm_push.json" ]; then
    echo '{"push_tg_enabled":false,"push_wx_enabled":false,"my_callsign":"","tg_token":"","tg_chat_id":"","wx_token":"","ignore_list":[],"focus_list":[],"quiet_mode":{"enabled":false,"start_time":"23:00","end_time":"07:00"}}' | sudo tee /etc/mmdvm_push.json
fi
sudo chmod 666 /etc/mmdvm_push.json

# --- 6. 部署服务 ---
sudo cp "$CUR_DIR/push_script.py" /home/pi-star/
if [ -f "$CUR_DIR/mmdvm-push.service" ]; then
    sudo cp "$CUR_DIR/mmdvm-push.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable mmdvm-push.service
    sudo systemctl restart mmdvm-push.service
fi

echo "✅ 安装成功！请刷新管理页面确认菜单。"
