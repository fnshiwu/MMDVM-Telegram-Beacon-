<?php
$configFile = '/etc/mmdvm_push.json';
$config = json_decode(file_get_contents($configFile), true);
// ... 此处保留之前的 PHP 处理逻辑 ...
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="stylesheet" type="text/css" href="css/pistar-css.php" />
    <title>Pi-Star - <?php echo "推送功能设置";?></title>
    <style type="text/css">
        textarea { width: 98%; height: 50px; background-color: #ffffff; border: 1px solid #000000; font-family: "Lucida Console", Monaco, monospace; }
        input[type="text"], input[type="password"], input[type="time"] { width: 98%; border: 1px solid #000000; }
    </style>
</head>
<body>
<div id="container">
    <div id="header">
        <h1>Pi-Star 数字语音仪表盘 - 推送设置</h1>
    </div>

    <div id="main">
        <form method="post" action="">
        <table class="settings">
            <thead>
                <tr>
                    <th colspan="2">核心配置 (BA4SMQ 推送工具)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td align="left">我的呼号:</td>
                    <td><input type="text" name="callsign" value="<?php echo $config['my_callsign'];?>" /></td>
                </tr>
                
                <tr>
                    <th colspan="2">Telegram 推送设置</th>
                </tr>
                <tr>
                    <td align="left">启用 Telegram:</td>
                    <td><input type="checkbox" name="tg_en" <?php if($config['push_tg_enabled']) echo "checked";?> /></td>
                </tr>
                <tr>
                    <td align="left">Bot Token:</td>
                    <td><input type="password" name="tg_token" value="<?php echo $config['tg_token'];?>" /></td>
                </tr>
                <tr>
                    <td align="left">Chat ID:</td>
                    <td><input type="text" name="tg_chat_id" value="<?php echo $config['tg_chat_id'];?>" /></td>
                </tr>

                <tr>
                    <th colspan="2">微信 (PushPlus) 设置</th>
                </tr>
                <tr>
                    <td align="left">启用微信推送:</td>
                    <td><input type="checkbox" name="wx_en" <?php if($config['push_wx_enabled']) echo "checked";?> /></td>
                </tr>
                <tr>
                    <td align="left">PushPlus Token:</td>
                    <td><input type="password" name="wx_token" value="<?php echo $config['wx_token'];?>" /></td>
                </tr>

                <tr>
                    <th colspan="2">黑白名单管理 (忽略/关注)</th>
                </tr>
                <tr>
                    <td align="left">忽略列表:<br /><small>(不推送这些呼号)</small></td>
                    <td><textarea name="ignore_list"><?php echo implode("\n", $config['ignore_list']);?></textarea></td>
                </tr>
                <tr>
                    <td align="left">关注列表:<br /><small>(优先推送且不静音)</small></td>
                    <td><textarea name="focus_list"><?php echo implode("\n", $config['focus_list']);?></textarea></td>
                </tr>

                <tr>
                    <th colspan="2">静音时段 (Quiet Mode)</th>
                </tr>
                <tr>
                    <td align="left">启用静音:</td>
                    <td><input type="checkbox" name="qm_en" <?php if($config['quiet_mode']['enabled']) echo "checked";?> /></td>
                </tr>
                <tr>
                    <td align="left">开始/结束时间:</td>
                    <td>
                        <input type="time" name="qm_start" style="width: 45%;" value="<?php echo $config['quiet_mode']['start_time'];?>" /> 
                        - 
                        <input type="time" name="qm_end" style="width: 45%;" value="<?php echo $config['quiet_mode']['end_time'];?>" />
                    </td>
                </tr>

                <tr>
                    <td colspan="2" style="text-align: center; background-color: #dddddd; padding: 10px;">
                        <input type="button" value="返回管理页面" onclick="location.href='/admin/'" />
                        <input type="submit" name="action" value="save" style="font-weight: bold;" />
                        <button type="submit" name="action" value="test" style="background-color: #8b0000; color: #ffffff;">发送测试推送</button>
                    </td>
                </tr>
            </tbody>
        </table>
        </form>
    </div>

    <div id="footer">
        Pi-Star / Pi-Star Dashboard, &copy; Andy Taylor (MW0MWZ) 2014-2026.<br />
        Push Notifier Mod by BA4SMQ.
    </div>
</div>
</body>
</html>
