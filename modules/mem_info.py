# Standard imports
import time
import threading

# Modules
from modules.config import Config

# External packages
import psutil

# Config parameters and globals
config = Config()


class MemInfo:
    def __init__(self):
        self.dict = {}
        self.monitor_thread = threading.Thread(target=self.monitor, daemon=True)

    def start(self):
        self.monitor_thread.start()

    def get(self):
        mem_attr = psutil.virtual_memory()
        self.dict['available_MB'] = mem_attr.available / 1000000
        self.dict['usage_MB'] = mem_attr.used / 1000000

    def monitor(self):
        while True:
            tic = time.time()
            self.get()
            elap_time = time.time() - tic
            time.sleep(config.monitor_period-elap_time)
