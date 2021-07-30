from os import getenv
import logging
import sys


class Config:
    __instance = None

    def __new__(cls):
        if Config.__instance is None:
            Config.__instance = object.__new__(cls)
            Config.__instance.init()
        return Config.__instance

    def init(self):
        self.id = getenv("MQTT_ID", "telemetry_default")
        self.mqtt_broker = getenv("MQTT_HOST", "localhost")
        self.mqtt_port = int(getenv("MQTT_PORT", "1883"))
        self.mqtt_protocol = getenv("MQTT_PROTOCOL", "tcp")
        self.rest_port = int(getenv("REST_PORT", "8080"))
        self.monitor_period = int(getenv("MONITOR_PERIOD", "2"))
        self.categories = getenv("CATEGORIES", "{\"Active\":"
                                               "[\"CPU\", \"Disk\", \"Mem\", \"Net\"]}")
        self.rtt_server = getenv("RTT_SERVER", "8.8.8.8")
        self.tegrastats = bool(getenv("IS_JETSON", "False"))

        # Configure logger
        self.log_level = getenv("LOG_LEVEL", "DEBUG")

        if self.log_level == "INFO":
            level = logging.INFO
        else:
            level = logging.DEBUG

        self.logger = logging.Logger("ManagerLogger")
        out_hdlr = logging.StreamHandler(sys.stdout)
        out_hdlr.setFormatter(MyFormatter())
        self.logger.setLevel(level)
        self.logger.addHandler(out_hdlr)


# Custom formatter
class MyFormatter(logging.Formatter):
    err_fmt = "ERROR: %(msg)s"
    dbg_fmt = "DEBUG: %(module)s.py: line:%(lineno)d: %(msg)s"
    info_fmt = "INFO %(msg)s"

    def __init__(self):
        super().__init__(fmt="%(levelno)d: %(msg)s", datefmt=None, style="%")

    def format(self, record):

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._style._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._style._fmt = MyFormatter.dbg_fmt

        elif record.levelno == logging.INFO:
            self._style._fmt = MyFormatter.info_fmt

        elif record.levelno == logging.ERROR:
            self._style._fmt = MyFormatter.err_fmt

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._style._fmt = format_orig

        return result
