#!/usr/bin/env python
"""
Download email contents to files.

Running this as a script calls `process_emails()`.
This uses `get_email_server()` to open an email server connection and
then `get_all_checks()` to check which emails to save.
"""

import logging
import os
import re

from message_check import check_message
from message_content import get_message_text
from settings import (
	SAVE_FOLDER, get_all_checks, get_email_server, LOGGING_KWARGS
)


logger = logging.getLogger(__name__)


def all_checks_on_message(message, all_checks):
	"""
	Return details if the message matches one of the checks.

	If no check matches the message then None is returned.


	Parameters
	----------

	all_checks : list
		List of dictionaries containing check settings for the different types
		of emails.

	message : email.message.Message
		Message to be checked.


	Returns
	-------

	None
	tuple(dict, dict)
		Tuple with the matching check and the values from the match.
	"""

	for check_i, settings in enumerate(all_checks):
		logger.debug('Check %s on message.', check_i)

		match_values = check_message(message, settings)

		# Continue on next check if this one failed to match.
		if match_values is None:
			continue

		logger.debug('Extracted %s from message.', match_values)

		# Return the matched check and the values from it.
		return (settings, match_values)

	# Returns None if none of the checks matched the given message.
	return None


def get_message_file_path(settings, values):
	"""
	Return the file path where a message should be saved.


	Parameters
	----------

	settings : dict
		Dictionary of settings that matched this message.

	values : dict
		Dictionary of values gathered from the match.


	Raises
	------

	KeyError
		Raised if `save_file_format` is not in the settings.


	Returns
	-------

	str
		File path to where the message should be saved.
	"""

	rel_path_format = settings['save_file_format'].strip()

	# Create the file path from the format settings and matched details.
	rel_path = rel_path_format.format(**values)

	return os.path.join(SAVE_FOLDER, rel_path)


def get_message_mail_folder(settings, values):
	"""
	Return the mail server folder path where a message should be moved.


	Parameters
	----------

	settings : dict
		Dictionary of settings that matched this message.

	values : dict
		Dictionary of values gathered from the match.


	Raises
	------

	KeyError
		Raised if `move_message_to` is not in the settings.


	Returns
	-------

	str
		Folder where the message should be moved.
	"""

	folder_format = settings['move_message_to'].strip()

	# Create the folder path from the format settings and matched values.
	return folder_format.format(**values)


def move_message_to_folder(server, uid, settings, values):
	"""
	Move the given message to a different folder on the server.


	Parameters
	----------

	server : imap.EmailAccount
		Connection to the email server.

	settings : dict
		Dictionary of settings that matched this message.

	uid : int
		UID of the message on the email server.

	values : dict
		Dictionary of values gathered from the match.


	Returns
	-------

	bool
		True if the message was moved to the folder, False otherwise.
	"""

	try:
		folder_path = get_message_mail_folder(settings, values)
	except KeyError:
		logger.error('Settings does not contain a folder format.')
		return False

	server.move_message(uid, folder_path)

	return True


def process_emails():
	"""
	Connect to the email server and check for matching messages.

	If a message matches one of the checks then it is saved locally and the
	message is moved to another folder on the server.


	Returns
	-------

	bool
		True if all messages were processed.
	"""

	all_checks = get_all_checks()

	if all_checks is None:
		logger.error('Message checks could not be loaded.')
		return False

	# Open a connection to the mail server.
	with get_email_server() as server:
		# Ensure current folder is the inbox.
		server.select_folder(server.INBOX)

		# Loop messages in the inbox.
		for message, uid in server.loop_messages(True):
			# Check message is valid (matched) for saving.
			result = all_checks_on_message(message, all_checks)

			# Continue with next message if current one failed to match.
			if result is None:
				continue

			# Get the match details and the values extracted from these.
			settings, values = result

			# Save message to the local file system.
			save_message_to_file(message, settings, values)

			# Move message to another folder on the mail server.
			move_message_to_folder(server, uid, settings, values)

	return True


def save_message_to_file(message, settings, values):
	"""
	Save the given message to the local file system.


	Parameters
	----------

	message : email.message.Message
		Message with content to be saved.

	settings : dict
		Dictionary of settings that matched this message.

	values : dict
		Dictionary of values gathered from the match.


	Returns
	-------

	bool
		True if the message is saved.
	"""

	# Get the file path to where the message should be saved.
	try:
		file_path = get_message_file_path(settings, values)
	except KeyError:
		logger.error('Check does not contain file format.')
		return False

	# Check if the email has already been saved.
	if os.path.exists(file_path):
		logger.info('File %s already exists.', file_path)
		return True

	# Get the parent folder path from the file path.
	folder_path = os.path.dirname(file_path)

	# Create the folder path if it does not exist already.
	if not os.path.exists(folder_path):
		os.makedirs(folder_path)

	# Get the text content of the message.
	content = get_message_text(message)

	# Write the contents of the CSV to the file.
	with open(file_path, 'w') as f:
		f.write(content)

	return True


if '__main__' == __name__:
	logging.basicConfig(**LOGGING_KWARGS)

	logger.info('Started reading emails.')

	process_emails()

	logger.info('Finished reading emails.')
