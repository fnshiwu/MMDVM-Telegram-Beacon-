<?php
// MMDVM 推送插件管理页面 - 完全适配 Pi-Star 原生 UI
$configFile = '/etc/mmdvm_push.json';
$config = json_decode(file_get_contents($configFile), true);

$message = "";
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'];
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
        file_put_contents($configFile, json_encode($config, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        $message = "设置已成功保存！";
    }
    if ($action === 'test') {
        $test_msg = "🔔 MMDVM 推送测试\n呼号: " . ($_POST['callsign'] ?: "BA4SMQ") . "\n状态: 正常";
        if (isset($_POST['tg_en'])) @file_get_contents("https://api.telegram.org/bot".trim($_POST['tg_token'])."/sendMessage?chat_id=".trim($_POST['tg_chat_id'])."&text=".urlencode($test_msg));
        if (isset($_POST['wx_en'])) @file_get_contents("http://www.pushplus.plus/send?token=".trim($_POST['wx_token'])."&title=Test&content=".urlencode($test_msg));
        $message = "测试消息已发出！";
    }
}
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="stylesheet" type="text/css" media="screen and (min-width: 830px)" href="css/pistar-css.php?version=0.95" />
    <link rel="stylesheet" type="text/css" media="screen and (max-width: 829px)" href="css/pistar-css-mini.php?version=0.95" />
    <title>BA4SMQ - 推送功能设置</title>
    <style type="text/css">
        textarea { width: 95%; height: 60px; font-family: "Lucida Console", Monaco, monospace; font-size: 12px; }
        input[type="text"], input[type="password"], input[type="time"] { width: 95%; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div style="font-size: 8px; text-align: left; padding-left: 8px; float: left;">Hostname: ba4smq</div>
        <div style="font-size: 8px; text-align: right; padding-right: 8px;">Pi-Star:4.2.3 / 推送设置页面</div>
        <h1>Pi-Star 数字语音 仪表盘 - BA4SMQ</h1>
        <p style="padding-right: 5px; text-align: right; color: #ffffff;"> 
            <a href="/" style="color: #ffffff;">仪表盘</a> | 
            <a href="/admin/" style="color: #ffffff;">管理</a> | 
            <a href="/admin/index.php" style="color: #ffffff;">返回管理页</a> 
        </p>
    </div>

    <div class="contentwide">
        <b>推送功能全局配置</b>
        <?php if($message) echo "<div style='color: #000; background: #ffff00; padding: 5px; font-weight: bold;'>$message</div>"; ?>
        
        <form method="post">
        <table style="table-layout: fixed;">
            <tr><th colspan="2">核心信息</th></tr>
            <tr>
                <td align="right" width="30%">我的呼号:</td>
                <td align="left"><input type="text" name="callsign" value="<?php echo $config['my_callsign'];?>" /></td>
            </tr>

            <tr><th colspan="2">Telegram 推送服务</th></tr>
            <tr><td align="right">启用推送:</td><td align="left"><input type="checkbox" name="tg_en" <?php if($config['push_tg_enabled']) echo "checked";?> /></td></tr>
            <tr><td align="right">Bot Token:</td><td align="left"><input type="password" name="tg_token" value="<?php echo $config['tg_token'];?>" /></td></tr>
            <tr><td align="right">Chat ID:</td><td align="left"><input type="text" name="tg_chat_id" value="<?php echo $config['tg_chat_id'];?>" /></td></tr>

            <tr><th colspan="2">微信推送服务 (PushPlus)</th></tr>
            <tr><td align="right">启用推送:</td><td align="left"><input type="checkbox" name="wx_en" <?php if($config['push_wx_enabled']) echo "checked";?> /></td></tr>
            <tr><td align="right">Token:</td><td align="left"><input type="password" name="wx_token" value="<?php echo $config['wx_token'];?>" /></td></tr>

            <tr><th colspan="2">名单过滤 (每行一个呼号)</th></tr>
            <tr><td align="right">忽略列表:</td><td align="left"><textarea name="ignore_list"><?php echo implode("\n", $config['ignore_list']);?></textarea></td></tr>
            <tr><td align="right">关注列表:</td><td align="left"><textarea name="focus_list"><?php echo implode("\n", $config['focus_list']);?></textarea></td></tr>

            <tr><th colspan="2">静音模式 (不打扰时段)</th></tr>
            <tr><td align="right">启用静音:</td><td align="left"><input type="checkbox" name="qm_en" <?php if($config['quiet_mode']['enabled']) echo "checked";?> /></td></tr>
            <tr><td align="right">起止时间:</td><td align="left">
                <input type="time" name="qm_start" style="width:40%;" value="<?php echo $config['quiet_mode']['start_time'];?>" /> - 
                <input type="time" name="qm_end" style="width:40%;" value="<?php echo $config['quiet_mode']['end_time'];?>" />
            </td></tr>

            <tr>
                <td colspan="2" style="background: #ffffff; text-align: center; padding: 15px;">
                    <input type="submit" name="action" value="save" style="font-weight: bold; width: 100px;" value="保存设置" />
                    <input type="submit" name="action" value="test" style="background: #b55; color: white; width: 100px;" value="发送测试" />
                </td>
            </tr>
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
