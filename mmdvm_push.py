import os, time, json, glob, re, urllib.request, urllib.parse, sys, base64, hmac, hashlib, mmap, subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from threading import Semaphore

# --- 核心版本号 ---
VERSION = "v3.0.7-S"

# --- [修复网页端] 必须置于顶部，确保面板调用秒回 ---
if len(sys.argv) > 1 and sys.argv[1] == "--version":
    print(VERSION)
    sys.exit(0)

# --- 路径与常量配置 ---
CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"
LOCAL_ID_FILE = "/usr/local/etc/nextionUsers.csv"

class ConfigManager:
    _config = {}
    _last_mtime = 0
    _check_interval = 5
    _last_check_time = 0

    @classmethod
    def get_config(cls):
        now = time.time()
        if now - cls._last_check_time < cls._check_interval:
            return cls._config
        cls._last_check_time = now
        if not os.path.exists(CONFIG_FILE): return {}
        try:
            mtime = os.path.getmtime(CONFIG_FILE)
            if mtime > cls._last_mtime:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cls._config = json.load(f)
                cls._last_mtime = mtime
        except Exception: pass
        return cls._config

class HamInfoManager:
    def __init__(self, id_file):
        self.id_file = id_file
        self._io_lock = Semaphore(4)
        self.geo_map = {
            "China": "🇨🇳 中国", "Hong Kong": "🇭🇰 中国香港", "Macao": "🇲🇴 中国澳门", "Taiwan": "🇹🇼 中国台湾",
            "Japan": "🇯🇵 日本", "Korea": "🇰🇷 韩国", "South Korea": "🇰🇷 韩国", "North Korea": "🇰🇵 朝鲜",
            "Thailand": "🇹🇭 泰国", "Singapore": "🇸🇬 新加坡", "Malaysia": "🇲🇾 马来西亚", "Indonesia": "🇮🇩 印度尼西亚",
            "Philippines": "🇵🇭 菲律宾", "Vietnam": "🇻🇳 越南", "India": "🇮🇳 印度", "Pakistan": "🇵🇰 巴基斯坦",
            "Sri Lanka": "🇱🇰 斯里兰卡", "Bangladesh": "🇧🇩 孟加拉国", "Nepal": "🇳🇵 尼泊尔", "Mongolia": "🇲🇳 蒙古",
            "United Arab Emirates": "🇦🇪 阿联酋", "UAE": "🇦🇪 阿联酋", "Saudi Arabia": "🇸🇦 沙特", "Israel": "🇮🇱 以色列",
            "Turkey": "🇹🇷 土耳其", "Iran": "🇮🇷 伊朗", "Iraq": "🇮🇶 伊拉克", "Kuwait": "🇰🇼 科威特",
            "Oman": "🇴🇲 阿曼", "Qatar": "🇶🇦 卡塔尔", "Jordan": "🇯🇴 约旦", "Lebanon": "🇱🇧 黎巴嫩",
            "Kazakhstan": "🇰🇿 哈萨克斯坦", "Uzbekistan": "🇺🇿 乌兹别克斯坦",
            "United Kingdom": "🇬🇧 英国", "UK": "🇬🇧 英国", "Germany": "🇩🇪 德国",
            "France": "🇫🇷 法国", "Italy": "🇮🇹 意大利", "Spain": "🇪🇸 西班牙", "Portugal": "🇵🇹 葡萄牙",
            "Russia": "🇷🇺 俄罗斯", "Russian Federation": "🇷🇺 俄罗斯", "Netherlands": "🇳🇱 荷兰",
            "Belgium": "🇧🇪 比利时", "Switzerland": "🇨🇭 瑞士", "Austria": "🇦🇹 奥地利", "Sweden": "🇸🇪 瑞典",
            "Norway": "🇳🇴 挪威", "Denmark": "🇩🇰 丹麦", "Finland": "🇫🇮 芬兰", "Poland": "🇵🇱 波兰",
            "Czech Republic": "🇨🇿 捷克", "Hungary": "🇭🇺 匈牙利", "Greece": "🇬🇷 希腊", "Ireland": "🇮🇪 爱尔兰",
            "Romania": "🇷🇴 罗马尼亚", "Bulgaria": "🇧🇬 门加利亚", "Ukraine": "🇺🇦 乌克兰", "Belarus": "🇧🇾 白俄罗斯",
            "Slovakia": "🇸🇰 斯洛伐克", "Croatia": "🇭🇷 克罗地亚", "Serbia": "🇷🇸 塞尔维亚", "Slovenia": "🇸🇮 斯洛文尼亚",
            "Estonia": "🇪🇪 爱沙尼亚", "Latvia": "🇱🇻 拉脱维亚", "Lithuania": "🇱🇹 立陶宛", "Iceland": "🇮🇸 冰岛",
            "Luxembourg": "🇱🇺 卢森堡", "Monaco": "🇲🇨 摩纳哥", "Cyprus": "🇨🇾 塞浦路斯", "Malta": "🇲🇹 马耳他",
            "United States": "🇺🇸 美国", "USA": "🇺🇸 美国", "Canada": "🇨🇦 加拿大", "Mexico": "🇲🇽 墨西哥",
            "Cuba": "🇨🇺 古巴", "Jamaica": "🇯🇲 牙买加", "Puerto Rico": "🇵🇷 波多黎各", "Dominican Republic": "🇩🇴 多米尼加",
            "Costa Rica": "🇨🇷 哥斯达黎加", "Panama": "🇵🇦 巴拿马", "Guatemala": "🇬🇹 危地马拉", "Honduras": "🇭🇳 洪都拉斯",
            "Brazil": "🇧🇷 巴西", "Argentina": "🇦🇷 阿根廷", "Chile": "🇨🇱 智利", "Colombia": "🇨🇴 哥伦比亚",
            "Peru": "🇵🇪 秘鲁", "Venezuela": "🇻🇪 委内瑞拉", "Uruguay": "🇺🇾 乌拉圭", "Paraguay": "🇵🇾 巴拉圭",
            "Ecuador": "🇪🇨 厄瓜多尔", "Bolivia": "🇧🇴 玻利维亚",
            "Australia": "🇦🇺 澳大利亚", "New Zealand": "🇳🇿 新西兰", "Fiji": "🇫🇯 斐济", "Papua New Guinea": "🇵🇬 巴布亚新几内亚",
            "South Africa": "🇿🇦 南非", "Egypt": "🇪🇬 埃及", "Nigeria": "🇳🇬 尼日利亚", "Kenya": "🇰🇪 肯尼亚",
            "Morocco": "🇲🇦 摩洛哥", "Algeria": "🇩🇿 阿尔及利亚", "Ethiopia": "🇪🇹 埃塞俄比亚", "Ghana": "🇬🇭 加纳",
            "Tanzania": "🇹🇿 坦桑尼亚", "Uganda": "🇺🇬 乌干达", "Mauritius": "🇲🇺 毛里求斯", "Seychelles": "🇸🇨 塞舌尔"
        }

    @lru_cache(maxsize=4096)
    def get_info(self, callsign):
        if not os.path.exists(self.id_file): return {"name": "", "loc": "Unknown"}
        if not self._io_lock.acquire(timeout=2): return {"name": "", "loc": "Unknown"}
        try:
            with open(self.id_file, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    query = f",{callsign},".encode('utf-8')
                    idx = mm.find(query)
                    if idx != -1:
                        start = mm.rfind(b'\n', 0, idx) + 1
                        end = mm.find(b'\n', idx)
                        line_bytes = mm[start:end]
                        try: line = line_bytes.decode('utf-8')
                        except: line = line_bytes.decode('gb18030', 'ignore')
                        parts = line.split(',')
                        first_name = parts[2].strip() if len(parts) > 2 else ""
                        last_name = parts[3].strip() if len(parts) > 3 else ""
                        city = parts[4].strip().title() if len(parts) > 4 else ""
                        state = parts[5].strip().upper() if len(parts) > 5 else ""
                        country = parts[6].strip()
                        if any('\u4e00' <= char <= '\u9fff' for char in country):
                            for k, v in self.geo_map.items():
                                if k in country or (len(v.split()) > 1 and v.split()[1] in country):
                                    country = v
                                    break
                        else: country = self.geo_map.get(country, country)
                        full_name = f"{first_name} {last_name}".strip().upper()
                        return {"name": f" ({full_name})", "loc": f"{city}, {state} ({country})"}
        except Exception: pass
        finally: self._io_lock.release()
        return {"name": "", "loc": "Unknown"}

class PushService:
    _executor = ThreadPoolExecutor(max_workers=3)

    @staticmethod
    def post_with_retry(url, data=None, is_json=False, retries=2):
        """【S级加固】带重试和强制超时"""
        for i in range(retries + 1):
            try:
                req = urllib.request.Request(url, data=data, method='POST') if data else urllib.request.Request(url)
                if is_json: req.add_header('Content-Type', 'application/json; charset=utf-8')
                with urllib.request.urlopen(req, timeout=10) as response:
                    return response.read().decode()
            except Exception:
                if i == retries: return None
                time.sleep(1)

    @classmethod
    def _do_push_logic(cls, config, type_label, body_text, is_voice):
        if config.get('push_fs_enabled') and config.get('fs_webhook'):
            ts = str(int(time.time()))
            template = "blue" if is_voice else "orange" if "上线" in type_label else "green"
            payload = {"msg_type": "interactive", "card": {"header": {"title": {"tag": "plain_text", "content": type_label}, "template": template}, "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": body_text}}]}}
            if config.get('fs_secret'):
                string_to_sign = f'{ts}\n{config["fs_secret"]}'
                hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
                payload["timestamp"], payload["sign"] = ts, base64.b64encode(hmac_code).decode('utf-8')
            cls.post_with_retry(config['fs_webhook'], data=json.dumps(payload).encode(), is_json=True)

        if config.get('push_wx_enabled') and config.get('wx_token'):
            br = "<br>"
            html = f"<b>{type_label}</b>{br}{br}{br.join(body_text.splitlines())}"
            d = json.dumps({"token": config['wx_token'], "title": type_label, "content": html, "template": "html"}).encode()
            cls.post_with_retry("http://www.pushplus.plus/send", data=d, is_json=True)

    @classmethod
    def send(cls, config, type_label, body_text, is_voice=True):
        cls._executor.submit(cls._do_push_logic, config, type_label, body_text, is_voice)

class MMDVMMonitor:
    def __init__(self):
        self.last_msg = {"call": "", "ts": 0}
        self.ham_manager = HamInfoManager(LOCAL_ID_FILE)
        self.re_master = re.compile(r'end of (?P<v_type>(?:voice\s+|data\s+)?)transmission from (?P<call>[A-Z0-9/\-]+) to (?P<target>[A-Z0-9/\-\s]+?), (?P<dur>\d+\.?\d*) seconds(?:, (?P<loss>\d+)% packet loss)?(?:, BER: (?P<ber>\d+\.?\d*)%)?', re.IGNORECASE)

    def get_sys_info(self):
        try:
            ip = subprocess.getoutput("hostname -I").split()[0]
            cpu = subprocess.getoutput("top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}'")
            mem = subprocess.getoutput("free -m | awk 'NR==2{printf \"%.1f%%\", $3*100/$2 }'")
            return ip, cpu, mem
        except: return "Unknown", "0", "0"

    def get_current_temp(self, conf):
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp_c = float(f.read()) / 1000.0
            return f"{temp_c:.1f}°C", temp_c
        except: return "N/A", 0.0

    def run(self):
        conf = ConfigManager.get_config()
        if conf.get('boot_push_enabled', True):
            for _ in range(10):
                ip, cpu, mem = self.get_sys_info()
                if ip != "Unknown": break
                time.sleep(3)
            temp_str, _ = self.get_current_temp(conf)
            body = (f"🚀 **设备已上线** ({VERSION})\n🌐 **当前IP**: {ip}\n🌡️ **系统温度**: {temp_str}\n📊 **CPU占用**: {cpu}%\n💾 **内存占用**: {mem}\n⏰ **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            PushService.send(conf, "⚙️ 系统启动通知", body, is_voice=False)

        while True:
            try:
                log_files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
                if not log_files: time.sleep(5); continue
                current_log = max(log_files, key=os.path.getmtime)
                
                # 【S级加固】日志打开保护逻辑
                try:
                    with open(current_log, "r", encoding="utf-8", errors="ignore") as f:
                        f.seek(0, 2)
                        last_rot_check = time.time()
                        while True:
                            if time.time() - last_rot_check > 5:
                                if max(log_files, key=os.path.getmtime) != current_log: break
                                last_rot_check = time.time()
                            line = f.readline()
                            if not line: time.sleep(0.1); continue
                            self.process_line(line)
                except (FileNotFoundError, PermissionError, OSError):
                    time.sleep(1); continue
            except Exception: time.sleep(5)

    def process_line(self, line):
        if "end of" not in line.lower(): return
        match = self.re_master.search(line)
        if not match: return
        conf = ConfigManager.get_config()
        call = match.group('call').upper()
        dur = float(match.group('dur'))
        my_call = conf.get('my_callsign', '').upper()
        
        # 屏蔽逻辑：时长、屏蔽列表、自己呼号
        if (my_call and call == my_call) or call in conf.get('ignore_list', []) or dur < conf.get('min_duration', 1.0):
            return
        
        curr_ts = time.time()
        if call == self.last_msg["call"] and (curr_ts - self.last_msg["ts"]) < 3: return
        self.last_msg.update({"call": call, "ts": curr_ts})
        
        info = self.ham_manager.get_info(call)
        temp_str, _ = self.get_current_temp(conf)
        is_v = 'data' not in match.group('v_type').lower()
        slot = " (Slot 1)" if "Slot 1" in line else " (Slot 2)" if "Slot 2" in line else ""
        body = (f"👤 **呼号**: {call}{info['name']}\n👥 **群组**: {match.group('target').strip()}\n📍 **地区**: {info['loc']}\n📅 **日期**: {datetime.now().strftime('%Y-%m-%d')}\n⏰ **时间**: {datetime.now().strftime('%H:%M:%S')}\n⏳ **时长**: {dur}秒\n📦 **丢失**: {match.group('loss') or '0'}%\n📉 **误码**: {match.group('ber') or '0.0'}%\n🌡️ **温度**: {temp_str}")
        PushService.send(conf, f"{'🎙️ 语音通联' if is_v else '💾 数据模式'}{slot}", body, is_voice=is_v)

if __name__ == "__main__":
    MMDVMMonitor().run()
