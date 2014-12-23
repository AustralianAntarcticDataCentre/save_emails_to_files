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

		self.database = database
		self.subject_values = subject_values
		self.table_name = table_name

		self.csv_column_name = {}
		self.db_field_name = {}

		# Settings to interpret the CSV columns.
		self.load_csv = csv['load_csv']

		# Settings to save a copy of the CSV.
		self.save_csv = csv.get('save_csv', {})

		# Save the format the date column uses.
		self.db_time_format = self.load_csv['date_time']['format']

		for setting_name in ['date_time', 'latitude', 'longitude']:
			setting = self.load_csv[setting_name]
			column = setting['column']

			# Save the CSV column name for parsing rows later.
			self.csv_column_name[setting_name] = column

			# Use the CSV column name if the database field is not specified.
			self.db_field_name[setting_name] = setting.get('field', column)

	def process_csv_content(self, content):
		"""
		Save the CSV to a file and continue processing it.


		Parameters
		----------

		content : str
			Text from the email, processed from the raw format.
		"""

		if 'file_name_format' in self.save_csv:
			file_name_format = self.save_csv['file_name_format'].strip()

			# Create the file name from the subject parts.
			file_name = file_name_format.format(**self.subject_values)

			file_path = os.path.join(CSV_FOLDER, file_name)

			# Write the contents of the CSV to the file.
			with open(file_name, 'w') as f:
				f.write(content)

		# Continue processing the message.
		CSVEmailParser.process_csv_content(self, content)

	def process_csv_row(self, csv_row):
		"""
		Process a single row of CSV from a voyage email.


		Parameters
		----------

		row : dict
			Column names and their values.
		"""

		#print(sorted(row.keys()))

		# Stores the field names and values to be inserted into the database.
		fields = {}

		setting_name = 'date_time'
		csv_name = self.csv_column_name[setting_name]
		db_name = self.db_field_name[setting_name]

		# Get the raw time value from the CSV row.
		time_str = csv_row.pop(csv_name)

		# Save the time object after converting it using the saved format.
		fields[field_name] = datetime.strptime(time_str, self.db_time_format)

		for setting_name in ['latitude', 'longitude']:
			csv_name = self.csv_column_name[setting_name]
			db_name = self.db_field_name[setting_name]
			fields[db_name] = float(csv_row.pop(csv_name))

		# Loop each of the CSV column details.
		for csv_name, column_details in self.load_csv['columns'].items():
			if csv_name not in csv_row:
				continue

			# Use the CSV column name if a database field name is not given.
			db_name = column_details.get('field', csv_name)

			fields[field_name] = csv_row[csv_name]

		self.database.insert_row(self.table_name, fields)


def process_message(database, message, csv_file_types):
	"""
	Process a message containing CSV voyage data.


	Parameters
	----------

	database : object
		Helper class for accessing the database used to store CSV data.

	message : email.message.Message
		Message (hopefully) with CSV content to be processed.

	csv_file_types : list
		List of dictionaries containing checks and settings for the different
		types of CSV emails that can be processed.


	Raises
	------

	KeyError
		If any of the required settings are not in the CSV types dictionary.


	Returns
	-------

	bool
		True if the message was processed, False if no handler could be found.
	"""

	# parseaddr() splits "From" into name and address.
	# https://docs.python.org/3/library/email.util.html#email.utils.parseaddr
	email_from = email.utils.parseaddr(message['From'])[1]

	logger.debug('Email is from "%s".', email_from)

	subject = message['Subject']

	logger.debug('Email subject is "%s".', subject)

	for csv_type in csv_file_types:
		check = csv_type['check']

		required_from = check['from']

		# Skip this message if it did not come from the correct sender.
		if email_from != required_from:
			msg = 'Email is not from the correct sender (%s).'
			logger.warning(msg, required_from)
			continue

		# Use the compiled RegEx if it is available.
		if 'subject_regex_compiled' in check:
			subject_regex = check['subject_regex_compiled']

		# Compile and save the RegEx otherwise.
		else:
			subject_regex_list = check['subject_regex']
			subject_regex = re.compile(''.join(subject_regex_list))
			check['subject_regex_compiled'] = subject_regex

		# Check if the message subject matches the RegEx.
		match_data = subject_regex.match(subject)

		# Skip this message if the subject does not match the RegEx.
		if match_data is None:
			logger.warning('Email subject does not match the required format.')
			continue

		# Get a dict of the values matched in the regex.
		match_dict = match_data.groupdict()

		save_table = csv_type['save_table']

		# Get the table name template.
		table_name_format = save_table['file_name_format'].strip()

		# Create the table name from the regex values.
		table_name = table_name_format.format(**match_dict)

		# Create the required table if it does not exist.
		if not database.table_exists(table_name):
			logger.info('Table "%s" does not exist.', table_name)

			load_csv = csv_type['load_csv']
			column_lookup = database.create_table(table_name, load_csv)

		parser = VoyageEmailParser(database, csv_type, table_name, match_dict)
		parser.process_message(message)

		# No need to check other CSV parsers once one is complete.
		return True

	# Returns False if none of the parsers matched the given email.
	return False


def process_emails():
	"""
	Main function to import CSV emails into the database.

	Creates a database and email connection then loops all the emails in the
	inbox.


	Returns
	-------

	bool
		False if settings cannot be loaded.
	"""

	csv_file_types = get_csv_file_types()

	if csv_file_types is None:
		logger.error('CSV file types could not be read from `settings.yaml`.')
		return False

	with get_database_client() as database, get_email_client() as email_client:
		email_client.select_inbox()

		for message in email_client.loop_email_messages():
			process_message(database, message, csv_file_types)

	return True


if '__main__' == __name__:
	logging.basicConfig(format=LOGGING_FORMAT, level=LOGGING_LEVEL)

	logger.info('Started reading emails.')

	process_emails()

	logger.info('Finished reading emails.')
