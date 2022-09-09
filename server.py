import socket
import json

PORT = 1234
VENDOR_ID = '1422'
PRODUCT_ID = '5014'
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind((socket.gethostname(), PORT))
s.bind(('127.0.0.1', PORT))
s.listen(2)
print('waiting for client')

#  TODO run client.exe

client_socket, address = s.accept()
print(f'connection from {address} has been successful!')


def find_device(vendor_id=VENDOR_ID, product_id=PRODUCT_ID):
    data = data_dict = {
        'command': 'findDevice',
        'data': {
            'vendorID': vendor_id,
            'productID': product_id
        }
    }
    return data


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


# TODO RUN TEREAD
json_data = {}
while True:

    data_dict = find_device
    json_object = json.dumps(data_dict)

    client_socket.sendall(bytes(json_object, 'utf-8'))
    msg = client_socket.recv(30)

    print(msg)
    if msg == 'find_true':
        message = True
        data = identify_device(message)
        json_object = json.dumps(data)
        client_socket.sendall(bytes(json_object, 'utf-8'))
    if msg == 'identify_true':
        message = True
        data = read_data_once(message)
        json_object = json.dumps(data)
        client_socket.sendall(bytes(json_object, 'utf-8'))
    if msg == 'read_data_once_true':
        message = True
        data = start_stream_data(message)
        json_object = json.dumps(data)
        client_socket.sendall(bytes(json_object, 'utf-8'))
        msg = client_socket.recv(30)
    if json_data:

        print(json_data)
        json_object = json.dumps(data)
        client_socket.sendall(bytes(json_object, 'utf-8'))
    if msg == 'disconnect':
        print('connection closed')
        client_socket.close()
