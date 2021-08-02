# Standard imports
import os
import re
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

                self.get_rtt(iface)
                self.get_throughput(iface, self.dict[iface]['rtt_ms'])

            except psutil.Error as exc:
                config.logger.error("Error reading interface {}: {}".format(iface, exc))

    def get_rtt(self, net_iface):
        command = f"ping -c 1 -w 1 -W 1 -I {net_iface} {config.rtt_server}"
        request = os.popen(command).read()
        request = re.search('=\\s(\\d+\\.\\d+)', request)
        rtt = float(request.group(1)) if request is not None else None
        self.dict[net_iface]['rtt_ms'] = float('{0:.2f}'.format(rtt)) if rtt is not None else None

    def get_throughput(self, net_iface, rtt_ms):
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
        self.dict[net_iface]['throughput'] = (min(rmem_max, tcp_rmem_max) / 1000000) / \
                                                 (rtt_ms / 1000) if rtt_ms is not None else None

    def monitor(self):
        while True:
            tic = time.time()
            self.get()
            elap_time = time.time() - tic
            time.sleep(config.monitor_period-elap_time)
