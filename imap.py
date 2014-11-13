"""
Read voyage data emails.
"""

import email
from imaplib import IMAP4_SSL
import logging


OK = 'OK'

logger = logging.getLogger(__name__)


class EmailCheckError(Exception):
	pass


def connect_to_server(server):
	return IMAP4_SSL(server)


def login_to_account(mail, username, password):
	logger.debug('Start login_to_account(%s).', username)

	mail.login(username, password)
	logger.info('Login as "%s" worked.', username)


def select_inbox(mail):
	logger.debug('Start select_inbox().')

	ok, mail_count_list = mail.select('INBOX')
	if ok != OK:
		raise EmailCheckError('Failed checking inbox.')

	try:
		mail_count = int(mail_count_list[0])
	except ValueError as e:
		raise EmailCheckError('Mail count conversion failed.') from e

	logger.info('Found %s items in the inbox.', mail_count)


def get_uid_list(mail):
	logger.debug('Start get_uid_list().')

	select_inbox(mail)

	#ok, data = mail.search(None, 'ALL')
	ok, raw_uid_list = mail.uid('search', None, 'ALL')
	if ok != OK:
		raise EmailCheckError('Failed searching mail.')

	try:
		uid_list = raw_uid_list[0].split()
	except ValueError as e:
		raise EmailCheckError('Mail count conversion failed.') from e

	return uid_list


def get_email_message(mail, uid):
	logger.debug('Start get_email_message(%s).', uid)

	ok, data = mail.uid('fetch', uid, '(RFC822)')
	if ok != OK:
		raise EmailCheckError('Failed fetching message.')

	# data[0][0] == '1 (RFC822 {25644}'
	# data[0][1] is a string containing the email headers and body.

	logger.debug('Convert email from bytes.')
	raw_email_bytes = data[0][1]
	#raw_email_str = raw_email_bytes.decode('utf-8')
	#return email.message_from_string(raw_email_str)
	return email.message_from_bytes(raw_email_bytes)


def loop_email_messages(mail):
	logger.debug('Start loop_email_messages().')

	try:
		uid_list = get_uid_list(mail)
	except EmailCheckError as e:
		logger.error(e.args[0])
		raise e

	for uid in uid_list:
		yield get_email_message(mail, uid)
