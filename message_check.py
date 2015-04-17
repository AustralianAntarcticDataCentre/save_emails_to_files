#!/usr/bin/env python

import email
import logging
import re


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
		logger.debug(message['From'])

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
		subject_regex_list = [s.strip() for s in check['subject_regex']]
		subject_regex_text = ''.join(subject_regex_list)
		subject_regex = re.compile(subject_regex_text)
		check['subject_regex_compiled'] = subject_regex
	else:
		subject_regex_text = subject_regex.pattern

	# Check if the message subject matches the RegEx.
	match_data = subject_regex.match(subject)

	# Skip this message if the subject does not match the RegEx.
	if match_data is None:
		logger.debug('Regex is %s.', subject_regex_text)
		logger.warning('Email subject does not match the required format.')
		return None

	# Return a dict of the values matched in the regex.
	return match_data.groupdict()
