#!/usr/bin/python3
"""KonnektBox Manager

Manages KonnektBox telemetry

Copyright (C) 2020 IKERLAN S.Coop
"""

# Standard imports
import argparse
import os
import re
import sys
import time
import json
import socket

# Installed packages
import yaml
import psutil
import cpuinfo
import paho.mqtt.publish as publish

# Constants
DEF_CONFIG_PATH = './config/config.yml'

def get_cpu_info(config):
    """ Gets CPU info """

    cinfo = {}

    # Information to be provided at monitoring start up only:
    if config['isfirst']:
        cinfo['model'] = cpuinfo.get_cpu_info()['brand']
        cinfo['cores_physical'] = psutil.cpu_count(logical=False)
        cinfo['cores_logical'] = psutil.cpu_count()

    # Get cpu usage in percentage:
    cinfo['cpu_usage'] = psutil.cpu_percent()
    cinfo['cpu_freq'] = psutil.cpu_freq()

    return cinfo

def get_disk_usage():
    """ Get disk usage in percentage """

    return psutil.disk_usage('/')[3]

def get_mem_info():
    """ Get mem usage and availability """

    minfo = {}
    mem_attr = psutil.virtual_memory()
    minfo['available_mem_MB'] = mem_attr.available/1000000
    minfo['mem_usage_MB'] = mem_attr.used/1000000

    return minfo

def get_netinterfaces_info(config):
    """ Gets information from network interfaces """

    info = {}
    pll_stats = psutil.net_io_counters(pernic=True)
    pernic_addr = psutil.net_if_addrs()

    for iface in config['monitor']['netinterfaces']:
        try:
            ninfo = {}
            if config['isfirst']:
                for addr in pernic_addr[iface]:
                    # Get IP address:
                    if addr.family == socket.AF_INET:
                        ninfo['ip'] = addr.address
                    # Get MAC address:
                    elif addr.family == psutil.AF_LINK:
                        ninfo['mac'] = addr.address

            # Get total/dropped packets and data volume
            ninfo['rx_MB'] = pll_stats[iface].bytes_recv/1000000
            ninfo['rx_packets'] = pll_stats[iface].packets_recv
            ninfo['rx_lost_packets'] = pll_stats[iface].dropin
            ninfo['tx_MB'] = pll_stats[iface].bytes_sent/1000000
            ninfo['tx_packets'] = pll_stats[iface].packets_sent
            ninfo['tx_lost_packets'] = pll_stats[iface].dropout

            # Get RTT to a certain endpoint via ICMP
            command = "ping -c 1 -w 1 -W 1 -I {} {}".format(iface, config['endpoint']['icmp_ping'])
            request = os.popen(command).read()
            request = re.search('=\\s(\\d+\\.\\d+)', request)
            if request is None:
                ninfo['rtt_ms'] = "ICMP request timeout"
            else:
                rtt = float(request.group(1))
                ninfo['rtt_ms'] = float('{0:.2f}'.format(rtt))
            info[iface] = ninfo
        except psutil.Error as exc:
            print("Error reading interface {}: {}".format(iface, exc))
    return info

def get_config(config, path):
    """ Return CONFIG read from CONFIG file (same CONFIG if file not changed) """

    if 'timestamp' in config:
        if config['timestamp'] == os.path.getmtime(path):
            return config

    with open(path, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit()
    config['timestamp'] = os.path.getmtime(path)
    return config

def get_params():
    """ Get console input parameters """

    parser = argparse.ArgumentParser(description='KonnektBox telemetry daemon.')
    parser.add_argument('-c', '--config', metavar='path', help='path of the config file')
    args = parser.parse_args()
    return args

def telemetry_get(config):
    """ Gets telemetry data """

    # Build JSON with telemetry data
    telemetry_data = {}
    telemetry_data['net_interfaces'] = get_netinterfaces_info(config)
    telemetry_data['cpu_info'] = get_cpu_info(config)
    telemetry_data['disk_usage'] = get_disk_usage()
    telemetry_data['mem_usage'] = get_mem_info()

    return telemetry_data

def telemetry_export(config, telemetry_data):
    """ Exports telemetry data """

    if config['export']['screen']['enabled']:
        print(json.dumps(telemetry_data, sort_keys=True, indent=4))
    if config['export']['mqtt']['enabled']:
        tls_cfg = None
        if config['export']['mqtt']['tls']['enabled']:
            tls_cfg = {'ca_certs':config['export']['mqtt']['tls']['ca'],
                       'certfile':config['export']['mqtt']['tls']['cert'],
                       'keyfile':config['export']['mqtt']['tls']['key']}
        publish.single(config['export']['mqtt']['topic'],
                       json.dumps(telemetry_data),
                       auth={
                           'username':config['export']['mqtt']['username'],
                           'password':config['export']['mqtt']['password']},
                       hostname=config['export']['mqtt']['hostname'],
                       tls=tls_cfg)
    if config['export']['file']['enabled']:
        with open(config['export']['file']['path'], 'w') as myfile:
#            myfile.write('{},{}\n'.format(time.time(), json.dumps(telemetry_data)))
            myfile.write('{}\n'.format(json.dumps(telemetry_data)))


def main():
    """ Main app """

    params = get_params()
    config_path = DEF_CONFIG_PATH
    if params.config:
        config_path = params.config
    conf = {}
    conf = get_config(conf, config_path)
    conf['isfirst'] = True

    while True:
        conf = get_config(conf, config_path) # Refresh config each interval
        data = telemetry_get(conf)
        telemetry_export(conf, data)
        conf['isfirst'] = False
        time.sleep(int(conf['monitor']['interval']))

main()
