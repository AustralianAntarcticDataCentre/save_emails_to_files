import os
import re

from imap import EmailCheckError, EmailServer
from postgresql import DatabaseServer


CSV_FOLDER = os.getcwd()

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

TABLE_NAME_FORMAT = 'data_{year}{month}'


def get_database_client():
	con = 'my_username/my_password@database.example.com:5432/my_database'
	return DatabaseServer(con)


def get_email_client():
	return EmailServer('mail.example.com', 'my_username', 'my_password')
