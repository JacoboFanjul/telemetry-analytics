# Standard imports
import time
import threading

# Modules
from modules.config import Config

# Config parameters and globals
config = Config()


class TimeInfo:
    def __init__(self):
        self.dict = {}
        self.monitor_thread = threading.Thread(target=self.monitor, daemon=True)

    def start(self):
        self.monitor_thread.start()

    def get(self):
        """ Gets Energy info """

        self.dict['branch-misses'] = 'N/A'
        self.dict['cpu-cycles'] = 'N/A'
        self.dict['instructions'] = 'N/A'
        self.dict['context-switches'] = 'N/A'
        self.dict['task-clock'] = 'N/A'
        self.dict['migrations'] = 'N/A'

    def monitor(self):
        while True:
            tic = time.time()
            self.get()
            elap_time = time.time() - tic
            time.sleep(config.monitor_period-elap_time)
