"""KonnektBox Manager

Manages KonnektBox telemetry

Copyright (C) 2020 IKERLAN S.Coop
"""

# Standard imports
import os
import sys
import signal
import time
from threading import Event

# Modules
from modules.config import Config
from modules.rest_api import RestAPI
from modules.telemetry import Telemetry

# Config parameters and globals
config = Config()
telemetry = Telemetry()


def main():
    """ Main app """
    print('Launching KonnetkBox Telemetry Daemon')

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
        #Event().wait()
        command = "./tegrastats"
        request = os.popen(command).read()
        command = "tegrastats --stop"
        os.system(command)
        print(request)
        time.sleep(config.monitor_period)


if __name__ == "__main__":
    main()
