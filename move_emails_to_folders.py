import logging

from csv_email import get_move_folder, type_accepts_message
from settings import get_csv_file_types, get_email_client, LOGGING_KWARGS


logger = logging.getLogger(__name__)


def get_message_folder_name(message, csv_file_types):
	for csv_type in csv_file_types:
		match_dict = type_accepts_message(message, csv_type)
		if match_dict is None:
			continue

		return get_move_folder(csv_type, match_dict)

	return None


def move_messages_from_inbox():
	csv_file_types = get_csv_file_types()

	if csv_file_types is None:
		logger.error('CSV file types could not be read from `settings.yaml`.')
		return False

	with get_email_client() as email_client:
		email_client.select_inbox()

		folder_name_list = [name for name in email_client.loop_folder_names()]

		for message, uid in email_client.loop_email_messages(True):
			logger.debug('Message subject is %s.', message['Subject'])

			folder_name = get_message_folder_name(message, csv_file_types)
			logger.debug('Message folder is %s.', folder_name)

			if folder_name not in folder_name_list:
				continue

			email_client.move_message(uid, folder_name)

	return True


if '__main__' == __name__:
	logging.basicConfig(**LOGGING_KWARGS)

	move_messages_from_inbox()
