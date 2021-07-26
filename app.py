"""Telemetry Analytics

Manages and reports Edge platform telemetry

Jacobo Fanjul, 2021
"""

# Standard imports
import sys
import signal
from threading import Event

# Modules
from modules.config import Config
from modules.rest_api import RestAPI
from modules.telemetry import Telemetry
from modules.tegra_info import TegraInfo
import time

# Config parameters and globals
config = Config()
telemetry = Telemetry()
tegra_info = TegraInfo()


def main():
    """ Main app """
    print('Launching Telemetry Daemon')

    def clean_up(sig, frame):
        config.logger.info("Clean up done")
        telemetry.stop()
        sys.exit()
    
    # Launch RestAPI
    rest_api = RestAPI()
    server = rest_api.get_server()

    # Inits
    server.start()
    telemetry.start()

    signal.signal(signal.SIGINT, clean_up)
    signal.signal(signal.SIGTERM, clean_up)

    while True:
        Event().wait()
        tic = time.time()
        tegra_info.get()
        elap_time = time.time() - tic
        time.sleep(config.monitor_period - elap_time)


if __name__ == "__main__":
    main()
