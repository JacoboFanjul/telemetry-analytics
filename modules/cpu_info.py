# Standard imports
import time
import threading

# Modules
from modules.config import Config

# External packages
import psutil
import cpuinfo as cputil

# Config parameters and globals
config = Config()


class CPUInfo:
    def __init__(self):
        self.dict = {}
        cputil_info = cputil.get_cpu_info()
        if cputil_info['cpuinfo_version'][0] <= 5:
            self.dict['model'] = cputil_info['brand']
        else:
            self.dict['model'] = cputil_info['brand_raw']
        self.monitor_thread = threading.Thread(target=self.monitor, daemon=True)

    def start(self):
        self.monitor_thread.start()

    def get(self):
        self.dict['cores_physical'] = psutil.cpu_count(logical=False)
        self.dict['cores_logical'] = psutil.cpu_count()
        self.dict['usage'] = psutil.cpu_percent()
        self.dict['freq'] = psutil.cpu_freq()

    def monitor(self):
        while True:
            tic = time.time()
            self.get()
            elap_time = time.time() - tic
            time.sleep(config.monitor_period-elap_time)
