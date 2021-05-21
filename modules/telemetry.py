# Standard imports
import json
import time
import threading

# Modules
from modules.config import Config
from modules.mqtt import MqttClient
from modules.energy_info import EnergyInfo
from modules.time_info import TimeInfo
from modules.cpu_info import CPUInfo
from modules.disk_info import DiskInfo
from modules.mem_info import MemInfo
from modules.net_info import NetInfo

# Config parameters and globals
config = Config()

# Defines
energy_topic = "konnekt/v3/service/konnektbox-telemetry/energy"
time_topic = "konnekt/v3/service/konnektbox-telemetry/time"
cpu_topic = "konnekt/v3/service/konnektbox-telemetry/cpu"
disk_topic = "konnekt/v3/service/konnektbox-telemetry/disk"
mem_topic = "konnekt/v3/service/konnektbox-telemetry/mem"
net_topic = "konnekt/v3/service/konnektbox-telemetry/net"
all_topic = "konnekt/v3/service/konnektbox-telemetry/all"


class Telemetry:
    def __init__(self):
        self.dict = {}
        self.energy_info = EnergyInfo()
        self.time_info = TimeInfo()
        self.cpu_info = CPUInfo()
        self.disk_usage = DiskInfo()
        self.mem_info = MemInfo()
        self.net_info = NetInfo()
        self.avg_thread = threading.Thread(target=self.monitor_avg, daemon=True)
        self.mqtt_client = MqttClient()
        self._lock = threading.Lock()

    def start(self):
        self.mqtt_client.start()
        try:
            cats = json.loads(config.categories)
            if 'Energy' in cats['Active']:
                self.energy_info.start()
            if 'Time' in cats['Active']:
                self.time_info.start()
            if 'CPU' in cats['Active']:
                self.cpu_info.start()
            if 'Disk' in cats['Active']:
                self.disk_usage.start()
            if 'Mem' in cats['Active']:
                self.mem_info.start()
            if 'Net' in cats['Active']:
                self.net_info.start()
        except (ValueError, KeyError) as ke:
            config.logger.error("Not valid category in config: {} ".format(ke), exc_info=True)
        time.sleep(config.report_period)
        self.avg_thread.start()

    def stop(self):
        self.mqtt_client.stop()

    def monitor_avg(self):
        while True:
            tic = time.time()
            with self._lock:
                try:
                    cats = json.loads(config.categories)
                    if 'Energy' in cats['Active']:
                        self.dict['Energy'] = self.energy_info.dict
                        self.mqtt_client.send(json.dumps(self.energy_info.dict), energy_topic)
                    if 'Time' in cats['Active']:
                        self.dict['Time'] = self.time_info.dict
                        self.mqtt_client.send(json.dumps(self.time_info.dict), time_topic)
                    if 'CPU' in cats['Active']:
                        self.cpu_info.get_avg()
                        self.dict['cpu_info'] = self.cpu_info.dict
                        self.mqtt_client.send(json.dumps(self.cpu_info.dict), cpu_topic)
                    if 'Disk' in cats['Active']:
                        self.disk_usage.get_avg()
                        self.dict['disk_info'] = self.disk_usage.dict
                        self.mqtt_client.send(json.dumps(self.disk_usage.dict), disk_topic)
                    if 'Mem' in cats['Active']:
                        self.mem_info.get_avg()
                        self.dict['mem_info'] = self.mem_info.dict
                        self.mqtt_client.send(json.dumps(self.mem_info.dict), mem_topic)
                    if 'Net' in cats['Active']:
                        self.net_info.get_avg()
                        self.dict['net_info'] = self.net_info.dict
                        self.mqtt_client.send(json.dumps(self.net_info.dict), net_topic)
                except (ValueError, KeyError) as ke:
                    config.logger.error("Not valid category in config: {} ".format(ke), exc_info=True)

                self.mqtt_client.send(json.dumps(self.dict), all_topic)

            elap_time = time.time() - tic
            time.sleep(config.report_period - elap_time)
