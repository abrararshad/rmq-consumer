from flask import current_app


class RMQConfig(object):
    config = None

    @staticmethod
    def set_app(app):
        RMQConfig.config = app.config

    @staticmethod
    def consumer_value(key):
        c = current_app.config['CONSUMER']
        if key in c:
            return c[key]
