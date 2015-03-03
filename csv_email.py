"""
Process emails containing CSV data.

The CSVEmailParser class requires the implementor to provide it with
email messages.
It does not contain any code for accessing email accounts.
"""

import csv
import email
from io import StringIO
import logging
import quopri
import re


logger = logging.getLogger(__name__)


class CSVEmailParser:

	required_columns = None

	def process_message(self, message):
		"""
		Process CSV in an email.

		Uses `self.get_message_content()` to get the raw mail content.

		Calls `self.process_csv_content()` with the decoded mail content as the
		last step in this method.


		Parameters
		----------

		message : email.message.Message
			https://docs.python.org/3.4/library/email.message.html#email.message.Message
		"""

		raw_content = self.get_message_content(message)

		content_bytes = quopri.decodestring(raw_content, False)

		content = content_bytes.decode('utf-8')

		self.process_csv_content(content)


	def get_message_content(self, message):
		"""
		Get message content from an email.

		Uses `is_multipart()` and `get_payload()` to recursively call this
		function and build the message content from the parts.


		Parameters
		----------

		message : email.message.Message
			https://docs.python.org/3.4/library/email.message.html#email.message.Message


		Returns
		-------

		str
			Body of the message as a string.
		"""

		if not message.is_multipart():
			return message.get_payload()

		parts = [
			self.get_message_content(payload)
			for payload in message.get_payload()
		]

		return ''.join(parts)


	def process_csv_content(self, content):
		"""
		Process CSV from a string.

		Having this intermediate step between processing the entire CSV file
		and then each of the rows allows another action to happen.

		This may be saving the content to a file as a backup.


		Parameters
		----------

		content : str
			Decoded mail content text containing only CSV.
		"""

		self.process_csv_file(StringIO(content))


	def process_csv_file(self, content_file):
		"""
		Process CSV in a file.

		Creates a `csv.DictReader` from the file and loops over rows contained
		within it.

		Uses `self.check_row_is_valid()` on each row, which throws an exception
		if it fails.

		Calls `self.process_csv_row()` if the row is valid.


		Parameters
		----------

		content_file : file object
			This could be `open(file_name)` or `StringIO(text)`.
		"""

		with content_file as f:
			reader = csv.DictReader(f)
			for row in reader:
				# This will throw an error if the columns are missing.
				self.check_row_is_valid(row)

				self.process_csv_row(row)


	def check_row_is_valid(self, row):
		"""
		Check that required columns exist in the row.

		Column names are case-sensitive.


		Parameters
		----------

		row : dict
			Column names and their values.


		Raises
		------

		KeyError
			If a required column is missing.
		"""

		if self.required_columns is not None:
			# Make sure all the required columns are in the row.
			for column_name in self.required_columns:
				if column_name not in row:
					raise KeyError('Missing column "%s"', column_name)


	def process_csv_row(self, row):
		"""
		Process a single row of CSV content.

		This method should be replaced in a subclass to do something useful.


		Parameters
		----------

		row : dict
			Column names and their values.
		"""

		pass


def type_accepts_message(message, csv_type):
	email_from = email.utils.parseaddr(message['From'])[1]

	subject = message['Subject']

	check = csv_type['check']

	required_from = check['from']

	# Skip this message if it did not come from the correct sender.
	if email_from != required_from:
		msg = 'Email is not from the correct sender (%s != %s).'
		logger.warning(msg, email_from, required_from)
		return None

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
		return None

	# Get a dict of the values matched in the regex.
	return match_data.groupdict()
