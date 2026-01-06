#!/bin/bash
# MMDVM-Push-Notifier 增强型安装脚本
# 开发者: BA4SMQ

# 切换为读写模式
rpi-rw

echo "1. 正在创建并设置目录权限..."
INSTALL_DIR="/home/pi-star/MMDVM-Push-Notifier"
sudo mkdir -p $INSTALL_DIR
# 确保 pi-star 用户拥有该目录
sudo chown -R pi-star:pi-star $INSTALL_DIR
sudo chmod 755 $INSTALL_DIR

echo "2. 正在初始化配置文件..."
CONFIG_FILE="/etc/mmdvm_push.json"
if [ ! -f "$CONFIG_FILE" ]; then
    # 使用 tee 配合 sudo 解决权限重定向问题
    echo '{"my_callsign":"NOCALL","min_duration":1.0,"ui_lang":"cn","ignore_list":[],"focus_list":[]}' | sudo tee $CONFIG_FILE > /dev/null
fi
# 设置权限，允许 PHP (www-data) 读写配置文件
sudo chown www-data:www-data $CONFIG_FILE
sudo chmod 664 $CONFIG_FILE

echo "3. 部署 Web 管理页面..."
WEB_DIR="/var/www/dashboard/admin"
# 建立软链接
if [ -d "$WEB_DIR" ]; then
    sudo ln -sf $INSTALL_DIR/push_admin.php $WEB_DIR/push_admin.php
    echo "Web 页面已链接到: $WEB_DIR/push_admin.php"
else
    echo "警告: 找不到 Web 目录 $WEB_DIR"
fi

echo "4. 配置服务自启动..."
SERVICE_FILE="/etc/systemd/system/mmdvm_push.service"
# 确保项目目录下已有 service 文件，如果没有则现场创建一个
if [ ! -f "$INSTALL_DIR/mmdvm_push.service" ]; then
    echo "正在生成服务配置文件..."
    sudo tee $INSTALL_DIR/mmdvm_push.service <<EOF
[Unit]
Description=MMDVM Log Push Notifier
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/mmdvm_push.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
fi
sudo ln -sf $INSTALL_DIR/mmdvm_push.service $SERVICE_FILE
sudo systemctl daemon-reload
sudo systemctl enable mmdvm_push.service

echo "5. 设置脚本执行权限..."
sudo chmod +x $INSTALL_DIR/mmdvm_push.py

echo "------------------------------------------------"
echo "安装完成！"
echo "1. 请访问: http://pi-star.local/admin/push_admin.php"
echo "2. 在 Web 页面点击 'SAVE SETTINGS' 后点击 'Start' 启动服务。"
echo "------------------------------------------------"

# 切回只读模式
rpi-ro
