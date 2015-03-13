"""
Download email contents to files.

Running this as a script calls `process_emails()`.
This uses `get_email_client()` to open an email server connection and
then `get_file_types()` to check which email to save.
"""

import email
import logging
import os
import quopri
import re

from settings import (
	EMAIL_FOLDER_RE, SAVE_FOLDER, get_file_types, get_email_client,
	LOGGING_KWARGS
)


logger = logging.getLogger(__name__)


def check_message(message, check_details):
	"""
	Check if the message can be parsed with the given details.


	Parameters
	----------

	message : email.message.Message
		https://docs.python.org/3.4/library/email.message.html#email.message.Message

	check_details : dict
		Contains checks and settings for the given message.


	Returns
	-------

	dict
		Dictionary of match details extracted from the message.
	"""

	check = check_details.get('check')

	if check is None:
		return None


	if 'from' in check:
		# parseaddr() splits "From" into name and address.
		# https://docs.python.org/3/library/email.util.html#email.utils.parseaddr
		email_from = email.utils.parseaddr(message['From'])[1]

		logger.debug('Email is from "%s".', email_from)

		required_from = check['from']

		# Skip this message if it did not come from the correct sender.
		if email_from != required_from:
			msg = 'Email is not from the correct sender (%s != %s).'
			logger.warning(msg, email_from, required_from)
			return None


	subject = message['Subject']

	logger.debug('Email subject is "%s".', subject)

	# Use the compiled RegEx if it is available.
	subject_regex = check.get('subject_regex_compiled')

	# Compile and save the RegEx otherwise.
	if subject_regex is None:
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


def get_message_content(message):
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
		Raw content of the message that needs to be decoded.
	"""

	if not message.is_multipart():
		return message.get_payload()

	parts = [
		get_message_content(payload)
		for payload in message.get_payload()
	]

	return ''.join(parts)


def get_message_text(message):
	"""
	Get text content from an email message.

	Uses `get_message_content()` to get the raw mail content.


	Parameters
	----------

	message : email.message.Message
		https://docs.python.org/3.4/library/email.message.html#email.message.Message
	"""

	raw_content = get_message_content(message)

	content_bytes = quopri.decodestring(raw_content, False)

	return content_bytes.decode('utf-8')


def process_emails():
	"""
	Connect to the email server and check for messages to save.


	Returns
	-------

	bool
		False if settings cannot be loaded.
	"""

	file_types = get_file_types()

	if file_types is None:
		logger.error('File types could not be read from settings.')
		return False

	with get_email_client() as email_client:
		#email_client.select_folder(email_client.INBOX)

		folders = [
			name
			for name in email_client.loop_folder_names()
			if EMAIL_FOLDER_RE.match(name) is not None
		]

		#folders = []
		#for name in email_client.loop_folder_names():
			#match_data = EMAIL_FOLDER_RE.match(name)
			#if match_data is not None:
				#folders.append(name)

		for folder_name in folders:
			email_client.select_folder(folder_name)

			for message in email_client.loop_messages():
				process_message(message, file_types)

	return True


def process_message(message, all_checks):
	"""
	Check and save a message if it matches one of the checks.


	Parameters
	----------

	message : email.message.Message
		Message (hopefully) with CSV content to be processed.

	all_checks : list
		List of dictionaries containing checks and settings for the different
		types of emails that should be saved.


	Returns
	-------

	bool
		True if the message was processed, False if no handler could be found.
	"""

	for check_i, check_details in enumerate(all_checks):
		match_dict = check_message(message, check_details)

		if match_dict is None:
			continue

		logger.debug('Extracted %s from message.', match_dict)

		try:
			file_name_format = check_details['save_file_format'].strip()
		except KeyError:
			logger.error('Check %s does not contain file format.', check_i + 1)
			continue

		# Create the file name from the format settings and matched details.
		file_name = file_name_format.format(**match_dict)

		save_file_path = os.path.join(SAVE_FOLDER, file_name)

		# Check if the email has already been saved.
		if os.path.exists(save_file_path):
			logger.info('File %s already exists.', save_file_path)
			return True

		# Get the parent folder path.
		folder_path = os.path.dirname(save_file_path)

		# Create the folder path if it does not exist already.
		if not os.path.exists(folder_path):
			os.makedirs(folder_path)

		save_message_to_file(message, save_file_path)

		# No need to check other CSV parsers once one is complete.
		return True

	# Returns False if none of the checks matched the given message.
	return False


def save_message_to_file(message, file_path):
	"""
	Process a message containing CSV voyage data.


	Parameters
	----------

	message : email.message.Message
		Message with content to be saved.

	file_path : str
		Full file path to save the message contents to.
	"""

	content = get_message_text(message)

	# Write the contents of the CSV to the file.
	with open(file_path, 'w') as f:
		f.write(content)


if '__main__' == __name__:
	logging.basicConfig(**LOGGING_KWARGS)

	logger.info('Started reading emails.')

	process_emails()

	logger.info('Finished reading emails.')
