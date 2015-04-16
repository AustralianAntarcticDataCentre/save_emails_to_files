#!/usr/bin/env python
"""
Print subject of any message that fails all checks.
"""

import logging

from message_check import check_message, get_email_folders
from settings import get_file_types, get_email_client, LOGGING_KWARGS


logger = logging.getLogger(__name__)


def find_failures():
	file_types = get_file_types()

	if file_types is None:
		logger.error('File types could not be read from settings.')
		return

	with get_email_client() as email_client:
		folders = get_email_folders(email_client)

		for folder_name in folders:
			email_client.select_folder(folder_name)

			for message in email_client.loop_messages():
				if not message_matched(message, file_types):
					subject = message['Subject']
					print(subject)


def message_matched(message, all_checks):
	"""
	Return True if message passes any of the checks.


	Parameters
	----------

	message : email.message.Message
		Message to be checked.

	all_checks : list
		List of dictionaries containing checks and settings for the different
		types of emails that can be saved.


	Returns
	-------

	bool
		True if the message matched any of the checks, False otherwise.
	"""

	for check_details in all_checks:
		match_dict = check_message(message, check_details)

		if match_dict is not None:
			return True

	return False


if '__main__' == __name__:
	logging.basicConfig(**LOGGING_KWARGS)

	logger.info('Started checking emails.')

	find_failures()

	logger.info('Finished checking emails.')
