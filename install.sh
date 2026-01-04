#!/bin/bash
# MMDVM Telegram/WeChat Notifier 安装脚本
# 适用系统: Pi-Star

# 1. 切换至读写模式
rpi-rw

echo "------------------------------------------"
echo "  MMDVM 推送工具安装程序 - 正在启动..."
echo "------------------------------------------"

# 2. 安装依赖
echo ">> 正在检查并安装 Python3 依赖..."
sudo apt-get update && sudo apt-get install -y python3-requests

# 3. 复制文件并设置权限
echo ">> 正在同步脚本文件..."
# 确保文件存在于当前目录
if [ ! -f "push_script.py" ]; then
    echo "❌ 错误: 未在当前目录找到 push_script.py"
    exit 1
fi

sudo cp push_script.py /home/pi-star/
sudo chmod +x /home/pi-star/push_script.py

# 复制 PHP 管理页面
if [ -f "push_admin.php" ]; then
    sudo cp push_admin.php /var/www/dashboard/admin/
    sudo chmod 644 /var/www/dashboard/admin/push_admin.php
fi

# 4. 初始化配置文件 (如果不存在)
if [ ! -f "/etc/mmdvm_push.json" ]; then
    echo ">> 初始化配置文件 /etc/mmdvm_push.json"
    echo '{"push_tg_enabled":false,"push_wx_enabled":false,"my_callsign":"","tg_token":"","tg_chat_id":"","wx_token":"","ignore_list":[],"focus_list":[],"quiet_mode":{"enabled":false,"start_time":"23:00","end_time":"07:00"}}' | sudo tee /etc/mmdvm_push.json
fi
sudo chmod 666 /etc/mmdvm_push.json

# 5. 集成到 Pi-Star 顶栏菜单
echo ">> 正在将 [推送设置] 链接添加至系统管理菜单..."
ADMIN_INDEX="/var/www/dashboard/admin/index.php"
if ! grep -q "push_admin.php" "$ADMIN_INDEX"; then
    # 在 "Configuration" 之前插入 "推送设置"
    sudo sed -i "/<a href=\"configure.php\"/i \  echo \" <a href=\\\"/admin/push_admin.php\\\" style=\\\"color: #ffffff;\\\">推送设置</a> | \";" "$ADMIN_INDEX"
fi

# 6. 配置 Systemd 服务
echo ">> 正在配置守护进程服务..."
if [ -f "mmdvm-push.service" ]; then
    sudo cp mmdvm-push.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable mmdvm-push.service
    sudo systemctl restart mmdvm-push.service
else
    echo "⚠️ 警告: 未找到 mmdvm-push.service，跳过服务配置。"
fi

echo "------------------------------------------"
echo "✅ 安装成功！"
echo "请刷新 Pi-Star 管理后台，点击顶部的 [推送设置] 进行配置。"
echo "------------------------------------------"
