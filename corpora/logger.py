import logging
from logging import handlers
from os import path

# For sending mail.
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

log_path = path.join('log.log')

# Create the logger.
logger = logging.getLogger('argos.corpora')

# Configure the logger.
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Output to file, if DEBUG=True
fh = logging.FileHandler(log_path)
fh.setFormatter(formatter)
logger.addHandler(fh)

# Output to console.
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

# Output to email.
mh = handlers.SMTPHandler(
        (config.MAIL_HOST, config.MAIL_PORT),
        config.MAIL_USER,
        config.ADMINS,
        'Argos Corpora Error :(',
        credentials=(
            config.MAIL_USER,
            config.MAIL_PASS
        ),
        secure=()
)
mh.setLevel(logging.ERROR)
logger.addHandler(mh)

def notify(subject, body):
    """
    Send an e-mail notification.
    """
    from_addr = config.MAIL_USER

    # Construct the message.
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Connect to the mail server.
    server = smtplib.SMTP(config.MAIL_HOST, config.MAIL_PORT)
    server.starttls()
    server.login(from_addr, config.MAIL_PASS)

    for target in config.ADMINS:
        msg['To'] = target
        server.sendmail(from_addr, target, msg.as_string())

    server.quit()
