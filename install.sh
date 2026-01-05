#!/bin/bash
# MMDVM Push Notifier Installer by BA4SMQ
# Usage: sudo bash install.sh

echo "Starting installation..."
rpi-rw

# 1. 创建目录
mkdir -p /home/pi-star/MMDVM-Push-Notifier

# 2. 初始配置文件
if [ ! -f /etc/mmdvm_push.json ]; then
cat <<EOF > /etc/mmdvm_push.json
{
    "ui_lang": "cn",
    "my_callsign": "N0CALL",
    "min_duration": 3.0,
    "quiet_mode": {"enabled": false, "start": "23:00", "end": "07:00"},
    "push_tg_enabled": false,
    "tg_token": "",
    "tg_chat_id": "",
    "push_wx_enabled": false,
    "wx_token": "",
    "ignore_list": [],
    "focus_list": []
}
EOF
fi

# 3. 设置权限
sudo chown www-data:www-data /etc/mmdvm_push.json
sudo chmod 664 /etc/mmdvm_push.json
sudo cp push_admin.php /var/www/dashboard/admin/
sudo chown www-data:www-data /var/www/dashboard/admin/push_admin.php

# 4. 配置sudo免密 (关键步)
if ! sudo grep -q "mmdvm_push.service" /etc/sudoers; then
    echo "www-data ALL=(ALL) NOPASSWD: /bin/systemctl * mmdvm_push.service" | sudo tee -a /etc/sudoers
fi

# 5. 注册服务
sudo cp mmdvm_push.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mmdvm_push.service
sudo systemctl restart mmdvm_push.service

echo "Installation Complete! Please visit http://pi-star.local/admin/push_admin.php"
