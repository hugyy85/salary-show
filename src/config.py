import os
import logging

DEBUG = True if os.getenv('DEBUG') == 'true' else False

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')

TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')

MY_EMAIL = os.getenv('MY_EMAIL')