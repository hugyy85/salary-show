import os
import logging

DEBUG = True if os.getenv('DEBUG') == 'true' else False

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')

TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')

WEBHOOK_PATH = '/api/v1/tg_webhook'

# webserver settings
WEBAPP_ADDRESS = os.getenv('WEBAPP_ADDRESS')
WEBHOOK_IP = os.getenv('WEBHOOK_IP')
WEBAPP_HOST = os.getenv('WEBAPP_HOST') or '0.0.0.0'
WEBAPP_PORT = int(os.getenv('WEBAPP_PORT')) if os.getenv('WEBAPP_PORT') else 3003

MY_EMAIL = os.getenv('MY_EMAIL')