import socket
from loguru import logger as log
from time import sleep
import fcntl
import os
import struct
import subprocess


def get_ip_addr(ifname):
    return subprocess.getoutput("ip addr | grep wlan0 | grep inet")

def bcast():
    ipa1 = str(get_ip_addr('wlan0')).split('/')
    ipa2 = ipa1[0].split('inet ')
    ipaddr = ipa2[1]
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #client.settimeout(0.2)
    client.bind(("", 37020))
    while True:
        (data, addr) = client.recvfrom(1024)
        if not len(data):
            sleep(1)
            break
        log.debug(f"Received Broadcast: {data.decode()}")
        if data.decode() == 'GSM_DISCOVER':
            client.sendto(ipaddr.encode(), ('255.255.255.255', 37030))
            log.debug(f'Sent GSM_DISCOVER response: {ipaddr}')
        sleep(1)
