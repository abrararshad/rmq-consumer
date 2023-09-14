from rmq import RMQ

app = RMQ(__name__, '/static')

app.config['BASIC_AUTH_USERNAME'] = 'rmq_user_01'
app.config['BASIC_AUTH_PASSWORD'] = '123#321'

# Apply on the entire app
app.config['BASIC_AUTH_FORCE'] = True
app.config['BASIC_AUTH_REALM'] = 'Authentication is required'


def run_app(run_server=True):
    with app.app_context():

        import shared.filters
        from .controller import api

        if run_server:
            ssl_context = app.config['APP']['SSL_CONTEXT']
            if ssl_context:
                app.run(host='0.0.0.0', port=9001, debug=True, ssl_context=ssl_context)
            else:
                app.run(host='0.0.0.0', port=9001, debug=True)

    return app
