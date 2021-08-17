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

# Config parameters and globals
config = Config()
telemetry = Telemetry()


def main():
    """ Main app """
    config.logger.info('Launching Telemetry Daemon')

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


if __name__ == "__main__":
    main()
