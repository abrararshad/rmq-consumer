from rmq import RMQ

app = RMQ(__name__)


def run_app(run_server=True):
    with app.app_context():
        app.setup_logger(app.config['APP']['APP_LOG_NAME'])
        from utils.func import log

        from rmq.config import RMQConfig
        RMQConfig.set_app(app)

        if not RMQConfig.config['TESTING']:
            from .subscriber import connect
            connect()
        else:
            log('Running in testing mode')

        if run_server:
            ssl_context = app.config['APP']['SSL_CONTEXT']
            if ssl_context:
                app.run(host='0.0.0.0', port=7000, debug=True, ssl_context=ssl_context)
            else:
                app.run(host='0.0.0.0', port=7000, debug=True)

    return app
