"""
Populate voyage data tables from CSV emails.
"""

from datetime import datetime
import email
import logging

from message import CSVEmailParser
from settings import (
	DATABASE_STRING, DatabaseServer, EMAIL_FROM, EMAIL_SUBJECT_RE,
	EmailCheckError, EmailServer, IMAP_PASSWORD, IMAP_SERVER, IMAP_USERNAME,
	TABLE_NAME_FORMAT
)


logger = logging.getLogger(__name__)


class VoyageEmailParser(CSVEmailParser):

	required_columns = ('Date/Time', 'LATITUDE', 'LONGITUDE')

	def __init__(self, database, table_name):
		self.database = database
		self.table_name = table_name

	#def process_csv_content(self, content):
		# TODO: Save this content to a CSV file as backup.
		#file_name = ?
		#with open(file_name, 'w') as f:
			#f.write(content)

		#self.process_csv_rows(StringIO(content))
		#CSVEmailParser.process_csv_content(self, content)

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

		#self.database.create_table(self.table_name)

		# TODO: Remove this test code.
		print(latitude)
		raise Exception('Stop here')


def main():
	#with DatabaseServer(DATABASE_STRING) as database:
	if True:
		with EmailServer(IMAP_SERVER, IMAP_USERNAME, IMAP_PASSWORD) as server:
			server.select_inbox()

			for email_message in server.loop_email_messages():
				# parseaddr() splits "From" into name and address.
				# https://docs.python.org/3/library/email.util.html#email.utils.parseaddr
				email_from = email.utils.parseaddr(email_message['From'])[1]

				logger.debug('Email is from "%s".', email_from)

				# Skip this message if it did not come from the correct sender.
				if email_from != EMAIL_FROM:
					logger.warning('Email is not from the correct sender (%s).', EMAIL_FROM)
					continue

				subject = email_message['Subject']

				logger.debug('Email subject is "%s".', subject)

				match_data = EMAIL_SUBJECT_RE.match(subject)

				# Skip this message if the subject does not match the format.
				if match_data is None:
					logger.warning('Email subject does not match the required format.')
					continue

				# Get a dict of the values matched in the regex.
				match_dict = match_data.groupdict()

				# parsedate_tz() includes the timezone.
				# https://docs.python.org/3/library/email.util.html#email.utils.parsedate
				# https://docs.python.org/3/library/email.util.html#email.utils.parsedate_tz
				#sent_time = email.utils.parsedate_tz(date)

				# Create the table name from the regex values.
				table_name = TABLE_NAME_FORMAT.format(**match_dict)

				#parser = VoyageEmailParser(database, table_name)

				#parser.process_message(email_message)
				break
		#except EmailCheckError as e:
			#logger.error(e.args[0])
			#raise e


if '__main__' == __name__:
	logging.basicConfig(level=logging.DEBUG)

	logger.info('Started reading emails.')

	main()

	logger.info('Finished reading emails.')
