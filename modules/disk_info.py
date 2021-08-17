# Standard imports
import time
import threading

# Modules
from modules.config import Config

# External packages
import psutil

# Config parameters and globals
config = Config()


class DiskInfo:
    def __init__(self):
        self.dict = {}
        self.monitor_thread = threading.Thread(target=self.monitor, daemon=True)

    def start(self):
        self.monitor_thread.start()

    def get(self):
        self.dict['available_MB'] = psutil.disk_usage('/')[2] / 1000000
        self.dict['usage_MB'] = psutil.disk_usage('/')[1] / 1000000

    def monitor(self):
        while True:
            tic = time.time()
            self.get()
            elap_time = time.time() - tic
            time.sleep(config.monitor_period-elap_time)
