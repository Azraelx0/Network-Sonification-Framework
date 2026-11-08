import socket

PC_IP = "192.168.1.212"
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(b"hello from the sensor", (PC_IP, 9500))
print("Sent.")
