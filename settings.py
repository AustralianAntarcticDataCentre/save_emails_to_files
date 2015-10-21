"""
Connection settings for AAD IMAP server.

This module should NOT be saved in the repo, because it contains
sensitive details that only apply to the AAD environment.

Read comments in `settings_example.py` for each variable.
"""

import logging
import os
import re

import yaml

from imap import EmailAccount


BASE_PATH = os.path.join(os.getcwd(), '..', 'data')
BASE_PATH = os.path.normpath(BASE_PATH)

SAVE_FOLDER = BASE_PATH

SETTINGS_YAML_PATH = os.path.join(os.getcwd(), 'settings.yaml')

# Where the DIF XML files can be found.
EMAIL_SERVER = os.environ['EMAIL_SERVER']

# Base path of where the converted XML should go.
EMAIL_USERNAME = os.environ['EMAIL_USERNAME']

# Base path of where the XML conversion files can be found.
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']

LOGGING_FORMAT = '''
- file: %(pathname)s
  function: %(funcName)s
  level: %(levelname)s
  line: %(lineno)s
  logger: %(name)s
  message: |
    %(message)s
  time: %(asctime)s
'''.strip()

LOGGING_LEVEL = logging.DEBUG
#LOGGING_LEVEL = logging.INFO

LOGGING_KWARGS = dict(
	filemode='w',
	#filename='underway.log',
	format=LOGGING_FORMAT,
	level=logging.DEBUG
)


def get_all_checks():
	file_types = None

	with open(SETTINGS_YAML_PATH) as r:
		file_types = yaml.load(r)

	return file_types


def get_email_server():
	return EmailAccount(EMAIL_SERVER, EMAIL_USERNAME, EMAIL_PASSWORD)
