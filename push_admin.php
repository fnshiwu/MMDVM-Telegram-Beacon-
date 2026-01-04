
<?php
// 1. 环境初始化
require_once('config/version.php');
require_once('config/language.php');
$config_file = '/etc/mmdvm_push.json';

// 确保配置文件存在
if (!file_exists($config_file)) {
    $initial_config = [
        "push_tg_enabled" => false,
        "push_wx_enabled" => false,
        "my_callsign" => "BA4SMQ",
        "tg_token" => "",
        "tg_chat_id" => "",
        "wx_token" => "",
        "ignore_list" => [],
        "focus_list" => [],
        "min_duration" => 5.0,
        "quiet_mode" => ["enabled" => false, "start_time" => "23:00", "end_time" => "07:00"]
    ];
    file_put_contents($config_file, json_encode($initial_config, JSON_PRETTY_PRINT));
}

$c = json_decode(file_get_contents($config_file), true);
$status_msg = "";

// 2. 测试推送函数
function send_test($conf) {
    $test_text = "🔔 MMDVM 推送测试成功！\n时间: " . date("H:i:s") . "\n呼号: " . $conf['my_callsign'];
    $res_log = [];
    if ($conf['push_tg_enabled'] && !empty($conf['tg_token'])) {
        $url = "https://api.telegram.org/bot".$conf['tg_token']."/sendMessage?chat_id=".$conf['tg_chat_id']."&text=".urlencode($test_text);
        $res = @file_get_contents($url);
        $res_log[] = $res ? "TG:✅" : "TG:❌";
    }
    if ($conf['push_wx_enabled'] && !empty($conf['wx_token'])) {
        $data = json_encode(["token" => $conf['wx_token'], "title" => "MMDVM测试", "content" => $test_text]);
        $opts = ['http' => ['method' => 'POST', 'header' => "Content-type: application/json\r\n", 'content' => $data]];
        $res = @file_get_contents('http://www.pushplus.plus/send', false, stream_context_create($opts));
        $res_log[] = $res ? "微信:✅" : "微信:❌";
    }
    return count($res_log) > 0 ? implode(" | ", $res_log) : "请先开启通道并保存Token";
}

// 3. 处理表单提交
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    if (isset($_POST['save_cfg'])) {
        $c['push_tg_enabled'] = isset($_POST['tg_on']);
        $c['push_wx_enabled'] = isset($_POST['wx_on']);
        $c['my_callsign'] = strtoupper(trim($_POST['my_callsign']));
        $c['tg_token'] = trim($_POST['tg_token']);
        $c['tg_chat_id'] = trim($_POST['tg_chat_id']);
        $c['wx_token'] = trim($_POST['wx_token']);
        $c['ignore_list'] = array_filter(preg_split('/[,\s\n]+/', strtoupper($_POST['ignore_list'])));
        $c['focus_list'] = array_filter(preg_split('/[,\s\n]+/', strtoupper($_POST['focus_list'])));
        $c['quiet_mode']['enabled'] = isset($_POST['q_on']);
        $c['quiet_mode']['start_time'] = $_POST['q_start'];
        $c['quiet_mode']['end_time'] = $_POST['q_end'];
        file_put_contents($config_file, json_encode($c, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        $status_msg = "✅ 配置已保存";
    } elseif (isset($_POST['test_push'])) {
        $status_msg = "🚀 " . send_test($c);
    }
}
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" type="text/css" href="/css/pistar-css.php" />
    <title>Push Settings</title>
    <style>
        .cfg-box { background: #f9f9f9; color: #333; padding: 20px; border-radius: 5px; max-width: 800px; margin: 20px auto; text-align: left; border: 1px solid #ddd; }
        .cfg-box h3 { border-bottom: 2px solid #ff9000; padding-bottom: 5px; margin-top: 20px; font-size: 16px; }
        .input-full { width: 95%; padding: 8px; margin: 5px 0; border: 1px solid #ccc; border-radius: 3px; }
        textarea { width: 95%; height: 60px; border: 1px solid #ccc; padding: 8px; border-radius: 3px; }
        .btn-save { background: #ff9000; color: white; border: none; padding: 12px 25px; font-weight: bold; cursor: pointer; border-radius: 3px; }
        .btn-test { background: #444; color: white; border: none; padding: 12px 25px; cursor: pointer; border-radius: 3px; margin-left: 10px; }
        .status-bar { background: #fff3cd; padding: 10px; border-left: 5px solid #ffc107; margin-bottom: 20px; font-weight: bold; }
        /* 右上角返回按钮样式 */
        .back-link { float: right; color: #ffffff; text-decoration: none; font-size: 14px; border: 1px solid #ffffff; padding: 3px 8px; border-radius: 3px; margin-top: -35px; margin-right: 10px; }
        .back-link:hover { background: rgba(255,255,255,0.2); }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>Push Notification Settings</h1>
        <a href="/admin/index.php" class="back-link">返回管理界面</a>
    </div>

    <div class="content">
        <div class="cfg-box">
            <?php if($status_msg) echo "<div class='status-bar'>$status_msg</div>"; ?>
            <form method="post">
                <h3>1. 通道与密钥 (Tokens)</h3>
                <label><input type="checkbox" name="tg_on" <?php echo $c['push_tg_enabled']?'checked':''; ?>> Telegram</label> | 
                <label><input type="checkbox" name="wx_on" <?php echo $c['push_wx_enabled']?'checked':''; ?>> 微信</label><br><br>
                
                TG Token: <input type="text" name="tg_token" class="input-full" value="<?php echo $c['tg_token']; ?>">
                TG Chat ID: <input type="text" name="tg_chat_id" class="input-full" value="<?php echo $c['tg_chat_id']; ?>">
                微信 Token: <input type="text" name="wx_token" class="input-full" value="<?php echo $c['wx_token']; ?>">

                <h3>2. 呼号过滤</h3>
                我的呼号: <input type="text" name="my_callsign" value="<?php echo $c['my_callsign']; ?>"><br>
                忽略列表: <textarea name="ignore_list"><?php echo implode(", ", $c['ignore_list']); ?></textarea>
                关注列表: <textarea name="focus_list"><?php echo implode(", ", $c['focus_list']); ?></textarea>

                <h3>3. 静音模式</h3>
                <label><input type="checkbox" name="q_on" <?php echo $c['quiet_mode']['enabled']?'checked':''; ?>> 启用</label>
                从 <input type="time" name="q_start" value="<?php echo $c['quiet_mode']['start_time']; ?>"> 
                至 <input type="time" name="q_end" value="<?php echo $c['quiet_mode']['end_time']; ?>">

                <div style="margin-top:25px;">
                    <input type="submit" name="save_cfg" value="💾 保存设置" class="btn-save">
                    <button type="submit" name="test_push" class="btn-test">🧪 发送测试</button>
                </div>
            </form>
        </div>
    </div>
    <div class="footer">Pi-Star / MMDVM Push Tool</div>
</div>
</body>
</html>
