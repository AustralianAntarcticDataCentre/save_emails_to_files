"""
Populate voyage data tables from CSV emails.
"""

import email
import logging
import quopri

from imap import (
	connect_to_server, EmailCheckError, login_to_account, loop_email_messages
)
from settings import (
	EMAIL_FROM, EMAIL_SUBJECT_PREFIX, IMAP_PASSWORD, IMAP_SERVER, IMAP_USERNAME
)


logger = logging.getLogger(__name__)


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
		email_from = email.utils.parseaddr(email_message['From'])[1]

		# Skip this message if it did not come from the correct sender.
		if email_from != EMAIL_FROM:
			continue

		subject = email_message['Subject']

		# Skip this message if the subject does not have the correct prefix.
		if not subject.startswith(EMAIL_SUBJECT_PREFIX):
			continue

		content = quopri.decodestring(email_message.as_string(), False)
		for line in content.splitlines():
			print(line)

		break


if '__main__' == __name__:
	logging.basicConfig(level=logging.DEBUG)

	logger.info('Started.')

	main()

	logger.info('Complete.')
