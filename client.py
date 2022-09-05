import socket
import time

PORT = 1234

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(socket.gethostname())
s.connect((socket.gethostname(), PORT))

while True:
    print(s.recv(3))
    time.sleep(5)
    s.send(bytes('command received', 'utf-8'))
#     do anything
