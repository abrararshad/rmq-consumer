from flask import request, current_app
from app_initializer import AppInitializer
from flask_basicauth import BasicAuth

app = AppInitializer(__name__, '/static')

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


def run_app(run_server=True):
    with app.app_context():
        app.config['BASIC_AUTH_USERNAME'] = current_app.config['BASIC_AUTH_USERNAME']
        app.config['BASIC_AUTH_PASSWORD'] = current_app.config['BASIC_AUTH_PASSWORD']

        app.setup_logger()

        from .context import vars
        import shared.filters
        from .controller import api

        if run_server:
            ssl_context = app.config['APP']['SSL_CONTEXT']
            if ssl_context:
                app.run(host='0.0.0.0', port=9001, debug=True, ssl_context=ssl_context, allow_unsafe_werkzeug=True)
            else:
                app.run(host='0.0.0.0', port=9001, debug=True, allow_unsafe_werkzeug=True)

    return app
