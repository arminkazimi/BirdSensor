import sys
import threading
# import multiprocessing
import socket
import json
import time
import os
import subprocess
import keyboard as kb
from pynput import keyboard
import pandas
from datetime import datetime

# PRODUCTION = False
PRODUCTION = True
#
# VENDOR_ID = '0909'
# PRODUCT_ID = '0051'

DATA_LIMIT = True
DATA_COUNT = 2

PORT = 1234
HOST = '127.0.0.1'
VENDOR_ID = '1422'
PRODUCT_ID = '5014'
CLIENT_PATH = r'cs_app\PowerBird.exe'
LOG_FILE_PATH = r'client_log.txt'


class MyApp:
    def __init__(self):
        self.streamed_data = {'datetime': [],
                              'reflectedPower': [],
                              'forwardPower': [], 'refFwd': []}
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

        self.keyboard_listener_thread = None
        self.client_app_thread = None
        self.communicate_thread = None

    def communicate(self):
        self.accept_socket_client()
        for count in range(3):
            print('find and identify...')
            response = self.send_receive_data(self.find_and_identify_message)
            if response.get('findAndIdentify'):
                print(response)
                self.state['findAndIdentify'] = True
                break
            self.exit_app(response)
            time.sleep(1)

        while not self.state.get('find') and not self.state.get('findAndIdentify'):
            # self.accept_socket_client()
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
            response = self.send_receive_data(MyApp.identify_device_message)
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
            response = self.send_receive_data(self.start_stream_data)
            if response.get('StartDataStream'):
                self.state['startDataStream'] = True
                print(response)
                break
            self.exit_app(response)
            time.sleep(1)

        limit = 0
        df = pandas.DataFrame(data=self.streamed_data)
        start_time = datetime.now()
        start_time_str = start_time.strftime('%d%m%Y_%H:%M:%S')
        while self.state.get('startDataStream') and limit < self.data_property.get('count'):
            msg = self.client_socket.recv(1024)
            json_string = msg.decode('utf-8')
            response = json.loads(json_string)
            self.load_response(response)
            df = df.append({'datetime': self.streamed_data.get('datetime')[-1],
                            'reflectedPower': self.streamed_data.get('ReflectedPower')[-1],
                            'forwardPower': self.streamed_data.get('ForwardPower')[-1],
                            'refFwd': self.streamed_data.get('datetime')[-1]},
                           ignore_index=True)
            df.to_csv(f'{start_time_str}.csv')
            limit += 1
            if limit == self.data_property.get('count'):
                self.state['startDataStream'] = False
                kb.press_and_release('esc')
                break
            self.exit_app(response)

    def load_response(self, response):
        date = response.get('date')
        data = response.get('data')

        reflect = data.get('ReflectedPower')
        forward = data.get('ForwardPower')
        result = data.get('ReflectedPower') / data.get('ForwardPower')
        print("Reflected/Forward: ", result)
        print('date: ', date)
        self.streamed_data['datetime'].append(date)
        self.streamed_data['ReflectedPower'].append(reflect)
        self.streamed_data['ForwardPower'].append(forward)
        self.streamed_data['datetime'].append(result)

    def start_app(self):
        MyApp.kill_client_exe()
        time.sleep(1)
        self.keyboard_listener_thread = threading.Thread(target=self.keyboard_listener)
        self.keyboard_listener_thread.start()

        self.run_socket_server()
        if PRODUCTION:
            self.client_app_thread = threading.Thread(target=self.execute_client_app)
            self.client_app_thread.start()

        self.communicate_thread = threading.Thread(target=self.communicate)
        self.communicate_thread.start()

    @staticmethod
    def save_csv(df, start_time):
        start_time_str = start_time.strftime('%d%m%Y_%H:%M:%S')
        # end_time = datetime.now()
        # end_time_str = end_time.strftime('%d%m%Y_%H:%M:%S%f')[:-3]
        df.to_csv(f'{start_time_str}.csv')

    def on_press(self, key):
        if key == keyboard.Key.esc:
            self.quit_app = True
            response_dict = {'disconnect': False}
            self.exit_app(response_dict)
            return False
            # stop listener

        try:
            k = key.char  # single-char keys
            # print(k)
        except:
            k = key.name  # other keys
            # print(k)
        if k in ['d']:  # keys of interest
            # self.keys.append(k)  # store it in global-like variable
            print('Key pressed: ' + k)
            self.disconnect = True
            response_dict = {'disconnect': True}
            self.exit_app(response_dict)
            return False  # stop listener; remove this if want more keys

    def keyboard_listener(self):
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()  # start to listen on a separate thread
        listener.join()

    def execute_client_app(self):
        try:
            os.system(f'START /B {self.client_path} > {self.log_path}')
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
        print('request data: ', data)
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
            data = MyApp.close_message()
            json_object = json.dumps(data)
            self.client_socket.sendall(bytes(json_object, 'utf-8'))
            self.client_socket.close()
            self.kill_client_exe()

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
        except Exception as e:
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


if __name__ == '__main__':
    my_app = MyApp()
    my_app.start_app()
