<?php
// 1. 环境与配置初始化
require_once('config/version.php');
require_once('config/language.php');
$config_file = '/etc/mmdvm_push.json';

// 获取当前配置
if (file_exists($config_file)) {
    $c = json_decode(file_get_contents($config_file), true);
} else {
    $c = [
        "push_tg_enabled" => false, "push_wx_enabled" => false, "my_callsign" => "BA4SMQ",
        "tg_token" => "", "tg_chat_id" => "", "wx_token" => "",
        "ignore_list" => [], "focus_list" => [],
        "quiet_mode" => ["enabled" => false, "start_time" => "23:00", "end_time" => "07:00"]
    ];
}

$status_msg = "";

// 2. 发送测试函数
function send_test($conf) {
    $test_text = "🔔 MMDVM 推送测试成功！\n时间: " . date("H:i:s") . "\n呼号: " . $conf['my_callsign'];
    $res_log = [];
    if ($conf['push_tg_enabled'] && !empty($conf['tg_token'])) {
        $url = "https://api.telegram.org/bot".$conf['tg_token']."/sendMessage?chat_id=".$conf['tg_chat_id']."&text=".urlencode($test_text);
        $res = @file_get_contents($url);
        $res_log[] = $res ? "TG:✅" : "TG:❌";
    }
    if ($conf['push_wx_enabled'] && !empty($conf['wx_token'])) {
        $data = json_encode(["token" => $conf['wx_token'], "title" => "推送测试", "content" => $test_text]);
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
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" type="text/css" href="/css/pistar-css.php" />
    <title>Push Notification Settings</title>
    <style>
        body { background-color: #eee; }
        /* 核心居中容器 */
        .cfg-container {
            max-width: 850px;
            margin: 30px auto; /* 水平居中 */
            background: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: left;
        }
        h3 { border-bottom: 2px solid #ff9000; padding-bottom: 8px; margin-top: 25px; color: #444; }
        .input-full { width: 100%; box-sizing: border-box; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; font-family: monospace; }
        textarea { width: 100%; box-sizing: border-box; height: 80px; border: 1px solid #ccc; padding: 10px; border-radius: 4px; resize: vertical; }
        .status-bar { background: #fff3cd; padding: 15px; border-left: 5px solid #ffc107; margin-bottom: 20px; font-weight: bold; border-radius: 4px; }
        .btn-group { margin-top: 30px; text-align: center; border-top: 1px solid #eee; padding-top: 20px; }
        .btn-save { background: #ff9000; color: white; border: none; padding: 12px 30px; font-weight: bold; cursor: pointer; border-radius: 4px; font-size: 14px; }
        .btn-test { background: #444; color: white; border: none; padding: 12px 30px; cursor: pointer; border-radius: 4px; margin-left: 15px; font-size: 14px; }
        .back-link { float: right; color: #ffffff; text-decoration: none; font-size: 13px; border: 1px solid #ffffff; padding: 4px 10px; border-radius: 4px; margin-top: -40px; }
        .back-link:hover { background: rgba(255,255,255,0.2); }
        .hint { color: #777; font-size: 12px; margin-top: -5px; display: block; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>Push Notification Settings</h1>
        <a href="/admin/index.php" class="back-link">返回管理界面</a>
    </div>

    <div class="cfg-container">
        <?php if($status_msg) echo "<div class='status-bar'>$status_msg</div>"; ?>
        
        <form method="post">
            <h3>1. 通道与密钥 (Tokens)</h3>
            <label><input type="checkbox" name="tg_on" <?php echo $c['push_tg_enabled']?'checked':''; ?>> Telegram 推送</label> &nbsp;&nbsp;
            <label><input type="checkbox" name="wx_on" <?php echo $c['push_wx_enabled']?'checked':''; ?>> 微信 (PushPlus) 推送</label>
            <br><br>
            
            <strong>Telegram Token:</strong>
            <input type="text" name="tg_token" class="input-full" value="<?php echo $c['tg_token']; ?>" placeholder="例: 12345678:AAH-xxxx...">
            
            <strong>Telegram Chat ID:</strong>
            <input type="text" name="tg_chat_id" class="input-full" value="<?php echo $c['tg_chat_id']; ?>" placeholder="例: 987654321">
            
            <strong>微信 Token:</strong>
            <input type="text" name="wx_token" class="input-full" value="<?php echo $c['wx_token']; ?>" placeholder="PushPlus 官网提供的 Token">

            <h3>2. 呼号过滤策略</h3>
            我的呼号 (不推送): <input type="text" name="my_callsign" value="<?php echo $c['my_callsign']; ?>" style="text-transform: uppercase; padding: 5px;">
            
            <p style="margin-top:15px; margin-bottom:5px;">🚫 <b>忽略列表</b> (黑名单):</p>
            <span class="hint">呼号之间请使用逗号、空格或换行分隔。</span>
            <textarea name="ignore_list" placeholder="例如: BG4AAA, BY4BBB"><?php echo implode(", ", $c['ignore_list']); ?></textarea>
            
            <p style="margin-top:15px; margin-bottom:5px;">⭐ <b>关注列表</b> (白名单):</p>
            <span class="hint">关注的呼号将无视静音模式，强制发送提醒。</span>
            <textarea name="focus_list" placeholder="例如: BD4CCC, BI4DDD"><?php echo implode(", ", $c['focus_list']); ?></textarea>

            <h3>3. 夜间静音模式</h3>
            <label><input type="checkbox" name="q_on" <?php echo $c['quiet_mode']['enabled']?'checked':''; ?>> 启用静音时段</label>
            <div style="margin-top: 10px;">
                从 <input type="time" name="q_start" value="<?php echo $c['quiet_mode']['start_time']; ?>"> 
                至 <input type="time" name="q_end" value="<?php echo $c['quiet_mode']['end_time']; ?>">
            </div>

            <div class="btn-group">
                <button type="submit" name="save_cfg" class="btn-save">💾 保存全局设置</button>
                <button type="submit" name="test_push" class="btn-test">🧪 发送测试消息</button>
            </div>
        </form>
    </div>
    
    <div class="footer">Pi-Star / MMDVM Push Tool &copy; 2026</div>
</div>
</body>
</html>
