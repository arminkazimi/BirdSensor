import socket
import json
PORT = 1234
HEADER_SIZE = 10

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('127.0.0.1', PORT))
s.listen(2)
print('waiting for client')
client_socket, address = s.accept()
print(f'connection from {address} has been successful!')
while True:

    data_dict = {
        'command': 'findDevice',
        'data': {
            'vendorID': '1422',
            'productID': '5014'
        }
    }
    json_object = json.dumps(data_dict)
    client_socket.sendall(bytes(json_object,'utf-8'))
    msg = client_socket.recv(30)
    print(msg)
    if msg == '':
        print('connection closed')
        client_socket.close()
