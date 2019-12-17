import socket
from loguru import logger as log
from time import sleep

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
client.bind(("", 37020))
while True:
    data, addr = client.recvfrom(1024)
    log.info("received broadcast: %s" % data)
    sleep(.1)
