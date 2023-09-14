import argparse
from consumer import app as consumer_app, run_app as run_consumer_app
from frontend import app as frontend_app, run_app as run_frontend_app
import pydevd_pycharm

# pydevd_pycharm.settrace('172.17.0.1', port=21001, stdoutToServer=True, stderrToServer=True)

app_name = None
environment = None
run_locally = True


def init_app():
    apps = {
        'consumer': boot_consumer,
        'dash': boot_dashboard
    }

    app_to_run = apps.get(app_name)
    if not app_to_run:
        raise Exception('No app as such exists: {}'.format(app_name))

    app_to_run(run_locally, None, environment)


def boot_consumer(local=False, config=None, env='local'):
    if not config:
        config = consumer_app.get_config(env)

    app_instance = consumer_app.setup_config(config)
    app_instance.setup_dirs()

    return run_consumer_app(local)


def boot_dashboard(local=False, config=None, env='local'):
    if not config:
        config = frontend_app.get_config(env)

    app_instance = frontend_app.setup_config(config)
    app_instance.setup_dirs()

    return run_frontend_app(local)


def print_config(config):
    print('Environment:')
    for k, v in config.items():
        print("\t{} => {}".format(k, v))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("app", help="App(service) to start", choices=('consumer', 'dash'))
    parser.add_argument("env", help="The environment in which app should run", choices=('local', 'dev', 'prod'))
    parser.add_argument("local", help="Run the app locally", type=bool)
    args = parser.parse_args()

    app_name = args.app
    environment = args.env
    run_locally = args.local

    init_app()
