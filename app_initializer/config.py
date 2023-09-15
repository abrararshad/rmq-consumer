import os.path
from flask import current_app
import requests


class RMQConfig(object):
    config = None

    @staticmethod
    def get_global_ip():
        try:
            filename = current_app.config['APP_LOGS_DIR'] + '/global_ip.txt'
            if os.path.exists(filename):
                with open(filename, 'r') as file:
                    global_ip = file.read().strip()
                    if global_ip:
                        return global_ip

            response = requests.get('https://httpbin.org/ip')
            if response.status_code == 200:
                data = response.json()
                global_ip = data.get('origin')

                with open(filename, 'w') as file:
                    file.write(global_ip)

                return global_ip
            else:
                print(f"Error while getting ip, status code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred: {e}")

    @staticmethod
    def set_app(app):
        RMQConfig.config = app.config

    @staticmethod
    def consumer_value(key=None):
        c = current_app.config['CONSUMER']
        if key in c:
            return c[key]

        return c

    @staticmethod
    def notification_value(key=None):
        m = current_app.config['NOTIFICATION']
        if key in m:
            return m[key]

        return m
