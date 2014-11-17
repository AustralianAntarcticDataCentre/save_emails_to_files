"""
Populate voyage data tables from CSV emails.
"""

from datetime import datetime
import email
import logging

from imap import (
	connect_to_server, EmailCheckError, login_to_account, loop_email_messages
)
from message import CSVEmailParser
from settings import (
	EMAIL_FROM, EMAIL_SUBJECT_RE, IMAP_PASSWORD, IMAP_SERVER, IMAP_USERNAME
)


logger = logging.getLogger(__name__)


class VoyageEmailParser(CSVEmailParser):

	required_columns = ('Date/Time', 'LATITUDE', 'LONGITUDE')


	#def process_csv_content(self, content):
		# TODO: Save this content to a CSV file as backup.
		#self.process_csv_rows(StringIO(content))


	def process_csv_row(self, row):
		"""
		Process a single row of CSV from a voyage email.

		Parameters
		----------

		row : dict
			Column names and their values.
		"""

		#print(sorted(row.keys()))

		row_time_str = row['Date/Time']
		row_time = datetime.strptime(row_time_str, '%Y-%m-%d %H:%M')

		latitude = float(row['LATITUDE'])
		longitude = float(row['LONGITUDE'])

		print(latitude)
		raise Exception('Stop here')


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

		# parsedate_tz() includes the timezone.
		# https://docs.python.org/3.4/library/email.util.html#email.utils.parsedate
		# https://docs.python.org/3.4/library/email.util.html#email.utils.parsedate_tz
		#sent_time = email.utils.parsedate_tz(date)
		#sent_time = email.utils.parsedate(date)


		# parseaddr() splits "From" into name and address.
		# https://docs.python.org/3.4/library/email.util.html#email.utils.parseaddr
		email_from = email.utils.parseaddr(email_message['From'])[1]

		# Skip this message if it did not come from the correct sender.
		if email_from != EMAIL_FROM:
			logger.debug('Email is not from the correct sender (%s).', email_from)
			continue


		subject = email_message['Subject']
		logger.debug('Email subject is "%s".', subject)

		match_data = EMAIL_SUBJECT_RE.match(subject)

		# Skip this message if the subject does not match the format.
		if match_data is None:
			logger.debug('Email subject does not match the required format.')
			continue

		# Get a dict of the values matched in the regex.
		match_dict = match_data.groupdict()

		parser = VoyageEmailParser()

		# Create the table name from the regex values.
		parser.table_name = 'V{season_code}{voyage_code}'.format(**match_dict)

		parser.process_message(email_message)
		break


if '__main__' == __name__:
	logging.basicConfig(level=logging.DEBUG)

	logger.info('Started.')

	main()

	logger.info('Complete.')
