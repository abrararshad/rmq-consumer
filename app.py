import argparse
from consumer import app as consumer_app, run_app as run_consumer_app

import pydevd_pycharm


# pydevd_pycharm.settrace('172.17.0.1', port=21001, stdoutToServer=True, stderrToServer=True)


def boot_app(local=False, config=None, env='local'):
    if not config:
        config = consumer_app.get_config(env)

    app_instance = consumer_app.setup_config(config)
    app_instance.setup_dirs()

    return run_consumer_app(local)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("env", help="The environment in which app should run", choices=('local', 'dev', 'prod'))
    args = parser.parse_args()

    environment = args.env
    boot_app(True, None, environment)
