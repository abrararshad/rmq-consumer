from flask import current_app


@current_app.context_processor
def contextual_vars():
    return {'LOGGER_SOCKET': current_app.config['REAL_TIME_LOGGER']['SOCKET_URL']}
