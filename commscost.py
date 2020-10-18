#!/usr/bin/python3
"""KonnektBox Manager

Obtains the communication cost of an application

Copyright (C) 2020 IKERLAN S.Coop
"""

# Standard imports
import argparse
import os
#import re
import sys
import time
import json
import math
#import socket

# Installed packages
import yaml
#import psutil
#import cpuinfo
#import paho.mqtt.publish as publish

# Constants
DEF_CONFIG_PATH = './config/commscost-config.yml'
DEF_APPINFO_PATH = './files/app-info.yml'
DEF_APPATTR_PATH = './files/app-attr.yml'

def get_params():
    """ Get console input parameters """

    parser = argparse.ArgumentParser(description='KonnektBox telemetry daemon.')
    parser.add_argument('-c', '--config', metavar='path', help='path of the config file')
    args = parser.parse_args()
    return args

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

def get_telemetry(config):
    """ Return telemetry_data read from output file (TODO: get data via MQTT) """

    if config['import']['file']['enabled']:
        with open(config['import']['file']['path'], 'r') as stream:
            try:
                telemetry_data = json.load(stream)
            except ValueError as exc:
                print(exc)
                sys.exit()
    return telemetry_data

def get_appinfo(path):
    """ Load info/attributes from a YAML file"""
    with open(path, 'r') as stream:
        try:
            appinfo = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit()
    return appinfo

def get_cost(ninfo, app_attr, app_info):
    """ Return the communication cost for every application """

    cost = {}
    for app in app_info:
        infonat = app_info[app]['infoNature']
        iface = app_attr[infonat]['iface']
        bal = float(app_attr[infonat]['balance'])
        rttmax = float(app_attr[infonat]['rttmax'])
        pllmax = float(app_attr[infonat]['pllmax'])
        try:
            rtt = float(ninfo[iface]['rtt_ms'])
            total_packets = float(ninfo[iface]['rx_packets'] + ninfo[iface]['tx_packets'])
            total_lost = float(ninfo[iface]['rx_lost_packets'] + ninfo[iface]['tx_lost_packets'])
            pll = total_lost / total_packets
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit()
        try:
            cost[app] = ((float(app_attr[infonat]['priority']) / float(app_attr[infonat]['norm']))
                         - (bal*math.log(max(0, (1-(rtt/rttmax))))
                            + (1-bal)*math.log(max(0, (1-(pll/pllmax))))))
        except ValueError as exc:
            print(exc)
            cost[app] = math.inf
            return -1
    print(cost)
    return cost

def check_thres(ninfo, app_attr):
    """ Check if comms thresholds are satisfied at device level """

    devrttmax = float(app_attr['devLevel']['rttmax'])
    devpllmax = float(app_attr['devLevel']['pllmax'])

    for iface in ninfo:
        if ninfo[iface]['rtt_ms'] == 'ICMP request timeout':
            return -1
        try:
            rtt = float(ninfo[iface]['rtt_ms'])
            total_packets = float(ninfo[iface]['rx_packets'] + ninfo[iface]['tx_packets'])
            total_lost = float(ninfo[iface]['rx_lost_packets'] + ninfo[iface]['tx_lost_packets'])
            pll = total_lost / total_packets
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit()
        if ((rtt >= devrttmax) or (pll >= devpllmax)):
            return 1
    return 0


def main():
    """ Main app """

    params = get_params()
    config_path = DEF_CONFIG_PATH
    if params.config:
        config_path = params.config
    conf = {}
    conf = get_config(conf, config_path)
    apps = get_appinfo(DEF_APPINFO_PATH)
    attr = get_appinfo(DEF_APPATTR_PATH)

    while True:
        conf = get_config(conf, config_path) # Refresh config each interval
        data = get_telemetry(conf)
        # print(json.dumps(data, sort_keys=True, indent=4))
        thres_violation = check_thres(data['net_interfaces'], attr)
        if thres_violation == -1:
            print('Could not obtain comms. attributes')
        elif thres_violation == 1:
            print('Comms. requirements not satisfied')
            costs = get_cost(data['net_interfaces'], attr, apps)
            print(costs)
            markedapp = max(costs)
            apps[markedapp]['active'] = False
            print(markedapp)
        else:
            print('Up and running')

        time.sleep(int(conf['monitor']['interval']))

main()
