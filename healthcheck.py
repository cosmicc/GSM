#!/usr/bin/env python3.8

import argparse
import socket
import struct
import subprocess
import sys
from os import _exit as exit
from pathlib import Path
from time import sleep

from loguru import logger as log

logfile = '/var/log/healthcheck.log'
statusfile = Path('/media/mmcblk0p2/host.status')

parser = argparse.ArgumentParser(prog='GSM')
parser.add_argument('-c', '--console', action='store_true', help='supress logging output to console. default: error logging')
parser.add_argument('-d', '--debug', action='store_true', help='extra verbose output (debug)')
parser.add_argument('--checknow', action='store_true', help='Single Check now')
args = parser.parse_args()

if args.debug:
    loglevel = "DEBUG"
else:
    loglevel = "WARNING"

if args.console:
    log.configure(
        handlers=[dict(sink=sys.stdout, level=loglevel, backtrace=True, format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'),
                  dict(sink=logfile, level="INFO", enqueue=True, serialize=False, rotation="1 MB", retention="14 days", compression="gz")],
        levels=[dict(name="STARTUP", no=38, icon="¤", color="<yellow>")], extra={"common_to_all": "default"}, activation=[("my_module.secret", False), ("another_library.module", True)])
else:
    log.configure(
        handlers=[dict(sink=sys.stderr, level="CRITICAL", backtrace=True, format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'),
                  dict(sink=logfile, level="INFO", enqueue=True, serialize=False)],
        levels=[dict(name="STARTUP", no=38, icon="¤", color="<yellow>")], extra={"common_to_all": "default"}, activation=[("my_module.secret", False), ("another_library.module", True)])


def is_host_up(host):
    response = subprocess.run(["/usr/sbin/fping", host], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if response.returncode == 0:
        return True
    else:
        log.debug(f'Host {host} is not reachable')
        return False


def get_gateway():
    with open("/proc/net/route") as fh:
        for line in fh:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                continue
            return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))


def get_ip_addr():
    ip1 = subprocess.getoutput("ip addr | grep wlan0 | grep inet")
    ip2 = str(ip1).split('/')
    ip3 = ip2[0].split('inet ')
    return ip3[1]


def get_wifi_info():
    child = subprocess.Popen(['iwconfig'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=False)
    streamdata = child.communicate()[0].decode('UTF-8').split('\n')
    if child.returncode == 0:
        for each in streamdata:
            if each.find('ESSID:') != -1:
                ssid = each.split(':')[1].replace('"', '').strip()
            elif each.find('Frequency') != -1:
                apmac = each.split('Access Point: ')[1].strip()
                channel = each.split('Frequency:')[1].split(' Access Point:')[0].strip()
            elif each.find('Link Quality') != -1:
                linkqual = each.split('=')[1].split(' Signal level')[0].strip()
                signal = int(each.split('=')[2].split(' ')[0].strip())
                # -80 -30  0 100
                signal_percent = int(0 + (100 - 0) * ((signal - -80) / (-35 - -80)))
                if signal_percent > 100:
                    signal_percent = 100
            elif each.find('Bit Rate') != -1:
                bitrate = each.split('=')[1].split('Tx-Power')[0].strip()

        return {'ssid': ssid, 'apmac': apmac, 'channel': channel, 'signal': signal, 'signal_percent': signal_percent, 'quality': linkqual, 'bitrate': bitrate}
    else:
        return False


if args.checknow:
    print(f'IP: {get_ip_addr()}')
    print(f'GATEWAY: {get_gateway()}')
    print(f'GATEWAY REACHABLE: {is_host_up(get_gateway())}')
    print(f'INTERNET REACHABLE: {is_host_up("1.1.1.1")}')
    print(f'VPN REACHABLE: {is_host_up("172.25.1.10")}')
    print(f'WIFI INFO: {get_wifi_info()}')
    exit(0)

loop = 0
gatewaymissed = 0

log.info(f'Starting host health monitor')

log.debug('Getting last status')
if statusfile.exists():
    laststatus = statusfile.read_text()
    log.warning(f'Last status exists: {laststatus}')
else:
    log.debug('No last status exists')


while True:
    if is_host_up(get_gateway()):
        sleep(60)
    else:
        if not get_ip_addr():
            gatewaymissed += 1



