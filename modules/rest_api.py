import uvicorn
from fastapi import FastAPI, Request, Response
from modules.config import Config
from threading import Thread
import time

config = Config()

SVC_HEADER = "/jjsmarthome/v1"

app = FastAPI()


class RestAPI:
    def get_server(self):
        uvicorn_config = uvicorn.Config(
            app,
            host="0.0.0.0",
            reload=False,
            port=config.rest_port,
            workers=1,
        )
        return Server(config=uvicorn_config)


@app.get(f"{SVC_HEADER}/ping")
def ping(response: Response):
    response.status_code = 200
    return "OK"


@app.put(f"{SVC_HEADER}/config")
async def config_update(request: Request, response: Response):
    msg = await request.json()
    config.logger.debug(msg)
    if 'config' in msg:
        conf = msg['config']
        if 'MQTT_ID' in conf:
            config.id = conf['MQTT_ID']
            response.status_code = 200
            return "OK"
        elif 'MQTT_HOST' in conf:
            config.mqtt_broker = conf['MQTT_HOST']
            response.status_code = 200
            return "OK"
        elif 'MQTT_PORT' in conf:
            config.mqtt_port = conf['MQTT_PORT']
            response.status_code = 200
            return "OK"
        elif 'MQTT_PROTOCOL' in conf:
            config.mqtt_protocol = conf['MQTT_PROTOCOL']
            response.status_code = 200
            return "OK"
        elif 'MONITOR_PERIOD' in conf:
            config.monitor_period = conf['MONITOR_PERIOD']
            response.status_code = 200
            return "OK"
        elif 'REPORT_PERIOD' in conf:
            config.report_period = conf['REPORT_PERIOD']
            response.status_code = 200
            return "OK"
        elif 'CATEGORIES' in conf:
            config.categories = conf['CATEGORIES']
            response.status_code = 200
            return "OK"
        elif 'NET_IFACES' in conf:
            config.net_ifaces = conf['NET_IFACES']
            response.status_code = 200
            return "OK"
        elif 'RTT_SERVER' in conf:
            config.rtt_server = conf['RTT_SERVER']
            response.status_code = 200
            return "OK"

    config.logger.error("Bad json request")
    response.status_code = 400
    return "Bad json request"


# Trick to launch FastApi-uvicorn outside the main thread
class Server(uvicorn.Server):
    def install_signal_handlers(self):
        pass

    def start(self):
        thread = Thread(target=self.run, daemon=True)
        thread.start()
        while not self.started:
            time.sleep(1e-3)
