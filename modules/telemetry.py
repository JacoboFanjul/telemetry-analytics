# Standard imports
import json
import time
import threading

# Modules
from modules.config import Config
from modules.mqtt import MqttClient
from modules.cpu_info import CPUInfo
from modules.disk_info import DiskInfo
from modules.mem_info import MemInfo
from modules.net_info import NetInfo
from modules.tegra_info import TegraInfo

# Config parameters and globals
config = Config()


class Telemetry:
    def __init__(self):
        self.dict = {}
        self.cpu_info = CPUInfo()
        self.disk_usage = DiskInfo()
        self.mem_info = MemInfo()
        self.net_info = NetInfo()
        self.tegra_info = TegraInfo()
        self.avg_thread = threading.Thread(target=self.monitor_avg, daemon=True)
        self.mqtt_client = MqttClient()
        self._lock = threading.Lock()

    def start(self):
        self.mqtt_client.start()
        try:
            cats = json.loads(config.categories)
            if 'CPU' in cats['Active']:
                self.cpu_info.start()
            if 'Disk' in cats['Active']:
                self.disk_usage.start()
            if 'Mem' in cats['Active']:
                self.mem_info.start()
            if 'Net' in cats['Active']:
                self.net_info.start()
            if config.tegrastats is True:
                self.tegra_info.start()
        except (ValueError, KeyError) as ke:
            config.logger.error("Not valid category in config: {} ".format(ke), exc_info=True)
        time.sleep(config.monitor_period)
        self.avg_thread.start()

    def stop(self):
        self.mqtt_client.stop()

    def monitor_avg(self):
        while True:
            tic = time.time()
            with self._lock:
                self.dict['timestamp'] = time.time()
                try:
                    cats = json.loads(config.categories)
                    if 'CPU' in cats['Active']:
                        self.dict['cpu_info'] = self.cpu_info.dict
                    if 'Disk' in cats['Active']:
                        self.dict['disk_info'] = self.disk_usage.dict
                    if 'Mem' in cats['Active']:
                        self.dict['mem_info'] = self.mem_info.dict
                    if 'Net' in cats['Active']:
                        self.dict['net_info'] = self.net_info.dict
                    if config.tegrastats is True:
                        self.dict['tegra_info'] = self.tegra_info.dict
                except (ValueError, KeyError) as ke:
                    config.logger.error("Not valid category in config: {} ".format(ke), exc_info=True)

                self.mqtt_client.send(json.dumps(self.dict), self.mqtt_client.telemetry_topic)

            elap_time = time.time() - tic
            time.sleep(config.monitor_period - elap_time)
