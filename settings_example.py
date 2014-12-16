"""
Example settings module.

This should be copied as `settings.py` and the values modified there.

That file is ignored by the repo, since it will contain environment
specific and sensitive information (like passwords).
"""

# TODO: Allow separate settings for different subject matches.
# Email formats and CSV names may change over the years, and this could
# be detected by subject matches.

import logging
import os
import re

from imap import EmailCheckError, EmailServer
from postgresql import DatabaseServer


CSV_COLUMNS = dict(
	date_time='time',
	date_time_format='%Y-%m-%dT%H:%M:%SZ',
	latitude='latitude',
	longitude='longitude'
)

# If this is set to a valid path, all CSV files extracted from emails will be
# stored in sub-folders within it.
CSV_FOLDER = os.getcwd()

# Values come from `EMAIL_SUBJECT_RE`.
CSV_NAME_FORMAT = '{year}-{month}-{day}T{hour}{minute}.csv'

# Restrict emails by sender.
EMAIL_FROM = 'sender@example.com'

# Restrict emails by subject.
EMAIL_SUBJECT_RE = re.compile(''.join([
	r'(?P<year>\d{4})',
	r'(?P<month>\d{2})',
	r'(?P<day>\d{2})',
	r'(?P<hour>\d{2})',
	r'(?P<minute>\d{2})',
	r'\.csv',
]))

LOGGING_FORMAT = '''
- file: %(pathname)s
  level: %(levelname)s
  line: %(lineno)s
  message: |
    %(message)s
  time: %(asctime)s
'''.strip()

LOGGING_LEVEL = logging.DEBUG

# Values come from `EMAIL_SUBJECT_RE`.
TABLE_NAME_FORMAT = 'data_{year}{month}'


def get_database_client():
	con = 'my_username/my_password@database.example.com:5432/my_database'
	return DatabaseServer(con)


def get_email_client():
	return EmailServer('mail.example.com', 'my_username', 'my_password')
