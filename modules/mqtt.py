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
        client.subscribe(userdata.peers_topic)
        config.logger.info(
            "MQTT Client connected and subscribed to {} topic".format(
                userdata.peers_topic
            )
        )
    else:
        config.logger.error("MQTT Connect Error st: {} flags: {}".format(ret, flags))


def on_message(client, userdata, message):
    """ Callback """

    config.logger.info("MQTT message arrived: {}".format(message.payload))
    config.monitor_peers = message.payload


def on_disconnect(client, userdata, rc):
    config.logger.error(
        "MQTT Broker connection lost. Trying to reconnect in background..."
    )


class MqttClient:
    def __init__(self):

        # Set internal variables
        box_id = config.id
        self.endpoint = (config.mqtt_broker, config.mqtt_port)
        self.telemetry_topic = "konnekt/v3/service/konnektbox-telemetry"
        self.peers_topic = "konnekt/v3/service/konnektbox-telemetry/peers"

        # Init Thread
        self.mqtt_thr = Thread(target=self.mqtt_thr_cbk)
        self.mqtt_thr.daemon = True

        # Init MQTT client
        self.mqtt_cli = mqtt.Client(box_id)
        self.mqtt_cli.on_message = on_message
        self.mqtt_cli.on_connect = on_connect
        self.mqtt_cli.on_disconnect = on_disconnect
        self.mqtt_cli.username_pw_set(box_id, password="")
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
            config.logger.debug("Msg {} sent to topic {}".format(data, topic))
            return True

        config.logger.debug("Msg {} could not be sent to topic {}".format(data, topic))
        return False

    def mqtt_thr_cbk(self):
        """ Runs MQTT client in its own thread """
        try:
            self.mqtt_cli.connect(self.endpoint[0], self.endpoint[1], 60)
        except BaseException:
            self.connection_failed = True
            exit(1)
        self.mqtt_cli.loop_forever(retry_first_connection=True)
