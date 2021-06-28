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
        self.dict = {'available_MB': [],
                     'usage_MB': []}
        self.monitor_thread = threading.Thread(target=self.monitor, daemon=True)

    def start(self):
        self.monitor_thread.start()

    def get(self):
        """ Get mem usage and availability """

        mem_attr = psutil.virtual_memory()
        self.dict['available_MB'].append(mem_attr.available / 1000000)
        self.dict['usage_MB'].append(mem_attr.used / 1000000)

    def monitor(self):
        while True:
            tic = time.time()
            self.get()
            elap_time = time.time() - tic
            time.sleep(config.monitor_period-elap_time)

    def get_avg(self):
        """ Averages mem usage and availability """

        try:
            self.dict['avg_available_MB'] = sum(self.dict['available_MB'])/len(self.dict['available_MB'])
            self.dict['avg_usage_MB'] = sum(self.dict['usage_MB'])/len(self.dict['usage_MB'])
        except ZeroDivisionError as e:
            config.logger.error("Math. error: {}".format(e))
        self.dict['available_MB'] = []
        self.dict['usage_MB'] = []
