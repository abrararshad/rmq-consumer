from flask import current_app


class RMQConfig(object):
    config = None

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
    def mail_value(key=None):
        m = current_app.config['MAIL']
        if key in m:
            return m[key]

        return m
