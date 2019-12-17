import socket
import time

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
client.bind(("", 37030))
client.settimeout(5)
found = False
while not found:
    print("GSM Discover Broadcast Sent")
    client.sendto(b'GSM_DISCOVER', ('255.255.255.255', 37020))
    try:
        while not found:
            (data, addr) = client.recvfrom(1024)
            if data.decode() != 'GSM_DISCOVER':
                print(f'GSM Found: {data.decode()} ({addr[0]})')
                found = True
    except socket.timeout:
        pass
