import sys
import threading
import socket
import json
import time
import keyboard
import os
import subprocess
from pynput import keyboard

PRODUCTION = False

VENDOR_ID = '0909'
PRODUCT_ID = '0051'

DATA_LIMIT = True
DATA_COUNT = 20

PORT = 1234
HOST = '127.0.0.1'
# VENDOR_ID = '1422'
# PRODUCT_ID = '5014'
CLIENT_PATH = 'cs_app\\PowerBird.exe'
LOG_FILE_PATH = 'client_log.txt'


class myApp:
    def __init__(self):
        self.state = {'find': False,
                      'identify': False,
                      'findAndIdentify': False,
                      'readDataOnce': False,
                      'stopDataStream': False,
                      'startDataStream': False,
                      'exit': False
                      }
        self.data_property = {
            'limit': DATA_LIMIT,
            'count': DATA_COUNT
        }
        self.port = PORT
        self.vendor_id = VENDOR_ID
        self.product_id = PRODUCT_ID
        self.client_path = CLIENT_PATH
        self.log_path = LOG_FILE_PATH
        self.host = HOST
        self.quit_app = False
        self.disconnect = False
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket, self.address = None, None

    def start_app(self):
        keyboard_listener_thread = threading.Thread(target=self.keyboard_listener)
        keyboard_listener_thread.start()

        self.run_socket_server()
        if PRODUCTION:
            client_app_thread = threading.Thread(target=self.execute_client_app)
            client_app_thread.start()

        communicate_thread = threading.Thread(target=self.communicate)
        communicate_thread.start()

    def communicate(self):
        while not self.state.get('find'):
            self.accept_socket_client()
            print('finding...')
            response = self.send_receive_data(self.find_device_message)
            if response.get('find'):
                print(response)
                self.state['find'] = True
                break
            self.exit_app(response)
            time.sleep(1)

        while not self.state.get('identify') and self.state.get('find'):
            print('Identifying...')
            response = self.send_receive_data(myApp.identify_device_message)
            if response.get('identify'):
                print(response)
                self.state['identify'] = True
                break
            self.exit_app(response)
            time.sleep(1)

        # while not self.state.get('readDataOnce') and self.state.get('find') and self.state.get('identify'):
        #     print('Read data once...')
        #     response = self.send_receive_data(myApp.read_data_once)
        #     if response.get('readDataOnce'):
        #         self.state['readDataOnce'] = True
        #         print(response)
        #         break
        #     self.exit_app(response)
        #     time.sleep(1)
        # Start data stream
        while (self.state.get('findAndIdentify') or (
                self.state.get('find') and self.state.get('identify')) and not self.state.get('startDataStream')):
            response = self.send_receive_data(myApp.start_stream_data)
            if response.get('StartDataStream'):
                self.state['startDataStream'] = True
                print(response)
                break
            self.exit_app(response)
            time.sleep(1)
        while self.state.get('startDataStream'):
            msg = self.client_socket.recv(1024)
            json_string = msg.decode('utf-8')
            response = json.loads(json_string)
            print(response)
            self.exit_app(response)

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
            subprocess.Popen(['START', '/B', self.client_path, '>', self.log_path])
            # subprocess.Popen(self.client_path)
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

    def send_receive_data(self, my_function):
        data = my_function()
        print('send_receive_data: ', data)
        json_object = json.dumps(data)
        self.client_socket.sendall(bytes(json_object, 'utf-8'))
        msg = self.client_socket.recv(1024)
        json_string = msg.decode('utf-8')
        res_data = json.loads(json_string)
        return res_data

    @staticmethod
    def close_message():
        data = {'command': 'Exit'}
        return data

    def exit_app(self, response):
        if self.quit_app:
            print('quit the app...')
            data = myApp.close_message()
            json_object = json.dumps(data)
            self.client_socket.sendall(bytes(json_object, 'utf-8'))
            self.client_socket.close()
            self.kill_client_exe()
            # self.client_socket = None
            time.sleep(1)
            print('quited')
            sys.exit()

        if response.get('disconnect') or self.disconnect:
            print('disconnecting...')
            self.state = dict.fromkeys(self.state, False)
            # self.close_message()
            self.client_socket.close()
            print('closed connection', self.client_socket)
            self.client_socket = None
            print('connection closed')

    @staticmethod
    def kill_client_exe():
        try:
            subprocess.call(['taskkill', '/IM', 'PowerBird.exe', '/F'])
        except BaseException as e:
            print('killing exe file exception:', e)

    def find_device_message(self):
        data = {
            'command': 'findDevice',
            'data': {
                'vendorID': self.vendor_id,
                'productID': self.product_id
            }
        }
        return data

    @staticmethod
    def identify_device_message():
        data = {'command': 'IdentifyDevice'}
        return data

    def find_and_identify_message(self):
        data = {
            'command': 'FindAndIdentify',
            'data': {
                'vendorID': self.vendor_id,
                'productID': self.product_id
            }
        }
        return data

    @staticmethod
    def read_data_once():
        data = {'command': 'ReadDataOnce'}
        return data

    def start_stream_data(self):
        data = {'command': 'StartDataStream', 'data': {
            'limit': self.data_property.get('limit'),
            'count': self.data_property.get('count')
        }}
        return data


my_app = myApp()
my_app.start_app()
