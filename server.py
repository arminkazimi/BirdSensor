import socket
import json

PORT = 1234


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind((socket.gethostname(), PORT))
s.bind(('127.0.0.1', PORT))
s.listen(2)
print('waiting for client')
client_socket, address = s.accept()
print(f'connection from {address} has been successful!')


def identify_device(message):
    if message:
        data = {'command': 'IdentifyDevice'}
        return data
    else:
        data = {'command': 'findDevice'}
        return data


def read_data_once(message):
    if message:
        data = {'command': 'ReadDataOnce'}
        return data
    else:
        data = {'command': 'IdentifyDevice'}
        return data


def start_stream_data(message):
    if message:
        data = {'command': 'StartDataStream', 'data': {
            'limit': -1
        }}
        return data
    else:
        data = {'command': 'ReadDataOnce'}
        return data


i = 0
while True:
    i += 1
    print(i)
    data_dict = {
        'command': 'findDevice',
        'data': {
            'vendorID': '1422',
            'productID': '5014'
        }
    }
    json_object = json.dumps(data_dict)

    client_socket.sendall(bytes(json_object, 'utf-8'))
    msg = client_socket.recv(30)
    print(msg)
    if msg == 'true':
        message = True
        data = identify_device(message)
        json_object = json.dumps(data)
        client_socket.sendall(bytes(json_object, 'utf-8'))
    if msg == 'true':
        message = True
        data = identify_device(message)
        json_object = json.dumps(data)
        client_socket.sendall(bytes(json_object, 'utf-8'))

    if msg == '':
        print('connection closed')
        client_socket.close()
