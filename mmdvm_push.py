import os, time, json, glob, re, urllib.request, urllib.parse, sys, base64, hmac, hashlib
from datetime import datetime
from threading import Thread

# --- 路径与常量配置 ---
CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"
LOCAL_ID_FILE = "/usr/local/etc/DMRIds.dat"

class HamInfoManager:
    def __init__(self, id_file):
        self.id_file = id_file
        self.cache = {}

    def get_info(self, callsign):
        if callsign in self.cache: return self.cache[callsign]
        if os.path.exists(self.id_file):
            try:
                cmd = f"grep -m 1 '\t{callsign}\t' {self.id_file}"
                with os.popen(cmd) as p:
                    res = p.read().strip()
                    if res:
                        parts = res.split('\t')
                        loc = f"{parts[3].title()}, {parts[4].upper()}" if len(parts) > 4 else "Unknown"
                        info = {"name": f" ({parts[2].upper()})", "loc": loc}
                        self.cache[callsign] = info
                        return info
            except: pass
        return {"name": "", "loc": "Unknown"}

class PushService:
    @staticmethod
    def get_fs_sign(secret, timestamp):
        string_to_sign = f'{timestamp}\n{secret}'
        hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        return base64.b64encode(hmac_code).decode('utf-8')

    @classmethod
    def post_request(cls, url, data=None, is_json=False):
        try:
            req = urllib.request.Request(url, data=data, method='POST') if data else urllib.request.Request(url)
            if is_json: req.add_header('Content-Type', 'application/json; charset=utf-8')
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode()
        except Exception as e:
            print(f"推送网络错误: {e}")
            return None

    @classmethod
    def send(cls, config, type_label, body_text, is_voice=True, async_mode=True):
        def build_and_send():
            msg_header = "━━━━━━━━━━━━━━━\n"
            if config.get('push_wx_enabled') and config.get('wx_token'):
                br = "<br>"
                html_content = f"<b>{type_label}</b>{br}{br.join(body_text.splitlines())}"
                d = json.dumps({"token": config['wx_token'], "title": type_label, "content": html_content, "template": "html"}).encode()
                cls.post_request("http://www.pushplus.plus/send", data=d, is_json=True)
            
            if config.get('push_tg_enabled') and config.get('tg_token'):
                params = urllib.parse.urlencode({"chat_id": config['tg_chat_id'], "text": f"*{type_label}*\n{msg_header}{body_text}", "parse_mode": "Markdown"})
                cls.post_request(f"https://api.telegram.org/bot{config['tg_token']}/sendMessage?{params}")
            
            if config.get('push_fs_enabled') and config.get('fs_webhook'):
                ts = str(int(time.time()))
                fs_payload = {"msg_type": "interactive", "card": {"header": {"title": {"tag": "plain_text", "content": type_label}, "template": "blue" if is_voice else "green"}, "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": body_text}}]}}
                if config.get('fs_secret'):
                    fs_payload["timestamp"], fs_payload["sign"] = ts, cls.get_fs_sign(config['fs_secret'], ts)
                cls.post_request(config['fs_webhook'], data=json.dumps(fs_payload).encode(), is_json=True)

        if async_mode:
            Thread(target=build_and_send, daemon=True).start()
        else:
            build_and_send()

class MMDVMMonitor:
    def __init__(self):
        self.last_msg = {"call": "", "ts": 0}
        self.ham_manager = HamInfoManager(LOCAL_ID_FILE)
        # 修正后的正则，精准适配你的日志格式
        self.re_master = re.compile(
            r'end of (?P<v_type>(?:voice )?|data )transmission from '
            r'(?P<call>[A-Z0-9/\-]+) to (?P<target>[A-Z0-9/\-\s]+?), '
            r'(?P<dur>\d+\.?\d*) seconds', 
            re.IGNORECASE
        )

    def is_quiet_time(self, conf):
        if not conf.get('quiet_mode', {}).get('enabled'): return False
        now = datetime.now().strftime("%H:%M")
        start, end = conf['quiet_mode']['start'], conf['quiet_mode']['end']
        return (start <= now <= end) if start <= end else (now >= start or now <= end)

    def get_latest_log(self):
        log_files = [f for f in glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log")) if os.path.getsize(f) > 0]
        return max(log_files, key=os.path.getmtime) if log_files else None

    def run(self):
        print(f"MMDVM 监控启动成功，正在实时解析日志...")
        while True:
            try:
                current_log = self.get_latest_log()
                if not current_log:
                    time.sleep(5); continue
                
                with open(current_log, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(0, 2)
                    while True:
                        new_log = self.get_latest_log()
                        if new_log and new_log != current_log: break
                        line = f.readline()
                        if not line:
                            time.sleep(0.5); continue
                        self.process_line(line)
            except Exception as e:
                print(f"运行异常: {e}"); time.sleep(5)

    def process_line(self, line):
        # 只要包含结束标志，就尝试匹配
        if "end of" not in line.lower(): return
        
        match = self.re_master.search(line)
        if not match: return

        try:
            v_type_raw = match.group('v_type').lower()
            is_v = 'data' not in v_type_raw
            call = match.group('call').upper()
            target = match.group('target').strip()
            dur = float(match.group('dur'))

            if not os.path.exists(CONFIG_FILE): return
            with open(CONFIG_FILE, 'r') as cf: conf = json.load(cf)

            # 过滤
            if self.is_quiet_time(conf): return
            if call in conf.get('ignore_list', []): return
            if conf.get('focus_list') and call not in conf['focus_list']: return
            
            curr_ts = time.time()
            if call == self.last_msg["call"] and (curr_ts - self.last_msg["ts"]) < 3: return
            if is_v and (dur < conf.get('min_duration', 1.0) or call == conf.get('my_callsign')): return
            
            self.last_msg.update({"call": call, "ts": curr_ts})
            info = self.ham_manager.get_info(call)
            
            # 自动提取 Slot
            slot = "Slot 1" if "Slot 1" in line else "Slot 2"
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 匹配成功: {call} -> {target} ({dur}s)")
            
            type_label = f"🎙️ 语音 ({slot})" if is_v else f"💾 数据 ({slot})"
            body = (f"👤 **呼号**: {call}{info['name']}\n👥 **群组**: {target}\n📍 **地区**: {info['loc']}\n"
                    f"📅 **日期**: {datetime.now().strftime('%Y-%m-%d')}\n⏰ **时间**: {datetime.now().strftime('%H:%M:%S')}\n⏳ **时长**: {dur}秒")
            
            PushService.send(conf, type_label, body, is_voice=is_v, async_mode=True)
        except Exception as e:
            print(f"处理错误: {e}")

if __name__ == "__main__":
    monitor = MMDVMMonitor()
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        try:
            with open(CONFIG_FILE, 'r') as cf: c = json.load(cf)
            PushService.send(c, "🔔 MMDVM 监控测试", "正则校准版测试成功！", is_voice=True, async_mode=False)
            print("测试推送已发出，请查收。")
        except Exception as e: print(f"测试失败: {e}")
    else:
        monitor.run()
