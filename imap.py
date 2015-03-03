"""
Read voyage data emails.

	>>> with EmailAccount('imap4.example.com', 'my_user', 'my_pass') as acc:
	>>>     acc.select_inbox()
	>>>     for message in acc.loop_email_messages():
	...         print(message['From'])
	...         print(message['Subject'])
"""

import email
import imaplib
import logging
import re


OK = 'OK'

logger = logging.getLogger(__name__)

# http://stackoverflow.com/questions/25457441/reading-emails-with-imaplib-got-more-than-10000-bytes-error
imaplib._MAXLINE = 40000

# Matches the folder details format used by IMAP.
folder_regex = re.compile('\((?P<start>[^)]+)\) "/" "?(?P<folder>.+)"?$')


class EmailCheckError(Exception):
	pass


class EmailAccount:

	def __init__(self, server, username, password):
		self.password = password
		self.server = server
		self.username = username

	def __enter__(self):
		self.mail = imaplib.IMAP4_SSL(self.server)

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

		# Raises "imaplib.error: got more than 10000 bytes" when the mailbox
		# contains too many messages.
		#ok, data = self.mail.search(None, 'ALL')
		ok, raw_uid_list = self.mail.uid('search', None, 'ALL')
		if ok != OK:
			raise EmailCheckError('Failed searching mail.')

		try:
			uid_list = raw_uid_list[0].split()
		except ValueError as e:
			raise EmailCheckError('Mail count conversion failed.') from e

		return uid_list

	def get_email_message(self, uid):
		logger.debug('Get email message with UID %s.', uid)

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


		Raises
		------

		EmailCheckError
			If the UID list request fails.
		"""

		try:
			uid_list = self.get_uid_list()
		except EmailCheckError as e:
			logger.error(e.args[0])
			raise e

		logger.debug('Start looping UID list.')

		for uid in uid_list:
			yield self.get_email_message(uid)

		logger.debug('Finished looping UID list.')

	def loop_folder_names(self):
		"""
		Generates all folder names on the mail server.


		Raises
		------

		EmailCheckError
			If the folders cannot be listed.
		"""

		ok, folders = self.mail.list()
		if ok != OK:
			raise EmailCheckError('Failed to list the folders.')

		for folder_details_bytes in folders:
			folder_details = folder_details_bytes.decode('utf-8')
			logger.info('Reading folder %s', folder_details)

			match_data = folder_regex.match(folder_details)

			if match_data is None:
				logger.warning('Folder %s does not match format.', folder_details)
				continue

			folder_name = match_data.groupdict()['folder']

			yield folder_name

	def move_message(self, uid, folder):
		"""
		Move a message to a different folder.
		"""

		#ok, result = self.mail.uid('copy', uid, folder)
		#ok, result = self.mail.expunge()
		pass
