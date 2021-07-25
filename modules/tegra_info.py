# Standard imports
import os
import re
import time
import threading

# Modules
from modules.config import Config

# External packages

# Config parameters and globals
config = Config()


class TegraInfo:
    def __init__(self):
        self.dict = {'cpu_usage': []}
        self.monitor_thread = threading.Thread(target=self.monitor, daemon=True)

    def start(self):
        self.monitor_thread.start()

    def parse(self, line):

        ram_raw = re.findall(r'RAM ([0-9]*)\/([0-9]*)MB \(lfb ([0-9]*)x([0-9]*)MB\)', line)
        ram = ram_raw[0] if ram_raw else None
        self.dict['RAM_usage_MB'] = float(ram[0]) if ram else None
        self.dict['RAM_available_MB'] = float(ram[1]) - float(ram[0]) if ram else None

        swap_raw = re.findall(r'SWAP ([0-9]*)\/([0-9]*)MB \(cached ([0-9]*)MB\)', line)
        #swap = swap_raw[0] if swap_raw else None
        #self.dict['swap_usage_MB'] = float(swap[0]) if swap else None
        #self.dict['swap_available_MB'] = float(swap[1]) - float(swap[0]) is swap else None
        #self.dict['swap_cached_MB'] = float(swap[2]) if swap else None

        iram_raw = re.findall(r'IRAM ([0-9]*)\/([0-9]*)kB \(lfb ([0-9]*)kB\)', line)
        iram = iram_raw[0] if iram_raw else None
        self.dict['IRAM_usarge_kB'] = float(iram[0]) if iram else None
        self.dict['IRAM_available_kB'] = float(iram[1]) - float(iram[0]) if iram else None

        cpus_raw = re.findall(r'CPU \[(.*)\]', line)
        cpus = cpus_raw[0] if cpus_raw else None
        frequency = re.findall(r'@([0-9]*)', cpus)
        self.dict['cpu_freq_MHz'] = float(frequency[0]) if frequency else ''
        for i, cpu in enumerate(cpus.split(',')):
            self.dict[f'cpu_{i}_usage_%'] = cpu.split('%')[0]

        ape = re.findall(r'APE ([0-9]*)', line)
        self.dict['ape_freq_MHz'] = float(ape[0]) if ape else None

        gr3d_raw = re.findall(r'GR3D_FREQ ([0-9]*)%@?([0-9]*)?', line)
        gr3d = gr3d_raw[0] if gr3d_raw else None
        self.dict['gr3d_usage_%'] = float(gr3d[0]) if gr3d else None
        self.dict['gr3d_freq_MHz)'] = float(gr3d[1]) if gr3d[1] else ''

        emc_raw = re.findall(r'EMC_FREQ ([0-9]*)%@?([0-9]*)?', line)
        emc = emc_raw[0] if emc_raw else None
        self.dict['emc_usage_%'] = float(emc[0]) if emc else None
        self.dict['emc_freq_MHz'] = float(emc[1]) if emc else ''

        nvenc = re.findall(r'NVENC ([0-9]*)', line)
        self.dict['nvenc_freq_MHz'] = float(nvenc[0]) if nvenc else None

        mts = re.findall(r'MTS fg ([0-9]*)% bg ([0-9]*)%', line)  # !!!!

        temperatures = re.findall(r'([A-Za-z]*)@([0-9.]*)C', line)
        vdds = None

        if temperatures:
            for label, temperature in temperatures:
                self.dict[f'{label}_temp_C'] = float(temperature)
            substring = line[(line.rindex(temperatures[-1][1] + "C") + len(temperatures[-1][1] + "C")):]
            vdds = re.findall(r'([A-Za-z0-9_]*) ([0-9]*)\/([0-9]*)', substring)
        else:
            vdds = re.findall(r'VDD_([A-Za-z0-9_]*) ([0-9]*)\/([0-9]*)', line)
        for label, curr_vdd, avg_vdd in vdds:
            self.dict[f'{label}_power_consumption_mW'] = float(curr_vdd)
            self.dict[f'avg_{label}_power_consumption_mW'] = float(avg_vdd)

    def get(self):
        command = "./tegrastats"
        request = os.popen(command).read()
        command = "tegrastats --stop"
        os.system(command)
        self.parse(request) if request else config.logger.error('Tegrastats output could not be parsed')

    def monitor(self):
        while True:
            tic = time.time()
            self.get()
            elap_time = time.time() - tic
            time.sleep(config.monitor_period-elap_time)
