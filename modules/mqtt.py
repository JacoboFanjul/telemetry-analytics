import paho.mqtt.client as mqtt
from modules.config import Config
from threading import Thread
import time

WILL = '{"dead": true}'
DEF_QOS = 0

config = Config()


def on_connect(client, userdata, flags, ret):
    """ Connect Callback """

    if ret == 0:
        config.logger.info(f"MQTT Client connected to Broker at {client.endpoint[0]}:{client.endpoint[1]}")
    else:
        config.logger.error(f"MQTT Connect Error st: {ret} flags: {flags}")


def on_disconnect(client, userdata, rc):
    config.logger.error(
        "MQTT Broker connection lost. Trying to reconnect in background..."
    )


class MqttClient:
    def __init__(self):

        # Set internal variables
        device_id = config.id
        self.endpoint = (config.mqtt_broker, config.mqtt_port)
        self.telemetry_topic = f"jjsmarthome/v1/devices/{device_id}/telemetry"

        # Init Thread
        self.mqtt_thr = Thread(target=self.mqtt_thr_cbk)
        self.mqtt_thr.daemon = True

        # Init MQTT client
        self.mqtt_cli = mqtt.Client(device_id)
        self.mqtt_cli.on_message = on_message
        self.mqtt_cli.on_connect = on_connect
        self.mqtt_cli.on_disconnect = on_disconnect
        self.mqtt_cli.username_pw_set(device_id, password="")
        self.mqtt_cli.will_set(self.telemetry_topic, WILL, 1)
        self.mqtt_cli.user_data_set(self)
        self.connection_failed = False

        if config.mqtt_protocol == "tls":
            # TODO
            pass

    def start(self):
        """ Starts MQTT Client """

        self.mqtt_thr.start()
        while not self.mqtt_cli.is_connected():
            config.logger.info("Waiting for connection to MQTT Broker ...")
            if self.connection_failed:
                config.logger.error(
                    "Connection to MQTT Broker {}:{} failed".format(
                        self.endpoint[0], self.endpoint[1]
                    )
                )
                exit(1)
            time.sleep(1)

    def stop(self):
        """ Stops MQTT Client """

        self.mqtt_cli.disconnect()

    def send(self, data, topic):
        """ Sends data """

        ret = self.mqtt_cli.publish(topic, data, DEF_QOS)
        if ret.rc == mqtt.MQTT_ERR_SUCCESS:
            config.logger.debug(f"Msg {data} sent to topic {topic}")
            return True

        config.logger.debug(f"Msg {data} could not be sent to topic {topic}")
        return False

    def mqtt_thr_cbk(self):
        """ Runs MQTT client in its own thread """
        try:
            self.mqtt_cli.connect(self.endpoint[0], self.endpoint[1], 60)
        except BaseException:
            self.connection_failed = True
            exit(1)
        self.mqtt_cli.loop_forever(retry_first_connection=True)
