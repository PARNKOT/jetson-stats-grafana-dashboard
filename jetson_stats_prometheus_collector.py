#!/usr/bin/python3
# -*- coding: utf-8 -*-

# MIT License
#
# Copyright (c) 2021 Stefan von Cavallar
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
import atexit
import argparse
from jtop import jtop, JtopException
from prometheus_client.core import InfoMetricFamily, GaugeMetricFamily, REGISTRY, CounterMetricFamily
from prometheus_client import start_http_server


class CustomCollector(object):
    def __init__(self):
        atexit.register(self.cleanup)
        self._jetson = jtop()
        self._jetson.start()

    def cleanup(self):
        print("Closing jetson-stats connection...")
        self._jetson.close()

    def collect(self):
        if self._jetson.ok():
            # print('emc: ', self._jetson.emc)
            # print('iram: ', self._jetson.iram)
            # print('mts: ', self._jetson.mts)

            #
            # Board info 
            #
            i = InfoMetricFamily('jetson_info_board', 'Board sys info', labels=['board_info'])
            i.add_metric(['info'], {
                'machine': self._jetson.board['platform']['Machine'],
                'distribution': self._jetson.board['platform']['Distribution'],
                'release': self._jetson.board['platform']['Release'],
                'jetpack': self._jetson.board['hardware']['Jetpack'], 
                'l4t': self._jetson.board['hardware']['L4T'],
                'module': self._jetson.board['hardware']['Module'],
                'type': self._jetson.board['hardware']['Model'],
                'codename': self._jetson.board['hardware']['Codename'],
                'soc': self._jetson.board['hardware']['SoC'],
                'cuda_arch_bin': self._jetson.board['hardware']['CUDA Arch BIN'],
                'serial_number': self._jetson.board['hardware']['Serial Number']
                })
            yield i

            #
            # NV power mode
            #
            i = InfoMetricFamily('jetson_nvpmode', 'NV power mode', labels=['nvpmode'])
            i.add_metric(['mode'], {'mode': self._jetson.nvpmodel.name})
            yield i

            #
            # System uptime 
            #
            g = GaugeMetricFamily('jetson_uptime', 'System uptime', labels=['uptime'])
            days = self._jetson.uptime.days
            seconds = self._jetson.uptime.seconds
            hours = seconds//3600
            minutes = (seconds//60) % 60
            g.add_metric(['days'], days)
            g.add_metric(['hours'], hours)
            g.add_metric(['minutes'], minutes)
            yield g

            #
            # CPU usage 
            #
            g = GaugeMetricFamily('jetson_usage_cpu', 'CPU % schedutil', labels=['cpu'])
            g.add_metric(['cpu_1'], self._jetson.cpu['cpu'][0]['freq']['cur'])
            g.add_metric(['cpu_2'], self._jetson.cpu['cpu'][1]['freq']['cur'])
            g.add_metric(['cpu_3'], self._jetson.cpu['cpu'][2]['freq']['cur'])
            g.add_metric(['cpu_4'], self._jetson.cpu['cpu'][3]['freq']['cur'])
            g.add_metric(['cpu_5'], self._jetson.cpu['cpu'][4]['freq']['cur'])
            g.add_metric(['cpu_6'], self._jetson.cpu['cpu'][5]['freq']['cur'])
            g.add_metric(['cpu_7'], self._jetson.cpu['cpu'][6]['freq']['cur'])
            g.add_metric(['cpu_8'], self._jetson.cpu['cpu'][7]['freq']['cur'])
            yield g

            # 
            # GPU usage
            #
            g = GaugeMetricFamily('jetson_usage_gpu', 'GPU % schedutil', labels=['gpu'])
            g.add_metric(['val'], self._jetson.gpu['gv11b']['status']['load'])
            # g.add_metric(['frq'], self._jetson.gpu['frq'])
            # g.add_metric(['min_freq'], self._jetson.gpu['min_freq'])
            # g.add_metric(['max_freq'], self._jetson.gpu['max_freq'])
            yield g

            # 
            # RAM usage
            #
            g = GaugeMetricFamily('jetson_usage_ram', 'Memory usage', labels=['ram'])
            g.add_metric(['used'], self._jetson.memory['RAM']['used'])
            g.add_metric(['shared'], self._jetson.memory['RAM']['shared'])
            g.add_metric(['total'], self._jetson.memory['RAM']['tot'])
            # g.add_metric(['unit'], self._jetson.ram['unit'])
            yield g

            # 
            # Disk usage
            #
            g = GaugeMetricFamily('jetson_usage_disk', 'Disk space usage', labels=['disk'])
            g.add_metric(['used'], self._jetson.disk['used'])
            g.add_metric(['total'], self._jetson.disk['total'])
            g.add_metric(['available'], self._jetson.disk['available'])
            g.add_metric(['available_no_root'], self._jetson.disk['available_no_root'])
            yield g

            # 
            # Fan usage
            #
            g = GaugeMetricFamily('jetson_usage_fan', 'Fan usage', labels=['fan'])
            g.add_metric(['speed'], self._jetson.fan['tegra_pwmfan']['speed'])
            g.add_metric(['rpm'], self._jetson.fan['tegra_pwmfan']['rpm'])
            # g.add_metric(['measure'], self._jetson.fan['measure'])
            # g.add_metric(['auto'], self._jetson.fan['auto'])
            # g.add_metric(['rpm'], self._jetson.fan['rpm'])
            # g.add_metric(['mode'], self._jetson.fan['mode'])
            yield g

            # 
            # Swapfile usage
            #
            g = GaugeMetricFamily('jetson_usage_swap', 'Swapfile usage', labels=['swap'])
            g.add_metric(['used'], self._jetson.memory['SWAP']['used'])
            g.add_metric(['total'], self._jetson.memory['SWAP']['tot'])
            # g.add_metric(['unit'], self._jetson.swap['unit'])
            # g.add_metric(['cached_size'], self._jetson.swap['cached']['size'])
            # g.add_metric(['cached_unit'], self._jetson.swap['cached']['unit'])
            yield g

            # 
            # Sensor temperatures
            #
            g = GaugeMetricFamily('jetson_temperatures', 'Sensor temperatures', labels=['temperature'])
            g.add_metric(['ao'], self._jetson.temperature['AO'] if 'AO' in self._jetson.temperature else 0)
            g.add_metric(['gpu'], self._jetson.temperature['GPU'] if 'GPU' in self._jetson.temperature else 0)
            g.add_metric(['tdiode'], self._jetson.temperature['Tdiode'] if 'Tdiode' in self._jetson.temperature else 0)
            g.add_metric(['aux'], self._jetson.temperature['AUX'] if 'AUX' in self._jetson.temperature else 0)
            g.add_metric(['cpu'], self._jetson.temperature['CPU'] if 'CPU' in self._jetson.temperature else 0)
            g.add_metric(['thermal'], self._jetson.temperature['thermal'] if 'thermal' in self._jetson.temperature else 0)
            g.add_metric(['tboard'], self._jetson.temperature['Tboard'] if 'Tboard' in self._jetson.temperature else 0)
            yield g

            # 
            # Power
            #
            g = GaugeMetricFamily('jetson_usage_power', 'Power usage', labels=['power'])
            g.add_metric(['cpu'], self._jetson.power['rail']['CPU']['power'] )
            g.add_metric(['cv'], self._jetson.power['rail']['CV']['power'] )
            g.add_metric(['gpu'], self._jetson.power['rail']['GPU']['power'] ) 
            g.add_metric(['soc'], self._jetson.power['rail']['SOC']['power'] )
            g.add_metric(['sys5v'], self._jetson.power['rail']['SYS5V']['power'] )
            g.add_metric(['vddrq'], self._jetson.power['rail']['VDDRQ']['power'] )
            yield g

            g = GaugeMetricFamily('jetson_usage_voltage_levels', 'Voltage', labels=['voltage'])
            g.add_metric(['cpu'], self._jetson.power['rail']['CPU']['volt'] ) 
            g.add_metric(['cv'], self._jetson.power['rail']['CV']['volt'] )
            g.add_metric(['gpu'], self._jetson.power['rail']['GPU']['volt'] ) 
            g.add_metric(['soc'], self._jetson.power['rail']['SOC']['volt'] )
            g.add_metric(['sys5v'], self._jetson.power['rail']['SYS5V']['volt'] )
            g.add_metric(['vddrq'], self._jetson.power['rail']['VDDRQ']['volt'] )
            yield g

            g = GaugeMetricFamily('jetson_usage_current_values', 'Current', labels=['current'])
            g.add_metric(['cpu'], self._jetson.power['rail']['CPU']['curr'] )
            g.add_metric(['cv'], self._jetson.power['rail']['CV']['curr'] )
            g.add_metric(['gpu'], self._jetson.power['rail']['GPU']['curr'] ) 
            g.add_metric(['soc'], self._jetson.power['rail']['SOC']['curr'] )
            g.add_metric(['sys5v'], self._jetson.power['rail']['SYS5V']['curr'] )
            g.add_metric(['vddrq'], self._jetson.power['rail']['VDDRQ']['curr'] )
            yield g


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000, help='Metrics collector port number')

    args = parser.parse_args()

    start_http_server(args.port)
    REGISTRY.register(CustomCollector())
    while True:
        time.sleep(1)
