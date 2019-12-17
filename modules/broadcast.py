import socket
import subprocess
from time import sleep

from loguru import logger as log


def get_ip_addr(ifname):
    return subprocess.getoutput("ip addr | grep wlan0 | grep inet")


def bcast():
    ipa1 = str(get_ip_addr('wlan0')).split('/')
    ipa2 = ipa1[0].split('inet ')
    ipaddr = ipa2[1]
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # client.settimeout(0.2)
    client.bind(("", 37020))
    while True:
        (data, addr) = client.recvfrom(1024)
        log.debug(f"Received Broadcast: {data.decode()} from {addr[0]}")
        if data.decode() == 'GSM_DISCOVER':
            server.sendto(ipaddr.encode(), ('255.255.255.255', 37030))
            log.debug(f'Sent GSM_DISCOVER response: {ipaddr}')

bcast()
