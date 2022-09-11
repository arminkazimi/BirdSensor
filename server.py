import sys
import threading
import socket
import json
import time
import keyboard
import os
import subprocess
from pynput import keyboard

PORT = 1234
HOST = '127.0.0.1'
# VENDOR_ID = '1422'
# PRODUCT_ID = '5014'
VENDOR_ID = '0909'
PRODUCT_ID = '0051'
CLIENT_PATH = 'cs_app\\PowerBird.exe'


class myApp:
    def __init__(self):
        self.port = PORT
        self.vendor_id = VENDOR_ID
        self.product_id = PRODUCT_ID
        self.client_path = CLIENT_PATH
        self.host = HOST
        self.quit_app = False
        self.disconnect = False
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket, self.address = None, None

    def start_app(self):
        keyboard_listener_thread = threading.Thread(target=self.keyboard_listener)
        keyboard_listener_thread.start()

        self.run_socket_server()

        # client_app_thread = threading.Thread(target=self.execute_client_app)
        # client_app_thread.start()

        communicate_thread = threading.Thread(target=self.communicate)
        communicate_thread.start()

    def on_press(self, key):
        if key == keyboard.Key.esc:
            self.quit_app = True
            return False
            # stop listener

        try:
            k = key.char  # single-char keys
            print(k)
        except:
            k = key.name  # other keys
            print(k)
        if k in ['d']:  # keys of interest
            # self.keys.append(k)  # store it in global-like variable
            print('Key pressed: ' + k)
            self.disconnect = True
            return False  # stop listener; remove this if want more keys

    def keyboard_listener(self):
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()  # start to listen on a separate thread
        listener.join()

    def execute_client_app(self):
        try:
            subprocess.Popen(self.client_path)
            print('client is running...')
        except Exception as e:
            print('execute client app error: ', e)

    def run_socket_server(self):
        self.my_socket.bind((self.host, self.port))
        self.my_socket.listen(2)

    def accept_socket_client(self):
        if not self.client_socket:
            print('waiting for client...')
            try:
                self.client_socket, self.address = self.my_socket.accept()
                print(f'connection from {self.address} has been successful!')
            except Exception as e:
                print('accepting client error: ', e)
        else:
            print(f'There is connection from {self.address} has not closed yet')

    def communicate(self):

        while True:
            self.accept_socket_client()
            req_data = find_device()
            json_object = json.dumps(req_data)

            self.client_socket.sendall(bytes(json_object, 'utf-8'))
            msg = self.client_socket.recv(30)

            json_string = msg.decode('utf-8')
            res_data = json.loads(json_string)
            print(res_data)
            if res_data.get('find'):
                message = True
                data = identify_device(message)
                json_object = json.dumps(data)
                self.client_socket.sendall(bytes(json_object, 'utf-8'))
            if res_data.get('identify'):
                message = True
                data = read_data_once(message)
                json_object = json.dumps(data)
                self.client_socket.sendall(bytes(json_object, 'utf-8'))
            if res_data.get('read_data_once'):
                message = True
                data = start_stream_data(message)
                json_object = json.dumps(data)
                self.client_socket.sendall(bytes(json_object, 'utf-8'))
                msg = self.client_socket.recv(30)

            if self.quit_app:
                self.send_close_message()

                self.client_socket.close()
                # self.kill_client_exe()

                # self.client_socket = None
                time.sleep(2)
                print('quit the app')
                sys.exit()

            if res_data.get('disconnect') or self.disconnect:
                self.send_close_message()
                # self.client_socket.shutdow()
                self.client_socket.close()
                print('closed connection',self.client_socket)
                # self.client_socket = None
                print('connection closed')
                # time.sleep(2)
            print(self.client_socket)
            time.sleep(2)

    def send_close_message(self):
        data = {'command': 'exit'}
        return data

    def kill_client_exe(self):
        try:
            subprocess.call(['taskkill', '/IM', 'PowerBird.exe', '/F'])
        except BaseException as e:
            print('killing exe file exception:', e)


# def on_press(key):
#     if key == keyboard.Key.esc:
#         global my_quit
#         my_quit == True
#         return True
#         # stop listener
#     try:
#         k = key.char  # single-char keys
#         print(k)
#     except:
#         k = key.name  # other keys
#         print(k)
#     # if k in ['1', '2', 'left', 'right']:  # keys of interest
#     #     # self.keys.append(k)  # store it in global-like variable
#     #     print('Key pressed: ' + k)
#     #     return False  # stop listener; remove this if want more keys
#
#
# def commands():
#     listener = keyboard.Listener(on_press=on_press)
#     listener.start()  # start to listen on a separate thread
#     listener.join()


# command_thread = threading.Thread(target=commands)
# command_thread.start()

# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# # s.bind((socket.gethostname(), PORT))
# s.bind(('127.0.0.1', PORT))
# s.listen(1)
# print('waiting for client...')
# client_thread = threading.Thread(target=execute_client)
# client_thread.start()

#  TODO run client.exe

# client_socket, address = s.accept()
# print(f'connection from {address} has been successful!')


def find_device(vendor_id=VENDOR_ID, product_id=PRODUCT_ID):
    data = data_dict = {
        'command': 'findDevice',
        'data': {
            'vendorID': vendor_id,
            'productID': product_id
        }
    }
    return data

def find_and_identify(vendor_id=VENDOR_ID, product_id=PRODUCT_ID):
    data = data_dict = {
        'command': 'FindAndIdentify',
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


# def do_while(function, message):
#     if message == 'find':
#         req_data = find_device()
#     # elif
#     json_object = json.dumps(req_data)
#     while True:
#         print(json_object)
#         client_socket.sendall(bytes(json_object, 'utf-8'))
#         msg = client_socket.recv(30)
#         json_string = msg.decode('utf-8')
#         res_data = json.loads(json_string)
#         print(res_data)
#         if res_data.get('find'):
#             req_data = identify_device(True)
#             json_object = json.dumps(req_data)
#             break


def do_sensor(client_socket):
    req_data = find_device()
    json_object = json.dumps(req_data)
    while True:
        print(json_object)
        client_socket.sendall(bytes(json_object, 'utf-8'))
        msg = client_socket.recv(30)
        json_string = msg.decode('utf-8')
        res_data = json.loads(json_string)
        print(res_data)
        if res_data.get('find'):
            req_data = identify_device(True)
            json_object = json.dumps(req_data)
            break

    while True:
        print(json_object)
        client_socket.sendall(bytes(json_object, 'utf-8'))
        msg = client_socket.recv(30)
        json_string = msg.decode('utf-8')
        res_data = json.loads(json_string)
        print(res_data)
        if res_data.get('identify'):
            req_data = read_data_once(True)
            json_object = json.dumps(req_data)
            break


my_app = myApp()
my_app.start_app()
