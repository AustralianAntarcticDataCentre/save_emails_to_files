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


class EmailServer:

	def __init__(self, server, username, password):
		self.password = password
		self.server = server
		self.username = username

	def __enter__(self):
		self.mail = IMAP4_SSL(self.server)

		logger.debug('Attempting to login as "%s".', self.username)

		self.mail.login(self.username, self.password)

		logger.debug('Login as "%s" worked.', self.username)

		return self

	def __exit__(self, type, value, traceback):
		#self.mail.close()
		pass

	def select_inbox(self):
		"""
		Access the inbox.


		Raises
		------

		EmailCheckError
			If the inbox cannot be accessed or the message count fails.


		Returns
		-------

		None
		"""

		logger.debug('Attempting to access the inbox.')

		ok, mail_count_list = self.mail.select('INBOX')
		if ok != OK:
			raise EmailCheckError('Failed selecting the inbox.')

		try:
			mail_count = int(mail_count_list[0])
		except ValueError as e:
			raise EmailCheckError('Failed to get the message count.') from e

		logger.info('Found %s items in the inbox.', mail_count)

	def get_uid_list(self):
		"""
		Return the message UID list.

		Each UID can be used to access the correct message, even if the mailbox
		changes after this call.


		Raises
		------

		EmailCheckError
			If the UID list request fails or the list cannot be split into
			values.


		Returns
		-------

		list
			List of UID integers.
		"""

		logger.debug('Attempting to get the message UID list.')

		self.select_inbox()

		#ok, data = mail.search(None, 'ALL')
		ok, raw_uid_list = self.mail.uid('search', None, 'ALL')
		if ok != OK:
			raise EmailCheckError('Failed searching mail.')

		try:
			uid_list = raw_uid_list[0].split()
		except ValueError as e:
			raise EmailCheckError('Mail count conversion failed.') from e

		return uid_list

	def get_email_message(self, uid):
		logger.debug('Start get_email_message(%s).', uid)

		ok, data = self.mail.uid('fetch', uid, '(RFC822)')
		if ok != OK:
			raise EmailCheckError('Failed fetching message.')

		# data[0][0] == '1 (RFC822 {25644}'
		# data[0][1] is a string containing the email headers and body.

		logger.debug('Convert email from bytes.')

		raw_email_bytes = data[0][1]
		#raw_email_str = raw_email_bytes.decode('utf-8')

		#return email.message_from_string(raw_email_str)
		return email.message_from_bytes(raw_email_bytes)

	def loop_email_messages(self):
		"""
		Generate email messages from the current mailbox.

		Yields the message from `get_email_message()` for each UID.

		>>> for message in loop_email_messages(mail):
		...     print(message)


		Raises
		------

		EmailCheckError
			If the UID list request fails.
		"""

		logger.debug('Attempting to get the UID list.')

		try:
			uid_list = self.get_uid_list()
		except EmailCheckError as e:
			logger.error(e.args[0])
			raise e

		logger.debug('Start looping UID list.')

		for uid in uid_list:
			yield self.get_email_message(uid)

		logger.debug('Finished looping UID list.')
