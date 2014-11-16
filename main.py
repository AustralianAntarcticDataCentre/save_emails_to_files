"""
Populate voyage data tables from CSV emails.
"""

import csv
import email
from io import StringIO
import logging
import quopri

from imap import (
	connect_to_server, EmailCheckError, login_to_account, loop_email_messages
)
from settings import (
	EMAIL_FROM, EMAIL_SUBJECT_PREFIX, IMAP_PASSWORD, IMAP_SERVER, IMAP_USERNAME
)


logger = logging.getLogger(__name__)


def get_email_content(message):
	if not message.is_multipart():
		return message.get_payload()

	parts = [get_email_content(payload) for payload in message.get_payload()]
	return ''.join(parts)


def main():
	# Would be nicer if `with IMAP4_SSL() as mail:` was possible.
	mail = connect_to_server(IMAP_SERVER)

	try:
		login_to_account(mail, IMAP_USERNAME, IMAP_PASSWORD)
	except EmailCheckError as e:
		logger.error(e.args[0])
		raise e

	for email_message in loop_email_messages(mail):
		#for header_name, header_value in email_message.items():

		# parseaddr() splits "From" into name and address.
		# https://docs.python.org/3.4/library/email.util.html#email.utils.parseaddr
		email_from = email.utils.parseaddr(email_message['From'])[1]

		# Skip this message if it did not come from the correct sender.
		if email_from != EMAIL_FROM:
			continue

		subject = email_message['Subject']

		# Skip this message if the subject does not have the correct prefix.
		if not subject.startswith(EMAIL_SUBJECT_PREFIX):
			continue

		# parsedate_tz() includes the timezone.
		# https://docs.python.org/3.4/library/email.util.html#email.utils.parsedate
		# https://docs.python.org/3.4/library/email.util.html#email.utils.parsedate_tz
		#sent_time = email.utils.parsedate_tz(date)
		#sent_time = email.utils.parsedate(date)

		# TODO: Should check the subject structure is correct.
		subject_parts = subject.split()
		setcode = subject_parts[2]

		raw_content = get_email_content(email_message)
		content_bytes = quopri.decodestring(raw_content, False)
		content = content_bytes.decode('utf-8')

		# TODO: Save this content to a CSV file as backup.

		with StringIO(content) as f:
			reader = csv.DictReader(f)
			for row in reader:
				print(row)
				break

		break


if '__main__' == __name__:
	logging.basicConfig(level=logging.DEBUG)

	logger.info('Started.')

	main()

	logger.info('Complete.')
