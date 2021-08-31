# Telemetry Analytics

This repo contains a python app to monitor and manage the telemetry of Edge devices. A Grafana dashboard for Jetson devices is also provided

## Requirements
This util can be executed with just an active installation of Docker and Docker Compose.

## Configuration
The module can be configure using the following environment variables:
- MQTT_ID
- MQTT_HOST
- MQTT_PORT
- MQTT_PROTOCOL
- REST_PORT
- MONITOR_PERIOD (seconds)
- CATEGORIES, e.g. {"Active":["CPU", "Disk", "Mem", "Net", "Tegra"]}
- NET_IFACES, e.g. {"Active":["eth0", "wlan0"]}
- RTT_SERVER 

## Usage
Execute the app using:
```
docker-compose up --build
```

## Dashboard
The included Compose provides additional components for Grafana visualization with a built-in dashboard for NVIDIA Jetson TX2 and Jetson Nano devices. In order to access the dashboard, go to http://device-IP:3000 using any web browser 
