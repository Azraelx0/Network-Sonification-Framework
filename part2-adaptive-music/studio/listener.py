import socket

PORT = 9500
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PORT))
print(f"Listening for messages on UDP port {PORT}...")

while True:
    data, addr = sock.recvfrom(4096)
    print(f"From {addr[0]}: {data.decode()}")