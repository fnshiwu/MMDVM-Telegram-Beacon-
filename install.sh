#!/bin/bash
rpi-rw
INSTALL_DIR="/home/pi-star/MMDVM-Push-Notifier"
PY_SCRIPT="$INSTALL_DIR/mmdvm_push.py"

# 从核心脚本动态获取版本号
VERSION=$(python3 $PY_SCRIPT --version 2>/dev/null || echo "v3.0.4")

echo "正在安装 MMDVM-Push-Notifier $VERSION..."

# [创建目录及设置权限逻辑...]
sudo mkdir -p $INSTALL_DIR
sudo chown -R pi-star:pi-star $INSTALL_DIR

# [配置 Service...]
sudo tee /etc/systemd/system/mmdvm_push.service <<EOF
[Unit]
Description=MMDVM Log Push Notifier $VERSION
After=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/python3 $PY_SCRIPT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo "安装完成，当前核心版本为: $VERSION"
rpi-ro
