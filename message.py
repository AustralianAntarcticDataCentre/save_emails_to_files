"""
Process emails containing CSV data.
"""

import csv
#import email
from io import StringIO
#import logging
import quopri


#logger = logging.getLogger(__name__)


class CSVEmailParser:

	required_columns = None

	def process_message(self, message):
		"""
		Process CSV in an email.

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

		Uses `is_multipart()` and `get_payload()` to recursively call this function,
		and build the message content from the parts.

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
		Process CSV in a string.

		Having this intermediate step between processing the entire CSV file
		and then each of the rows allows another action to happen.

		This may be saving the content to a file as a backup.

		Parameters
		----------

		content : str
		"""

		self.process_csv_file(StringIO(content))


	def process_csv_file(self, content_file):
		"""
		Process CSV in a file.

		Parameters
		----------

		content_file : file object
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
