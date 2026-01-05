<?php
session_start();
$configFile = '/etc/mmdvm_push.json';
$serviceName = 'mmdvm_push.service';

$config = json_decode(file_get_contents($configFile), true);
if (isset($_GET['set_lang'])) { 
    $_SESSION['pistar_push_lang'] = $_GET['set_lang']; 
    $config['ui_lang'] = $_GET['set_lang'];
    file_put_contents($configFile, json_encode($config, 192));
}
$current_lang = isset($_SESSION['pistar_push_lang']) ? $_SESSION['pistar_push_lang'] : ($config['ui_lang'] ?? 'cn');
$is_cn = ($current_lang === 'cn');

$lang = [
    'cn' => [
        'nav_push'=>'推送设置','srv_ctrl'=>'服务控制','status'=>'状态','run'=>'运行中','stop'=>'已停止',
        'btn_start'=>'启动','btn_stop'=>'停止','btn_res'=>'重启','btn_test'=>'发送测试','btn_save'=>'保存设置',
        'conf'=>'推送功能设置','my_call'=>'我的呼号','min_dur'=>'最小推送时长(秒)',
        'qm_en'=>'开启静音时段','qm_range'=>'静音时间范围','en'=>'启用','ign'=>'忽略列表(黑)','foc'=>'关注列表(白)'
    ],
    'en' => [
        'nav_push'=>'Push Settings','srv_ctrl'=>'Service Control','status'=>'Status','run'=>'RUNNING','stop'=>'STOPPED',
        'btn_start'=>'Start','btn_stop'=>'Stop','btn_res'=>'Restart','btn_test'=>'Send Test','btn_save'=>'SAVE SETTINGS',
        'conf'=>'Push Notifier Settings','my_call'=>'My Callsign','min_dur'=>'Min Duration(s)',
        'qm_en'=>'Quiet Mode','qm_range'=>'Quiet Time Range','en'=>'Enable','ign'=>'Ignore List','foc'=>'Focus List'
    ]
][$current_lang];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'];
    if ($action === 'save') {
        $config['my_callsign'] = strtoupper(trim($_POST['callsign']));
        $config['min_duration'] = floatval($_POST['min_duration']);
        $config['quiet_mode'] = ["enabled"=>isset($_POST['qm_en']), "start"=>$_POST['qm_start'], "end"=>$_POST['qm_end']];
        $config['push_tg_enabled'] = isset($_POST['tg_en']);
        $config['tg_token'] = trim($_POST['tg_token']);
        $config['tg_chat_id'] = trim($_POST['tg_chat_id']);
        $config['push_wx_enabled'] = isset($_POST['wx_en']);
        $config['wx_token'] = trim($_POST['wx_token']);
        $config['ignore_list'] = array_filter(array_map('trim', explode("\n", strtoupper($_POST['ignore_list']))));
        $config['focus_list'] = array_filter(array_map('trim', explode("\n", strtoupper($_POST['focus_list']))));
        file_put_contents($configFile, json_encode($config, 192));
    }
    if ($action === 'test') {
        $test_msg = "🚀 Push Test\nTime: ".date("H:i:s");
        if (isset($_POST['tg_en'])) @file_get_contents("https://api.telegram.org/bot".trim($_POST['tg_token'])."/sendMessage?".http_build_query(["chat_id"=>trim($_POST['tg_chat_id']),"text"=>$test_msg]));
        if (isset($_POST['wx_en'])) @file_get_contents("http://www.pushplus.plus/send?".http_build_query(["token"=>trim($_POST['wx_token']),"title"=>"Test","content"=>$test_msg]));
    }
    if (in_array($action, ['start','stop','restart'])) { shell_exec("sudo systemctl $action $serviceName"); }
}
$is_running = (strpos(shell_exec("sudo systemctl status $serviceName"), 'active (running)') !== false);
?>
<!DOCTYPE html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" type="text/css" href="css/pistar-css.php">
<style>textarea{width:95%;height:50px;} input[type="time"]{width:43%;display:inline-block;}</style>
</head><body><div class="container">
<div class="header"><h1>Push Notifier</h1>
<p style="text-align:right;padding-right:10px;"><a href="/" style="color:#fff;">Dashboard</a> | <a href="?set_lang=<?php echo $is_cn?'en':'cn';?>" style="color:#ff0;">[<?php echo $is_cn?'English':'中文';?>]</a></p>
</div><div class="contentwide"><form method="post"><table class="settings">
<thead><tr><th colspan="2"><?php echo $lang['srv_ctrl']; ?></th></tr></thead>
<tr><td align="right"><?php echo $lang['status']; ?>:</td><td><b style="color:<?php echo $is_running?'#008000':'#f00';?>"><?php echo $is_running?$lang['run']:$lang['stop'];?></b></td></tr>
<tr><td align="right">Action:</td><td><button type="submit" name="action" value="start"><?php echo $lang['btn_start'];?></button><button type="submit" name="action" value="restart"><?php echo $lang['btn_res'];?></button></td></tr>
<thead><tr><th colspan="2"><?php echo $lang['conf']; ?></th></tr></thead>
<tr><td align="right"><?php echo $lang['my_call']; ?>:</td><td><input type="text" name="callsign" value="<?php echo $config['my_callsign'];?>"></td></tr>
<tr><td align="right"><?php echo $lang['min_dur']; ?>:</td><td><input type="number" step="0.1" name="min_duration" value="<?php echo $config['min_duration'];?>"></td></tr>
<tr><td align="right"><?php echo $lang['qm_en']; ?>:</td><td><input type="checkbox" name="qm_en" <?php echo $config['quiet_mode']['enabled']?'checked':'';?>></td></tr>
<tr><td align="right"><?php echo $lang['qm_range']; ?>:</td><td><input type="time" name="qm_start" value="<?php echo $config['quiet_mode']['start'];?>"> - <input type="time" name="qm_end" value="<?php echo $config['quiet_mode']['end'];?>"></td></tr>
<thead><tr><th colspan="2">Telegram / WeChat</th></tr></thead>
<tr><td align="right">TG <?php echo $lang['en'];?>:</td><td><input type="checkbox" name="tg_en" <?php echo $config['push_tg_enabled']?'checked':'';?>> Token: <input type="password" name="tg_token" style="width:40%" value="<?php echo $config['tg_token'];?>"> ID: <input type="text" name="tg_chat_id" style="width:20%" value="<?php echo $config['tg_chat_id'];?>"></td></tr>
<tr><td align="right">WX <?php echo $lang['en'];?>:</td><td><input type="checkbox" name="wx_en" <?php echo $config['push_wx_enabled']?'checked':'';?>> Token: <input type="password" name="wx_token" style="width:60%" value="<?php echo $config['wx_token'];?>"></td></tr>
<thead><tr><th colspan="2"><?php echo $lang['ign'];?></th></tr></thead>
<tr><td colspan="2" align="center"><textarea name="ignore_list"><?php echo implode("\n",$config['ignore_list']);?></textarea></td></tr>
<thead><tr><th colspan="2"><?php echo $lang['foc'];?></th></tr></thead>
<tr><td colspan="2" align="center"><textarea name="focus_list"><?php echo implode("\n",$config['focus_list']);?></textarea></td></tr>
<tr><td colspan="2" align="center"><br><button type="submit" name="action" value="save" style="font-weight:bold;"><?php echo $lang['btn_save'];?></button> <button type="submit" name="action" value="test" style="background:#b55;color:#fff;"><?php echo $lang['btn_test'];?></button></td></tr>
</table></form></div></div></body></html>
