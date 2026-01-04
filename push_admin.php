<?php
session_start();
$configFile = '/etc/mmdvm_push.json';
$serviceName = 'mmdvm_push.service';

// 确保配置文件存在，不存在则初始化
if (!file_exists($configFile)) {
    $initialConfig = [
        "my_callsign" => "BA4SMQ",
        "push_tg_enabled" => false,
        "tg_token" => "",
        "tg_chat_id" => "",
        "push_wx_enabled" => false,
        "wx_token" => "",
        "ignore_list" => [],
        "focus_list" => [],
        "quiet_mode" => ["enabled" => false, "start_time" => "23:00", "end_time" => "07:00"],
        "ui_lang" => "cn"
    ];
    file_put_contents($configFile, json_encode($initialConfig, JSON_PRETTY_PRINT));
}

$config = json_decode(file_get_contents($configFile), true);

// 1. 语言判定逻辑
if (isset($_GET['set_lang'])) {
    $_SESSION['pistar_push_lang'] = $_GET['set_lang'];
}
$current_lang = isset($_SESSION['pistar_push_lang']) ? $_SESSION['pistar_push_lang'] : (isset($config['ui_lang']) ? $config['ui_lang'] : 'cn');
$is_cn = ($current_lang === 'cn');

// 2. 核心词条定义
if ($is_cn) {
    $nav_dash = "仪表盘"; $nav_admin = "管理"; $nav_log = "日志"; $nav_power = "电源"; $nav_update = "更新"; $nav_config = "配置"; $nav_push = "推送设置";
    $txt_title = "推送功能设置"; $txt_call = "我的呼号"; $txt_tg = "Telegram 推送设置"; $txt_wx = "微信 (PushPlus) 设置";
    $txt_filter = "黑白名单管理"; $txt_ign = "忽略列表"; $txt_foc = "关注列表"; $txt_quiet = "静音时段 (Quiet Mode)";
    $txt_en = "启用推送"; $txt_save = "保存设置"; $txt_test = "发送测试"; $txt_l_sw = "Switch to English"; $target_l = "en";
    $txt_srv_ctrl = "服务控制"; $txt_srv_status = "服务状态"; $txt_start = "启动"; $txt_stop = "停止"; $txt_restart = "重启";
} else {
    $nav_dash = "Dashboard"; $nav_admin = "Admin"; $nav_log = "Live Logs"; $nav_power = "Power"; $nav_update = "Update"; $nav_config = "Configuration"; $nav_push = "Push Settings";
    $txt_title = "Push Notifier Settings"; $txt_call = "My Callsign"; $txt_tg = "Telegram Settings"; $txt_wx = "WeChat (PushPlus) Settings";
    $txt_filter = "Filter Lists"; $txt_ign = "Ignore List"; $txt_foc = "Focus List"; $txt_quiet = "Quiet Mode Range";
    $txt_en = "Enable Push"; $txt_save = "Save Settings"; $txt_test = "Send Test"; $txt_l_sw = "切换到中文"; $target_l = "cn";
    $txt_srv_ctrl = "Service Control"; $txt_srv_status = "Status"; $txt_start = "Start"; $txt_stop = "Stop"; $txt_restart = "Restart";
}

// 3. 逻辑处理
$alertMsg = ""; 
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'];
    
    // 保存设置
    if ($action === 'save') {
        $config['my_callsign'] = strtoupper(trim($_POST['callsign']));
        $config['push_tg_enabled'] = isset($_POST['tg_en']);
        $config['tg_token'] = trim($_POST['tg_token']);
        $config['tg_chat_id'] = trim($_POST['tg_chat_id']);
        $config['push_wx_enabled'] = isset($_POST['wx_en']);
        $config['wx_token'] = trim($_POST['wx_token']);
        $config['ignore_list'] = array_filter(array_map('trim', explode("\n", strtoupper($_POST['ignore_list']))));
        $config['focus_list'] = array_filter(array_map('trim', explode("\n", strtoupper($_POST['focus_list']))));
        $config['quiet_mode']['enabled'] = isset($_POST['qm_en']);
        $config['quiet_mode']['start_time'] = $_POST['qm_start'];
        $config['quiet_mode']['end_time'] = $_POST['qm_end'];
        $config['ui_lang'] = $current_lang; 
        file_put_contents($configFile, json_encode($config, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        $alertMsg = $is_cn ? "设置保存成功！" : "Settings Saved!";
    }
    
    // 服务控制逻辑 (Start/Stop/Restart)
    if (in_array($action, ['start', 'stop', 'restart'])) {
        shell_exec("sudo systemctl $action $serviceName");
        $alertMsg = $is_cn ? "操作已执行: $action" : "Action executed: $action";
    }

    // 发送测试
    if ($action === 'test') {
        $test_msg = "🔔 MMDVM Push Test\nCall: " . ($_POST['callsign'] ?: "BA4SMQ") . "\nTime: " . date("H:i:s");
        if (isset($_POST['tg_en'])) @file_get_contents("https://api.telegram.org/bot".trim($_POST['tg_token'])."/sendMessage?chat_id=".trim($_POST['tg_chat_id'])."&text=".urlencode($test_msg));
        if (isset($_POST['wx_en'])) @file_get_contents("http://www.pushplus.plus/send?token=".trim($_POST['wx_token'])."&title=Test&content=".urlencode($test_msg));
        $alertMsg = $is_cn ? "测试消息已发出！" : "Test message sent!";
    }
}

// 4. 获取服务实时状态
$status_raw = shell_exec("sudo systemctl status $serviceName");
$is_running = (strpos($status_raw, 'active (running)') !== false);
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="stylesheet" type="text/css" media="screen and (min-width: 830px)" href="css/pistar-css.php" />
    <link rel="stylesheet" type="text/css" media="screen and (max-width: 829px)" href="css/pistar-css-mini.php" />
    <title><?php echo $txt_title; ?></title>
    <style type="text/css">
        textarea { width: 98%; height: 60px; font-family: "Lucida Console", Monaco, monospace; font-size: 12px; border: 1px solid #666; background: #fdfdfd; }
        input[type="text"], input[type="password"], input[type="time"] { width: 95%; border: 1px solid #666; height: 22px; }
        .lang-link { color: #ffff00; text-decoration: none; border: 1px solid #ffff00; padding: 1px 4px; font-size: 10px; border-radius: 3px; }
        .lang-link:hover { background: #ffff00; color: #b55; }
        .btn-container { background: #ffffff; text-align: center; padding: 15px; }
        .btn-save { font-weight: bold; width: 100px; height: 32px; cursor: pointer; background: #eee; border: 1px solid #666; }
        .btn-test { background: #b55; color: white; width: 100px; height: 32px; cursor: pointer; border: 1px solid #000; font-weight: bold; margin-left: 5px; }
        .btn-ctrl { width: 70px; height: 32px; cursor: pointer; border: 1px solid #666; font-size: 11px; margin: 0 2px; }
        .status-tag { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; }
        .status-running { background: #4caf50; color: white; }
        .status-stopped { background: #f44336; color: white; }
    </style>
    <script type="text/javascript"><?php if ($alertMsg) { echo "alert('$alertMsg');"; } ?></script>
</head>
<body>
<div class="container">
    <div class="header">
        <div style="font-size: 8px; text-align: left; padding-left: 8px; float: left;">Hostname: <?php echo exec('hostname'); ?></div>
        <div style="font-size: 8px; text-align: right; padding-right: 8px;">Pi-Star: 4.2.3</div>
        <h1><?php echo ($is_cn ? "Pi-Star 数字语音 仪表盘" : "Pi-Star Digital Voice Dashboard") . " - BA4SMQ"; ?></h1>
        <p style="padding-right: 5px; text-align: right; color: #ffffff;"> 
            <a href="/" style="color: #ffffff;"><?php echo $nav_dash; ?></a> | 
            <a href="/admin/" style="color: #ffffff;"><?php echo $nav_admin; ?></a> | 
            <a href="/admin/live_modem_log.php" style="color: #ffffff;"><?php echo $nav_log; ?></a> | 
            <a href="/admin/power.php" style="color: #ffffff;"><?php echo $nav_power; ?></a> | 
            <a href="/admin/update.php" style="color: #ffffff;"><?php echo $nav_update; ?></a> | 
            <a href="/admin/push_admin.php" style="color: #ffffff; font-weight: bold;"><?php echo $nav_push; ?></a> | 
            <a href="/admin/configure.php" style="color: #ffffff;"><?php echo $nav_config; ?></a> | 
            <a href="?set_lang=<?php echo $target_l; ?>" class="lang-link"><?php echo $txt_l_sw; ?></a>
        </p>
    </div>

    <div class="contentwide">
        <form method="post">
        <table class="settings">
            <thead>
                <tr><th colspan="2"><?php echo $txt_srv_ctrl; ?></th></tr>
            </thead>
            <tbody>
                <tr>
                    <td align="right" width="35%"><?php echo $txt_srv_status; ?>:</td>
                    <td align="left">
                        <?php if ($is_running): ?>
                            <span class="status-tag status-running">RUNNING</span>
                        <?php else: ?>
                            <span class="status-tag status-stopped">STOPPED</span>
                        <?php endif; ?>
                    </td>
                </tr>
                <tr>
                    <td align="right">Actions:</td>
                    <td align="left">
                        <button type="submit" name="action" value="start" class="btn-ctrl" style="background:#e7ffe7;"><?php echo $txt_start; ?></button>
                        <button type="submit" name="action" value="stop" class="btn-ctrl" style="background:#ffe7e7;"><?php echo $txt_stop; ?></button>
                        <button type="submit" name="action" value="restart" class="btn-ctrl"><?php echo $txt_restart; ?></button>
                    </td>
                </tr>
            </tbody>

            <thead>
                <tr><th colspan="2"><?php echo $txt_title; ?></th></tr>
            </thead>
            <tbody>
                <tr>
                    <td align="right"><?php echo $txt_call; ?>:</td>
                    <td align="left"><input type="text" name="callsign" value="<?php echo $config['my_callsign'];?>" /></td>
                </tr>

                <tr><th colspan="2"><?php echo $txt_tg; ?></th></tr>
                <tr><td align="right"><?php echo $txt_en; ?>:</td><td align="left"><input type="checkbox" name="tg_en" <?php if($config['push_tg_enabled']) echo "checked";?> /></td></tr>
                <tr><td align="right">Bot Token:</td><td align="left"><input type="password" name="tg_token" value="<?php echo $config['tg_token'];?>" /></td></tr>
                <tr><td align="right">Chat ID:</td><td align="left"><input type="text" name="tg_chat_id" value="<?php echo $config['tg_chat_id'];?>" /></td></tr>

                <tr><th colspan="2"><?php echo $txt_wx; ?></th></tr>
                <tr><td align="right"><?php echo $txt_en; ?>:</td><td align="left"><input type="checkbox" name="wx_en" <?php if($config['push_wx_enabled']) echo "checked";?> /></td></tr>
                <tr><td align="right">Token:</td><td align="left"><input type="password" name="wx_token" value="<?php echo $config['wx_token'];?>" /></td></tr>

                <tr><th colspan="2"><?php echo $txt_filter; ?></th></tr>
                <tr><td align="right"><?php echo $txt_ign; ?>:</td><td align="left"><textarea name="ignore_list"><?php echo implode("\n", $config['ignore_list']);?></textarea></td></tr>
                <tr><td align="right"><?php echo $txt_foc; ?>:</td><td align="left"><textarea name="focus_list"><?php echo implode("\n", $config['focus_list']);?></textarea></td></tr>

                <tr><th colspan="2"><?php echo $txt_quiet; ?></th></tr>
                <tr><td align="right"><?php echo $txt_en; ?>:</td><td align="left"><input type="checkbox" name="qm_en" <?php if($config['quiet_mode']['enabled']) echo "checked";?> /></td></tr>
                <tr><td align="right"><?php echo ($is_cn ? "时间范围" : "Time Range"); ?>:</td><td align="left">
                    <input type="time" name="qm_start" style="width:80px;" value="<?php echo $config['quiet_mode']['start_time'];?>" /> - 
                    <input type="time" name="qm_end" style="width:80px;" value="<?php echo $config['quiet_mode']['end_time'];?>" />
                </td></tr>

                <tr>
                    <td colspan="2" class="btn-container">
                        <button type="submit" name="action" value="save" class="btn-save"><?php echo $txt_save; ?></button>
                        <button type="submit" name="action" value="test" class="btn-test"><?php echo $txt_test; ?></button>
                    </td>
                </tr>
            </tbody>
        </table>
        </form>
    </div>

    <div class="footer">
        Pi-Star / Pi-Star Dashboard, &copy; Andy Taylor (MW0MWZ) 2014-2026.<br />
        Push Notifier Mod by BA4SMQ.
    </div>
</div>
</body>
</html>
