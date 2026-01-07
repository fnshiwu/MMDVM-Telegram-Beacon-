import os, time, json, glob, re, urllib.request, urllib.parse, sys, base64, hmac, hashlib, mmap
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from threading import Semaphore

# --- 路径与常量配置 ---
CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"
LOCAL_ID_FILE = "/usr/local/etc/DMRIds.dat"

class ConfigManager:
    """配置管理器：支持热加载，减少IO操作"""
    _config = {}
    _last_mtime = 0
    _check_interval = 5  # 每5秒检查一次文件变化
    _last_check_time = 0

    @classmethod
    def get_config(cls):
        now = time.time()
        if now - cls._last_check_time < cls._check_interval:
            return cls._config

        cls._last_check_time = now
        if not os.path.exists(CONFIG_FILE):
            return {}
            
        try:
            mtime = os.path.getmtime(CONFIG_FILE)
            if mtime > cls._last_mtime:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cls._config = json.load(f)
                cls._last_mtime = mtime
        except Exception as e:
            print(f"配置读取失败: {e}")
        
        return cls._config

class HamInfoManager:
    """处理呼号信息查询与完整的 MCC 国家码匹配（中文补全版）"""
    
    # 完整 ITU MCC 国家/地区映射表 (包含中国 461 扩容段)
    MCC_MAP = {
        # 亚洲
        "460": "中国", "461": "中国", "454": "中国香港", "455": "中国澳门", "466": "中国台湾",
        "440": "日本", "441": "日本", "450": "韩国", "452": "越南",
        "520": "泰国", "525": "新加坡", "510": "印度尼西亚", "502": "马来西亚",
        "515": "菲律宾", "404": "印度", "405": "印度", "413": "斯里兰卡",
        "424": "阿联酋", "425": "以色列", "410": "巴基斯坦", "418": "伊拉克", "419": "科威特",
        "420": "沙特阿拉伯", "422": "阿 Oman", "426": "约旦", "427": "黎巴嫩",
        # 欧洲
        "202": "希腊", "204": "荷兰", "206": "比利时", "208": "法国",
        "212": "摩纳哥", "214": "西班牙", "216": "匈牙利", "218": "波黑",
        "219": "克罗地亚", "220": "塞尔维亚", "222": "意大利", "226": "罗马尼亚",
        "228": "瑞士", "230": "捷克", "231": "斯洛伐克", "232": "奥地利",
        "234": "英国", "235": "英国", "238": "丹麦", "240": "瑞典",
        "242": "挪威", "244": "芬兰", "246": "立陶宛", "247": "拉脱维亚",
        "248": "爱沙尼亚", "250": "俄罗斯", "255": "乌克兰", "257": "白俄罗斯",
        "259": "摩尔多瓦", "260": "波兰", "262": "德国", "266": "直布罗陀",
        "268": "葡萄牙", "270": "卢森堡", "272": "爱尔兰", "274": "冰岛",
        "276": "阿尔巴尼亚", "278": "马耳他", "280": "塞浦路斯", "282": "格鲁吉亚",
        "283": "亚美尼亚", "284": "保加利亚", "286": "土耳其", "290": "格陵兰",
        "293": "斯洛文尼亚", "294": "北马其顿", "295": "列支敦士登", "297": "黑山",
        # 北美
        "302": "加拿大", "310": "美国", "311": "美国", "312": "美国", "313": "美国",
        "314": "美国", "315": "美国", "316": "美国", "330": "波多黎各", "334": "墨西哥",
        "338": "牙买加", "340": "瓜德罗普", "342": "巴巴多斯", "344": "安提瓜",
        "346": "开曼群岛", "348": "英属维尔京群岛", "350": "百慕大",
        "352": "格林纳达", "354": "蒙特塞拉特", "356": "圣基茨和尼维斯", "358": "圣卢西亚",
        "360": "圣文森特", "362": "库拉索", "363": "阿鲁巴", "364": "巴哈马",
        "365": "安圭拉", "366": "多米尼克", "368": "古巴", "370": "多米尼加",
        "372": "海地", "374": "特立尼达和多巴哥", "376": "特克斯和凯科斯",
        # 南美
        "702": "伯利兹", "704": "危地马拉", "706": "萨尔瓦多", "708": "洪都拉斯",
        "710": "尼加拉瓜", "712": "哥斯达黎加", "714": "巴拿马", "716": "秘鲁",
        "722": "阿根廷", "724": "巴西", "730": "智利", "732": "哥伦比亚",
        "734": "委内瑞拉", "736": "玻利维亚", "738": "圭亚那", "740": "厄瓜多尔",
        "742": "法属圭亚那", "744": "巴拉圭", "746": "苏里南", "748": "乌拉圭",
        # 大洋洲
        "505": "澳大利亚", "530": "新西兰", "537": "巴布亚新几内亚", "542": "斐济",
        "544": "美属萨摩亚", "545": "基里巴斯", "546": "新喀里多尼亚", "547": "法属波利尼西亚",
        # 非洲
        "602": "埃及", "603": "阿尔及利亚", "604": "摩洛哥", "605": "突尼斯",
        "606": "利比亚", "607": "冈比亚", "608": "塞内加尔", "609": "毛里塔尼亚",
        "610": "马里", "611": "几内亚", "612": "科特迪瓦", "613": "布基纳法索",
        "614": "尼日尔", "615": "多哥", "616": "贝宁", "617": "毛里求斯",
        "618": "利比里亚", "619": "塞拉利昂", "620": "加纳", "621": "尼日利亚",
        "622": "乍得", "623": "中非", "624": "喀麦隆", "625": "佛得角",
        "626": "圣多美和普林西比", "627": "赤道几内亚", "628": "加蓬", "629": "刚果(布)",
        "630": "刚果(金)", "631": "安哥拉", "632": "几内亚比绍", "633": "塞舌尔",
        "634": "苏丹", "635": "卢旺达", "636": "埃塞俄比亚", "637": "索马里",
        "638": "吉布提", "639": "肯尼亚", "640": "坦桑尼亚", "641": "乌干达",
        "642": "布隆迪", "643": "莫桑比克", "645": "赞比亚", "646": "马达加斯加",
        "647": "留尼汪", "648": "津巴布韦", "649": "纳米比亚", "650": "马拉维",
        "651": "莱索托", "652": "博茨瓦纳", "653": "斯威士兰", "654": "科摩罗",
        "655": "南非"
    }

    def __init__(self, id_file):
        self.id_file = id_file
        self._io_lock = Semaphore(4)

    @lru_cache(maxsize=4096)
    def get_info(self, callsign):
        if not os.path.exists(self.id_file):
            return {"name": "", "loc": "未知"}

        if not self._io_lock.acquire(timeout=2):
            return {"name": "", "loc": "未知"}

        try:
            with open(self.id_file, 'rb') as f:
                try:
                    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                        query = f"\t{callsign}\t".encode('utf-8')
                        idx = mm.find(query)
                        
                        if idx != -1:
                            start = mm.rfind(b'\n', 0, idx) + 1
                            end = mm.find(b'\n', idx)
                            if end == -1: end = len(mm)
                            
                            line = mm[start:end].decode('utf-8', 'ignore')
                            parts = line.split('\t')
                            
                            # 基于第一列 DMR ID 提取 MCC 匹配国家
                            country = "未知"
                            if len(parts) > 0:
                                dmr_id = parts[0].strip()
                                mcc = dmr_id[:3]
                                country = self.MCC_MAP.get(mcc, "未知")

                            # 构造显示内容：城市, 省份 (国家)
                            loc_info = f"{parts[3].title()}, {parts[4].upper()}" if len(parts) > 4 else "未知"
                            return {"name": f" ({parts[2].upper()})", "loc": f"{loc_info} ({country})"}
                except ValueError:
                    pass
        except Exception as e:
            print(f"查询异常: {e}")
        finally:
            self._io_lock.release()
            
        return {"name": "", "loc": "未知"}

class PushService:
    """管理多平台推送逻辑"""
    _executor = ThreadPoolExecutor(max_workers=3)

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
    def _do_send_task(cls, config, type_label, body_text, is_voice):
        try:
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
        except Exception as e:
            print(f"推送任务异常: {e}")

    @classmethod
    def send(cls, config, type_label, body_text, is_voice=True, async_mode=True):
        if async_mode:
            cls._executor.submit(cls._do_send_task, config, type_label, body_text, is_voice)
        else:
            cls._do_send_task(config, type_label, body_text, is_voice)

class MMDVMMonitor:
    """核心监控类"""
    def __init__(self):
        self.last_msg = {"call": "", "ts": 0}
        self.ham_manager = HamInfoManager(LOCAL_ID_FILE)
        self.re_master = re.compile(
            r'end of (?P<v_type>(?:voice )?|data )transmission from '
            r'(?P<call>[A-Z0-9/\-]+) to (?P<target>[A-Z0-9/\-\s]+?), '
            r'(?P<dur>\d+\.?\d*) seconds, '
            r'(?P<loss>\d+)% packet loss, '
            r'BER: (?P<ber>\d+\.?\d*)%', 
            re.IGNORECASE
        )

    def is_quiet_time(self, conf):
        if not conf.get('quiet_mode', {}).get('enabled'): return False
        now = datetime.now().strftime("%H:%M")
        start, end = conf['quiet_mode']['start'], conf['quiet_mode']['end']
        return (start <= now <= end) if start <= end else (now >= start or now <= end)

    def get_latest_log(self):
        try:
            log_files = [f for f in glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log")) if os.path.getsize(f) > 0]
            return max(log_files, key=os.path.getmtime) if log_files else None
        except Exception:
            return None

    def run(self):
        print(f"MMDVM 监控启动成功，正在实时抓取日志指标...")
        while True:
            try:
                current_log = self.get_latest_log()
                if not current_log:
                    time.sleep(5); continue
                
                print(f"正在监控日志文件: {current_log}")
                with open(current_log, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(0, 2)
                    last_rotation_check = time.time()
                    while True:
                        if time.time() - last_rotation_check > 5:
                            new_log = self.get_latest_log()
                            if new_log and new_log != current_log: 
                                print(f"检测到日志轮转: {current_log} -> {new_log}")
                                break
                            last_rotation_check = time.time()

                        line = f.readline()
                        if not line:
                            time.sleep(0.1)
                            continue
                        
                        self.process_line(line)
            except Exception as e:
                print(f"运行异常: {e}"); time.sleep(5)

    def process_line(self, line):
        if "end of" not in line.lower(): return
        
        match = self.re_master.search(line)
        if not match: return

        try:
            conf = ConfigManager.get_config()
            if not conf: return

            v_type_raw = match.group('v_type').lower()
            is_v = 'data' not in v_type_raw
            call = match.group('call').upper()
            target = match.group('target').strip()
            dur = float(match.group('dur'))
            loss = int(match.group('loss'))
            ber = float(match.group('ber'))

            if self.is_quiet_time(conf): return
            if call in conf.get('ignore_list', []): return
            if conf.get('focus_list') and call not in conf['focus_list']: return
            
            curr_ts = time.time()
            if call == self.last_msg["call"] and (curr_ts - self.last_msg["ts"]) < 3: return
            if is_v and (dur < conf.get('min_duration', 1.0) or call == conf.get('my_callsign')): return
            
            self.last_msg.update({"call": call, "ts": curr_ts})
            info = self.ham_manager.get_info(call)
            slot = "Slot 1" if "Slot 1" in line else "Slot 2"
            
            # --- 构造推送模板 ---
            type_label = f"🎙️ 语音通联 ({slot})" if is_v else f"💾 数据模式 ({slot})"
            body = (f"👤 **呼号**: {call}{info['name']}\n"
                    f"👥 **群组**: {target}\n"
                    f"📍 **地区**: {info['loc']}\n"
                    f"📅 **日期**: {datetime.now().strftime('%Y-%m-%d')}\n"
                    f"⏰ **时间**: {datetime.now().strftime('%H:%M:%S')}\n"
                    f"⏳ **时长**: {dur}秒\n"
                    f"📦 **丢失**: {loss}%\n"
                    f"📉 **误码**: {ber}%")
            
            PushService.send(conf, type_label, body, is_voice=is_v, async_mode=True)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 匹配成功: {call} | Loss: {loss}% | BER: {ber}%")
            
        except Exception as e:
            print(f"解析错误: {e}")

if __name__ == "__main__":
    monitor = MMDVMMonitor()
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        try:
            c = ConfigManager.get_config()
            if not c:
                c = {}
            PushService.send(c, "🔔 MMDVM 监控测试", "国家匹配（基于完整 MCC）已启用。", is_voice=True, async_mode=False)
            print("测试推送已发出。")
        except Exception as e: print(f"测试失败: {e}")
    else:
        monitor.run()
