#!/usr/bin/env python

import logging
import quopri


logger = logging.getLogger(__name__)


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

	logger.debug('Start getting message content.')

	raw_content = get_message_content(message)

	logger.debug('Decoding message content to bytes.')

	content_bytes = quopri.decodestring(raw_content, False)

	logger.debug('Decoding message bytes to text.')

	return content_bytes.decode('utf-8')
