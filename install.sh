#!/bin/bash
# MMDVM-Push-Notifier 安装脚本
# 开发者: BA4SMQ

rpi-rw

echo "1. 创建并设置目录权限..."
INSTALL_DIR="/home/pi-star/MMDVM-Push-Notifier"
sudo mkdir -p $INSTALL_DIR
sudo chmod 755 /home/pi-star
sudo chmod 755 $INSTALL_DIR

echo "2. 初始化配置文件..."
CONFIG_FILE="/etc/mmdvm_push.json"
if [ ! -f "$CONFIG_FILE" ]; then
    sudo echo '{"my_callsign":"NOCALL","min_duration":5.0,"ui_lang":"cn"}' > $CONFIG_FILE
fi
sudo chmod 666 $CONFIG_FILE

echo "3. 部署 Web 管理页面..."
WEB_DIR="/var/www/dashboard/admin"
sudo ln -sf $INSTALL_DIR/push_admin.php $WEB_DIR/push_admin.php

echo "4. 配置服务自启动..."
SERVICE_FILE="/etc/systemd/system/mmdvm_push.service"
sudo ln -sf $INSTALL_DIR/mmdvm_push.service $SERVICE_FILE
sudo systemctl daemon-reload
sudo systemctl enable mmdvm_push.service

echo "5. 设置脚本执行权限..."
sudo chmod +x $INSTALL_DIR/mmdvm_push.py

echo "安装完成！请访问 Pi-Star 仪表盘 /admin/push_admin.php 进行配置。"
rpi-ro
