"""
Populate voyage data tables from CSV emails.

Running as a script calls `process_emails()`.

This uses `get_csv_file_types()` to get email details for searching, and
opens email and database connections.
It then calls `process_message()` for each email.

This checks if the email matches a CSV file type.
A match creates a `VoyageEmailParser` and calls `process_message()`.
Look in the `csv_email` module for how this works.
"""

from datetime import datetime
import email
import logging
import os

from csv_email import CSVEmailParser, type_accepts_message
from settings import (
	CSV_FOLDER, get_csv_file_types, get_database_client, get_email_client,
	LOGGING_KWARGS
)


logger = logging.getLogger(__name__)


class VoyageEmailParser(CSVEmailParser):

	def __init__(self, database, settings, table_name, subject_values):
		"""
		Create a new voyage CSV email parser.

		Each of the parameters passed into this method are stored in the object.


		Parameters
		----------

		database : object
			Helper class for accessing the database used to store CSV data.

		settings : dict
			Dictionary used to extract data from the CSV email.
			The details are specific to the matched email format.

		table_name : str
			Name of the table in the database to update with CSV rows.

		subject_values : dict
			Values that were extracted from the email subject.
		"""

		self.database = database

		self.table_name = table_name


		# Settings to save a copy of the CSV.
		try:
			save_csv = settings['save_csv']

			file_name_format = save_csv['name_format'].strip()

			# Create the file name from the subject parts.
			file_name = file_name_format.format(**subject_values)

			self.save_file_path = os.path.join(CSV_FOLDER, file_name)

		except KeyError:
			self.save_file_path = None


		# Save details about the expected columns in the CSV.
		self.csv_columns = []

		# Loop each of the CSV column settings.
		for csv_name, details in settings['load_csv_columns'].items():
			# Use the CSV column name if a database field name is not given.
			field_name = details.get('field', csv_name)

			self.csv_columns.append([csv_name, field_name, details])

	def process_csv_content(self, content):
		"""
		Save the CSV to a file and continue processing it.


		Parameters
		----------

		content : str
			Text from the email, processed from the raw format.
		"""

		if self.save_file_path is not None:
			# Write the contents of the CSV to the file.
			with open(self.save_file_path, 'w') as f:
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

		#print(sorted(csv_row.keys()))

		# Stores the field names and values to be inserted into the database.
		fields = {}

		# Loop each of the CSV column details.
		for csv_name, field_name, details in self.csv_columns:
			# Get the value and type from the row or skip to the next column.
			try:
				value = csv_row[csv_name]
				item_type = details['type']
			except KeyError:
				continue

			if 'datetime' == item_type:
				# datetime requires the format text for conversion.
				try:
					csv_format = details['csv_format'].strip()
				except KeyError:
					continue

				# Convert the CSV text value into a datetime value.
				value = datetime.strptime(value, csv_format)

			fields[field_name] = value

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
		match_dict = type_accepts_message(message, csv_type)
		if match_dict is None:
			continue

		logger.debug('Extracted %s from subject.', match_dict)

		save_table = csv_type['save_table']

		# Get the table name template.
		table_name_format = save_table['name_format'].strip()

		# Create the table name from the regex values.
		table_name = table_name_format.format(**match_dict)

		# Create the required table if it does not exist.
		if not database.table_exists(table_name):
			logger.info('Table "%s" does not exist.', table_name)

			columns = csv_type['load_csv_columns']

			database.create_table(table_name, columns)

		else:
			logger.debug('Table "%s" exists.', table_name)

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
	logging.basicConfig(**LOGGING_KWARGS)

	logger.info('Started reading emails.')

	process_emails()

	logger.info('Finished reading emails.')
