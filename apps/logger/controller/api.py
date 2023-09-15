from flask import current_app, render_template


@current_app.route('/logger', methods=['GET'])
def logger():
    return render_template('logger.html')
