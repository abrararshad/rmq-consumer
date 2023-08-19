import os
from app import boot_app, consumer_app


def initialize_app(config=None):
    if not config:
        env = os.environ.get('WVISION_TESTING_ENV')
        config = consumer_app.get_config(env)

    if not config:
        raise Exception('No config found')

    # Based on this key, boot-up will start app in testing mode
    config.TESTING = True

    # setup the config now and it will start it
    instance = boot_app(False, config)
    return instance
