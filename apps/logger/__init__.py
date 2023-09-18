from flask import request, current_app
from .socket_app import app
from flask_basicauth import BasicAuth

# Apply on the entire app
app.config['BASIC_AUTH_FORCE'] = True
app.config['BASIC_AUTH_REALM'] = 'Authentication is required'
basic_auth = BasicAuth(app)


@app.before_request
def require_authentication():
    if not request.endpoint or request.endpoint == 'basic_auth.login':
        return  # Skip authentication for login route
    if not basic_auth.authenticate():
        return basic_auth.challenge()


def run_app(run_local=False):
    with app.app_context():
        app.config['BASIC_AUTH_USERNAME'] = current_app.config['BASIC_AUTH_USERNAME']
        app.config['BASIC_AUTH_PASSWORD'] = current_app.config['BASIC_AUTH_PASSWORD']

        app.setup_logger()

        from app_initializer.config import RMQConfig
        RMQConfig.set_app(app)

        from .controller import api

        if run_local:
            socket_app.socketio.run(app, port=8001, host='0.0.0.0', debug=True)

    return app
