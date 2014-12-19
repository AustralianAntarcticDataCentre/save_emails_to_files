"""
Populate voyage data tables from CSV emails.
"""

from datetime import datetime
import email
import logging
import os
import re

from csv_email import CSVEmailParser
from settings import (
	CSV_FOLDER, get_csv_file_types, get_database_client, get_email_client,
	LOGGING_FORMAT, LOGGING_LEVEL
)


logger = logging.getLogger(__name__)


class VoyageEmailParser(CSVEmailParser):

	def __init__(self, database, csv, table_name, subject_values):
		"""
		Create a new voyage CSV email parser.

		Each of the parameters passed into this method are stored in the object.


		Parameters
		----------

		database : object
			Helper class for accessing the database used to store CSV data.

		csv : dict
			Dictionary used to extract data from the CSV email.
			The details are specific to the matched email format.

		table_name : str
			Name of the table in the database to update with CSV rows.

		subject_values : dict
			Values that were extracted from the email subject.
		"""

		self.csv = csv
		self.database = database
		self.subject_values = subject_values
		self.table_name = table_name

	def process_csv_content(self, content):
		"""
		Save the CSV to a file and continue processing it.
		"""

		file_name_format = self.csv['save_csv']['file_name_format'].strip()

		# Create the file name from the subject parts.
		file_name = file_name_format.format(**self.subject_values)

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

		load_csv = self.csv['load_csv']

		#try:
		date_time_details = load_csv['date_time']
		row_time_str = row.pop(date_time_details['column'])
		row_time_format = row.pop(date_time_details['format'])
		#except KeyError as e:

		#try:
		row_time = datetime.strptime(row_time_str, row_time_format)
		#except ValueError as e:

		#try:
		latitude_name = load_csv['latitude']['column']
		latitude = float(row.pop(latitude_name))

		longitude_name = load_csv['longitude']['column']
		longitude = float(row.pop(longitude_name))
		#except KeyError as e:
		#except ValueError as e:

		# TODO: Remove this test code.
		print(row_time)
		raise Exception('Stop here')


def main():
	csv_file_types = get_csv_file_types()

	if csv_file_types is None:
		return False

	with get_database_client() as database:
		with get_email_client() as email_client:
			email_client.select_inbox()

			for email_message in email_client.loop_email_messages():
				# parseaddr() splits "From" into name and address.
				# https://docs.python.org/3/library/email.util.html#email.utils.parseaddr
				email_from = email.utils.parseaddr(email_message['From'])[1]

				logger.debug('Email is from "%s".', email_from)

				subject = email_message['Subject']

				logger.debug('Email subject is "%s".', subject)

				for CSV_TYPE in csv_file_types:
					check = CSV_TYPE['check']

					required_from = check['from']

					# Skip this message if it did not come from the correct sender.
					if email_from != required_from:
						msg = 'Email is not from the correct sender (%s).'
						logger.warning(msg, required_from)
						continue

					subject_regex_list = check['subject_regex']
					subject_regex = re.compile(''.join(subject_regex_list))

					match_data = subject_regex.match(subject)

					# Skip this message if the subject does not match the format.
					if match_data is None:
						logger.warning('Email subject does not match the required format.')
						continue

					# Get a dict of the values matched in the regex.
					match_dict = match_data.groupdict()

					save_table = CSV_TYPE['save_table']
					table_name_format = save_table['file_name_format'].strip()

					# Create the table name from the regex values.
					table_name = table_name_format.format(**match_dict)

					# Make sure the required table already exists.
					if not database.table_exists(table_name):
						logger.warning('Table "%s" does not exist.', table_name)
						continue

					parser = VoyageEmailParser(database, CSV_TYPE, table_name,
						match_dict
					)
					parser.process_message(email_message)

	return True


if '__main__' == __name__:
	logging.basicConfig(format=LOGGING_FORMAT, level=LOGGING_LEVEL)

	# TODO: Compile each `CSV[i]['check']['subject_regex']`.

	logger.info('Started reading emails.')

	main()

	logger.info('Finished reading emails.')
