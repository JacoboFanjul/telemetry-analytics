# Standard imports
import time
import threading

# Modules
from modules.config import Config

# Config parameters and globals
config = Config()


class EnergyInfo:
    def __init__(self):
        self.dict = {}
        self.monitor_thread = threading.Thread(target=self.monitor, daemon=True)

    def start(self):
        self.monitor_thread.start()

    def get(self):
        """ Gets Energy info """

        def get_from_path(path):
            ret = ''
            try:
                with open(path, 'r') as f:
                    ret = f.read()
            except:
                ret = 'N/A'
            return ret

        self.dict['soc_power'] = get_from_path('/sys/bus/i2c/drivers/ina3221x/1-0040/iio:device0/in_power2_input')
        self.dict['cpu_power'] = get_from_path('/sys/bus/i2c/drivers/ina3221x/1-0040/iio:device0/in_power1_input')
        self.dict['gpu_power'] = get_from_path('/sys/bus/i2c/drivers/ina3221x/1-0040/iio:device0/in_power0_input')
        self.dict['ddr_power'] = get_from_path('/sys/bus/i2c/drivers/ina3221x/1-0041/iio:device1/in_power1_input')
        self.dict['sys5v_power'] = get_from_path('/sys/bus/i2c/drivers/ina3221x/1-0041/iio:device1/in_power2_input')

    def monitor(self):
        while True:
            tic = time.time()
            self.get()
            elap_time = time.time() - tic
            time.sleep(config.monitor_period-elap_time)
