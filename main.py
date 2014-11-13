"""
Populate voyage data tables from CSV emails.
"""

#import email
import logging
import quopri

from imap import (
	connect_to_server, EmailCheckError, login_to_account, loop_email_messages
)
from settings import IMAP_PASSWORD, IMAP_SERVER, IMAP_USERNAME


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
		#email_from = email.utils.parseaddr(email_message['From'])[1]

		content = quopri.decodestring(email_message.as_string(), False)
		for line in content.splitlines():
			print(line)

		# TODO: Create voyage table if necessary.

		# TODO: Parse CSV from body.

		# TODO: Load CSV into Oracle `marine` database.

		# TODO: Move to voyage archive folder.
		break


if '__main__' == __name__:
	logging.basicConfig(level=logging.DEBUG)

	logger.info('Started.')

	main()

	logger.info('Complete.')
