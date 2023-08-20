from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from rmq.config import RMQConfig
from utils.func import log, log_error


def send_log_email(logs_lines=None, body_prefix=None):
    mail_config = RMQConfig.mail_value()
    sendgrid_config = mail_config['SENDGRID']
    if 'API_KEY' not in sendgrid_config and sendgrid_config['API_KEY'] is None:
        log_error('SendGrid API key is not set')
        return

    if not logs_lines:
        log_file_path = f"{RMQConfig.config['APP_LOGS_DIR']}/{RMQConfig.config['APP_LOG_NAME']}"
        num_lines = mail_config['LOG_NUM_LINES']
        with open(log_file_path, 'r') as log_file:
            lines = log_file.readlines()
            logs_lines = lines[-num_lines:]

    subject = f'{mail_config["LOG_SUBJECT"]} - {RMQConfig.config["APP"]["ENV"]}'
    body = '<html><body><h2>Errors</h2>'
    if body_prefix:
        body += body_prefix

    body += append_logs_body(logs_lines)

    # Email configuration
    from_email = sendgrid_config['FROM']
    to_email = sendgrid_config['TO']
    sendgrid_api_key = sendgrid_config['API_KEY']

    # Create the SendGrid mail object
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=body
    )

    # Send the email using SendGrid API
    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        log("Email sent successfully!")
    except Exception as e:
        log_error("An error occurred:", str(e))


def append_logs_body(logs_lines):
    body = '<table style="background-color: black; color: white; width: 100%; font-family: monospace;">'

    # Add header row
    body += '<tr><th>Line Number</th><th>Log Entry</th></tr>'

    # Add log lines with alternating background colors
    for idx, line in enumerate(logs_lines):
        line_number = idx + 1
        background_color = 'black' if idx % 2 == 0 else '#333'
        body += f'<tr style="background-color: {background_color};"><td>{line_number}</td><td>{line.strip()}</td></tr>'

    body += '</table></body></html>'

    return body
