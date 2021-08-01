# Standard imports
import os
import re
import sys
import json
import time
import socket
import threading

# Modules
from modules.config import Config

# External packages
import psutil

config = Config()


class NetInfo:
    def __init__(self):
        self.dict = {}
        self.monitor_thread = threading.Thread(target=self.monitor, daemon=True)

    def start(self):
        self.monitor_thread.start()

    def get(self):
        """ Gets information from network interfaces """

        pll_stats = psutil.net_io_counters(pernic=True)
        pernic_addr = psutil.net_if_addrs()
        net_ifaces = json.loads(config.net_ifaces)
        print(pernic_addr.keys())
        print(net_ifaces['Active'])

        for iface in pernic_addr.keys() & net_ifaces['Active']:
            if iface not in self.dict.keys():
                self.dict[iface] = {}
            if 'rtt_ms' not in self.dict[iface]:
                self.dict[iface]['rtt_ms'] = {}

            try:
                # TODO: Only first iteration
                for addr in pernic_addr[iface]:
                    # Get IP address:
                    if addr.family == socket.AF_INET:
                        self.dict[iface]['ip'] = addr.address
                    # Get MAC address:
                    elif addr.family == psutil.AF_LINK:
                        self.dict[iface]['mac'] = addr.address

                # Get total/dropped packets and data volume
                self.dict[iface]['rx_MB'] = pll_stats[iface].bytes_recv / 1000000
                self.dict[iface]['rx_packets'] = pll_stats[iface].packets_recv
                self.dict[iface]['rx_lost_packets'] = pll_stats[iface].dropin
                self.dict[iface]['tx_MB'] = pll_stats[iface].bytes_sent / 1000000
                self.dict[iface]['tx_packets'] = pll_stats[iface].packets_sent
                self.dict[iface]['tx_lost_packets'] = pll_stats[iface].dropout

                command = f"ping -c 1 -w 1 -W 1 -I {iface} {config.rtt_server}"
                request = os.popen(command).read()
                request = re.search('=\\s(\\d+\\.\\d+)', request)
                rtt = float(request.group(1)) if request is not None else None
                self.dict[iface]['rtt_ms'] = float('{0:.2f}'.format(rtt)) if rtt is not None else None

                try:
                    with open("/proc/sys/net/core/rmem_max", 'r') as f:
                        rmem_max = int(f.readline())
                except IOError as e:
                    raise ReadError(e.strerror, e.filename)
                try:
                    with open("/proc/sys/net/ipv4/tcp_rmem", 'r') as f:
                        tcp_rmem_line = f.readline()
                        tcp_rmem_list = tcp_rmem_line.split()
                        tcp_rmem_max = int(tcp_rmem_list[2])
                except IOError as e:
                    raise ReadError(e.strerror, e.filename)
                self.dict[iface]['throughput_avg'] = (min(rmem_max, tcp_rmem_max) / 1000000) / \
                    (self.dict[iface]['rtt_ms'] / 1000) if rtt is not None else None

            except psutil.Error as exc:
                config.logger.error("Error reading interface {}: {}".format(iface, exc))

    def monitor(self):
        while True:
            tic = time.time()
            self.get()
            elap_time = time.time() - tic
            time.sleep(config.monitor_period-elap_time)

    def get_avg(self):
        """ Averages information from network interfaces """

        try:
            peers = json.loads(config.monitor_peers)

            for iface in self.dict.keys():
                if iface not in peers.keys():
                    del self.dict[iface]
                else:
                    for peer in self.dict[iface]['rtt_ms'].keys():
                        if peer not in peers[iface]:
                            del self.dict[iface]['rtt_ms'][peer]
                            del self.dict[iface]['rtt_avg'][peer]
                            del self.dict[iface]['throughput_avg'][peer]

            for iface in peers.keys():
                if iface not in self.dict.keys():
                    self.dict[iface] = {}
                if 'rtt_avg' not in self.dict[iface]:
                    self.dict[iface]['rtt_avg'] = {}
                if 'throughput_avg' not in self.dict[iface]:
                    self.dict[iface]['throughput_avg'] = {}

                for peer in peers[iface]:
                    if not self.dict[iface]['rtt_ms'][peer]:
                        self.dict[iface]['rtt_avg'][peer] = sys.float_info.max
                    else:
                        try:
                            self.dict[iface]['rtt_avg'][peer] = sum(self.dict[iface]['rtt_ms'][peer]) /\
                                                                len(self.dict[iface]['rtt_ms'][peer])
                        except ZeroDivisionError as e:
                            config.logger.error("Math. error: {}".format(e))

                        self.dict[iface]['rtt_ms'][peer] = []
                        try:
                            with open("/proc/sys/net/core/rmem_max", 'r') as f:
                                rmem_max = int(f.readline())
                        except IOError as e:
                            raise ReadError(e.strerror, e.filename)
                        try:
                            with open("/proc/sys/net/ipv4/tcp_rmem", 'r') as f:
                                tcp_rmem_line = f.readline()
                                tcp_rmem_list = tcp_rmem_line.split()
                                tcp_rmem_max = int(tcp_rmem_list[2])
                        except IOError as e:
                            raise ReadError(e.strerror, e.filename)
                        self.dict[iface]['throughput_avg'][peer] = (min(rmem_max, tcp_rmem_max) / 1000000) /\
                                                                   (self.dict[iface]['rtt_avg'][peer] / 1000)

        except Exception as e:
            config.logger.error(
                "Exception parsing list of links: {} ".format(e), exc_info=True
            )
