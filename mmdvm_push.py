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
        # 限制检查频率，避免频繁 stat 文件
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
                # print("配置已重新加载")
        except Exception as e:
            print(f"配置读取失败: {e}")
        
        return cls._config

class HamInfoManager:
    """处理呼号信息查询与缓存"""
    def __init__(self, id_file):
        self.id_file = id_file
        # 限制并发文件读取数，防止IO争抢
        self._io_lock = Semaphore(4)

    @lru_cache(maxsize=4096)
    def get_info(self, callsign):
        if not os.path.exists(self.id_file):
            return {"name": "", "loc": "Unknown"}

        # 使用 Semaphore 限制同时进行文件搜索的线程数
        if not self._io_lock.acquire(timeout=2):
            return {"name": "", "loc": "Unknown"}

        try:
            with open(self.id_file, 'rb') as f:
                # 使用 mmap 内存映射替代 grep 进程创建，大幅降低系统调用开销
                # access=mmap.ACCESS_READ 允许多进程同时读取
                try:
                    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                        # 构建字节查询串 (制表符分隔)
                        query = f"\t{callsign}\t".encode('utf-8')
                        idx = mm.find(query)
                        
                        if idx != -1:
                            # 找到匹配，向前寻找行首
                            start = mm.rfind(b'\n', 0, idx) + 1
                            # 向后寻找行尾
                            end = mm.find(b'\n', idx)
                            if end == -1: end = len(mm)
                            
                            # 提取并解码行数据
                            line = mm[start:end].decode('utf-8', 'ignore')
                            parts = line.split('\t')
                            
                            loc = f"{parts[3].title()}, {parts[4].upper()}" if len(parts) > 4 else "Unknown"
                            return {"name": f" ({parts[2].upper()})", "loc": loc}
                except ValueError:
                    # 空文件会导致 mmap error
                    pass
        except Exception as e:
            print(f"查询异常: {e}")
        finally:
            self._io_lock.release()
            
        return {"name": "", "loc": "Unknown"}

class PushService:
    """管理多平台推送逻辑"""
    # 使用线程池防止线程爆炸
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
        """实际执行推送的任务函数"""
        try:
            msg_header = "━━━━━━━━━━━━━━━\n"
            # 1. 微信推送
            if config.get('push_wx_enabled') and config.get('wx_token'):
                br = "<br>"
                html_content = f"<b>{type_label}</b>{br}{br.join(body_text.splitlines())}"
                d = json.dumps({"token": config['wx_token'], "title": type_label, "content": html_content, "template": "html"}).encode()
                cls.post_request("http://www.pushplus.plus/send", data=d, is_json=True)
            
            # 2. Telegram 推送
            if config.get('push_tg_enabled') and config.get('tg_token'):
                # 注意：body_text 需要进行 Markdown 转义以避免解析错误，这里暂且保持原样，建议优化转义
                params = urllib.parse.urlencode({"chat_id": config['tg_chat_id'], "text": f"*{type_label}*\n{msg_header}{body_text}", "parse_mode": "Markdown"})
                cls.post_request(f"https://api.telegram.org/bot{config['tg_token']}/sendMessage?{params}")
            
            # 3. 飞书推送
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
        # 精准匹配：捕获呼号、目标、时长、丢包率、误码率
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
            # 优化：通常文件名包含日期，直接按文件名排序可能比 getmtime 快且稳定，
            # 但为了保险起见，保持 getmtime，但在 run 中减少调用频率
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
                        # 优化：每5秒才检查一次是否有新日志，而不是死循环里每次都检查
                        if time.time() - last_rotation_check > 5:
                            new_log = self.get_latest_log()
                            if new_log and new_log != current_log: 
                                print(f"检测到日志轮转: {current_log} -> {new_log}")
                                break # 跳出内层循环，重新 open 新日志
                            last_rotation_check = time.time()

                        line = f.readline()
                        if not line:
                            time.sleep(0.1) # 增加微小延时，由 0.5 改为 0.1 响应更快，同时避免死循环占满单核
                            continue
                        
                        self.process_line(line)
            except Exception as e:
                print(f"运行异常: {e}"); time.sleep(5)

    def process_line(self, line):
        if "end of" not in line.lower(): return
        
        match = self.re_master.search(line)
        if not match: return

        try:
            # 优化：从 ConfigManager 获取配置，不再每次 IO 读取
            conf = ConfigManager.get_config()
            if not conf: return

            # 提取原始数值
            v_type_raw = match.group('v_type').lower()
            is_v = 'data' not in v_type_raw
            call = match.group('call').upper()
            target = match.group('target').strip()
            dur = float(match.group('dur'))
            loss = int(match.group('loss'))
            ber = float(match.group('ber'))

            # 过滤
            if self.is_quiet_time(conf): return
            if call in conf.get('ignore_list', []): return
            if conf.get('focus_list') and call not in conf['focus_list']: return
            
            curr_ts = time.time()
            # 简单去重：3秒内相同呼号不重复推
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
                # 如果没有配置文件，造一个临时的用于测试
                print("未找到配置文件，尝试使用空配置测试，可能因缺少Token失败。")
                c = {}
            PushService.send(c, "🔔 MMDVM 监控测试", "数值 Emoji 已去除，保持原始数据呈现。", is_voice=True, async_mode=False)
            print("测试推送已发出。")
        except Exception as e: print(f"测试失败: {e}")
    else:
        monitor.run()
