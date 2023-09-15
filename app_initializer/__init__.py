import os
from .logger.extensions import logs
from .logger import settings as LoggingSettings
from flask import Flask, jsonify
from utils.func import load_yaml
from utils.struct import Struct
import pydevd_pycharm


# pydevd_pycharm.settrace('host.docker.internal', port=21001, stdoutToServer=True, stderrToServer=True)

class AppInitializer(Flask):
    def __init__(self, import_name, static_url_path=''):
        super(AppInitializer, self).__init__(import_name, static_url_path=static_url_path)
        self.register_error_handler(404, self.not_found)

    def not_found(self, error):
        return jsonify(error=str(error)), 404

    def setup_config(self, config):
        self.config.from_object(config)
        self.config['APP_ROOT'] = os.getcwd()

        return self

    def get_config(self, env):
        file = 'configuration/envs/{}_config.yml'.format(env)

        if not os.path.exists(file):
            raise FileExistsError('No config found at configuration/envs/{}'.format(file))

        config = {}

        # Global config
        global_config = load_yaml('configuration/global_config.yml')
        if global_config:
            for key in global_config:
                config[key] = global_config[key]

        # Environmental config
        env_config = load_yaml(file)
        if env_config:
            for key in env_config:
                config[key] = env_config[key]

        return Struct(**config)

    def setup_logger(self):
        self.config.from_object(LoggingSettings)

        self.config['LOG_DIR'] = self.config['APP_LOGS_DIR']
        self.config['APP_LOG_NAME'] = self.config['LOG_FILES'][self.name.split('.')[1].upper()]

        logs.init_app(self)

    def setup_dirs(self):
        app_root = self.config['APP_ROOT']

        if not self.config['APP']['APP_LOG_DIR']:
            app_logs_dir = app_root + '/logs'
        else:
            app_logs_dir = self.config['APP']['APP_LOG_DIR'] + '/logs'

        self.config['APP_LOGS_DIR'] = app_logs_dir

        paths = [
            app_logs_dir
        ]

        try:
            for path in paths:
                AppInitializer.create_app_dir(path)
        except Exception as e:
            raise Exception('Could not create directories: {}'.format(e))

    @classmethod
    def create_app_dir(cls, path):
        if not os.path.exists(path):
            os.mkdir(path)
