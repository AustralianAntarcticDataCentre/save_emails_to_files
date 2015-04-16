#!/usr/bin/env python
"""
Download email contents to files.

Running this as a script calls `process_emails()`.
This uses `get_email_client()` to open an email server connection and
then `get_file_types()` to check which email to save.
"""

import logging
import os
import re

from message_check import check_message, get_email_folders
from message_content import get_message_text
from settings import (
	SAVE_FOLDER, get_file_types, get_email_client, LOGGING_KWARGS
)


logger = logging.getLogger(__name__)


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
		folders = get_email_folders(email_client)

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
