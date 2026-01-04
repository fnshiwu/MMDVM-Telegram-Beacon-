<?php
// 必须包含 Pi-Star 的核心认证逻辑，确保只有管理员能访问
if (file_exists('/etc/mmdvm_push.json')) {
    $configFile = '/etc/mmdvm_push.json';
} else {
    die("配置文件不存在，请先运行安装脚本。");
}

// 保存逻辑
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $config = json_decode(file_get_contents($configFile), true);
    $config['push_tg_enabled'] = isset($_POST['tg_enabled']);
    $config['push_wx_enabled'] = isset($_POST['wx_enabled']);
    $config['my_callsign'] = strtoupper(trim($_POST['my_callsign']));
    $config['tg_token'] = trim($_POST['tg_token']);
    $config['tg_chat_id'] = trim($_POST['tg_chat_id']);
    $config['wx_token'] = trim($_POST['wx_token']);
    
    file_put_contents($configFile, json_encode($config, JSON_PRETTY_PRINT));
    $message = "设置已保存成功！";
}

$config = json_decode(file_get_contents($configFile), true);

// 检查后台服务状态
$service_status = shell_exec('systemctl is-active mmdvm-push.service');
$is_running = (trim($service_status) === 'active');
?>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml">
<head>
    <meta name="robots" content="index,follow" />
    <meta name="publisher" content="Pi-Star" />
    <meta name="author" content="BA4SMQ" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Pi-Star - MMDVM 推送设置</title>
    <link rel="stylesheet" type="text/css" href="/css/ircddblocal.css" /> <style>
        .status-box { padding: 10px; margin-bottom: 10px; border-radius: 5px; font-weight: bold; }
        .status-active { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status-inactive { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        input[type="text"], input[type="password"] { width: 95%; padding: 5px; border: 1px solid #ccc; border-radius: 3px; }
    </style>
</head>

<body>
<div id="container">
<div id="header">
    <div id="logo">
        <img src="/images/logo.png" width="200" alt="Pi-Star Logo" />
    </div>
</div>

<div id="nav">
    <a href="/admin/index.php" style="color: #ffffff;">返回控制台</a> |
    <a href="/admin/configure.php" style="color: #ffffff;">系统配置</a>
</div>

<div id="main">
    <div id="content">
        <div class="section">
            <h2 style="color: #dd0000;">MMDVM 通联推送设置</h2>
            
            <?php if (isset($message)): ?>
                <div style="background: #ffffcc; padding: 10px; border: 1px solid #ffcc00; margin-bottom: 15px; color: #333;">
                    <?php echo $message; ?>
                </div>
            <?php endif; ?>

            <div class="status-box <?php echo $is_running ? 'status-active' : 'status-inactive'; ?>">
                后台推送服务状态: <?php echo $is_running ? '● 正在运行 (Running)' : '○ 已停止 (Stopped)'; ?>
            </div>

            <form method="post">
                <table class="table-st" style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr>
                            <th colspan="2">基础设置</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td width="30%">我的呼号 (不推送自己):</td>
                            <td><input type="text" name="my_callsign" value="<?php echo $config['my_callsign']; ?>" placeholder="例如: BA4SMQ" /></td>
                        </tr>
                    </tbody>
                </table>

                <br />

                <table class="table-st" style="width: 100%;">
                    <thead>
                        <tr>
                            <th colspan="2">Telegram 配置</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td width="30%">启用 TG 推送:</td>
                            <td><input type="checkbox" name="tg_enabled" <?php echo $config['push_tg_enabled'] ? 'checked' : ''; ?> /></td>
                        </tr>
                        <tr>
                            <td>Bot Token:</td>
                            <td><input type="password" name="tg_token" value="<?php echo $config['tg_token']; ?>" /></td>
                        </tr>
                        <tr>
                            <td>Chat ID:</td>
                            <td><input type="text" name="tg_chat_id" value="<?php echo $config['tg_chat_id']; ?>" /></td>
                        </tr>
                    </tbody>
                </table>

                <br />

                <table class="table-st" style="width: 100%;">
                    <thead>
                        <tr>
                            <th colspan="2">微信 (PushPlus) 配置</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td width="30%">启用微信推送:</td>
                            <td><input type="checkbox" name="wx_enabled" <?php echo $config['push_wx_enabled'] ? 'checked' : ''; ?> /></td>
                        </tr>
                        <tr>
                            <td>PushPlus Token:</td>
                            <td><input type="password" name="wx_token" value="<?php echo $config['wx_token']; ?>" /></td>
                        </tr>
                    </tbody>
                </table>

                <div style="text-align: center; margin-top: 20px;">
                    <input type="submit" value="保存设置" style="padding: 10px 40px; background: #dd0000; color: white; border: none; cursor: pointer; border-radius: 5px; font-weight: bold;" />
                </div>
            </form>
        </div>
    </div>
</div>

<div id="footer">
    Pi-Star / MMDVM Notifier &copy; <?php echo date("Y"); ?> de BA4SMQ
</div>
</div>
</body>
</html>
