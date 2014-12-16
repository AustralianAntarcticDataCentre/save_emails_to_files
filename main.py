"""
Populate voyage data tables from CSV emails.
"""

from datetime import datetime
import email
import logging
import os

from csv_email import CSVEmailParser
from settings import (
	CSV_COLUMNS, CSV_FOLDER, CSV_NAME_FORMAT, EMAIL_FROM, EMAIL_SUBJECT_RE,
	get_database_client, get_email_client, LOGGING_FORMAT, LOGGING_LEVEL,
	TABLE_NAME_FORMAT
)


logger = logging.getLogger(__name__)


class VoyageEmailParser(CSVEmailParser):

	required_columns = ('Date/Time', 'LATITUDE', 'LONGITUDE')

	def __init__(self, database, table_name, subject_values):
		self.database = database
		self.subject_values = subject_values
		self.table_name = table_name

	def process_csv_content(self, content):
		"""
		Save the CSV to a file and continue processing it.
		"""

		# Create the file name from the subject parts.
		file_name = CSV_NAME_FORMAT.format(**self.subject_values)

		file_path = os.path.join(CSV_FOLDER, file_name)

		# Write the contents of the CSV to the file.
		with open(file_name, 'w') as f:
			f.write(content)

		# Continue processing the message.
		CSVEmailParser.process_csv_content(self, content)

	def process_csv_row(self, row):
		"""
		Process a single row of CSV from a voyage email.


		Parameters
		----------

		row : dict
			Column names and their values.
		"""

		#print(sorted(row.keys()))

		#try:
		row_time_str = row.pop(CSV_COLUMNS['date_time'])
		#except KeyError as e:

		#try:
		date_time_format = row.pop(CSV_COLUMNS['date_time_format'])
		row_time = datetime.strptime(row_time_str, date_time_format)
		#except ValueError as e:

		#try:
		latitude = float(row.pop(CSV_COLUMNS['latitude']))
		longitude = float(row.pop(CSV_COLUMNS['longitude']))
		#except KeyError as e:
		#except ValueError as e:

		# TODO: Remove this test code.
		print(row_time_str)
		raise Exception('Stop here')


def main():
	with get_database_client() as database:
		with get_email_client() as email_client:
			email_client.select_inbox()

			for email_message in email_client.loop_email_messages():
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

				# Create the table name from the regex values.
				table_name = TABLE_NAME_FORMAT.format(**match_dict)

				# Make sure the required table already exists.
				if not database.table_exists(table_name):
					logger.warning('Table "%s" does not exist.', table_name)
					continue

				parser = VoyageEmailParser(database, table_name, match_dict)
				parser.process_message(email_message)


if '__main__' == __name__:
	logging.basicConfig(format=LOGGING_FORMAT, level=LOGGING_LEVEL)

	logger.info('Started reading emails.')

	main()

	logger.info('Finished reading emails.')
