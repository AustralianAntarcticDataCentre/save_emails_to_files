"""
Oracle database connector.


Links
-----

- https://cx-oracle.readthedocs.org/en/latest/
"""

import logging
import re

import cx_Oracle


TABLE_CHECK = re.compile(r'^\w+$')

logger = logging.getLogger(__name__)


class DatabaseServer:

	def __init__(self, connection_string):
		self.connection_string = connection_string
		self.con = None

	def __enter__(self):
		self.con = cx_Oracle.connect(self.connection_string)
		return self

	def __exit__(self, type, value, traceback):
		self.con.close()

	def cursor(self):
		return self.con.cursor()

	def table_exists(self, table_name):
		# Make sure the table name given is valid.
		if not TABLE_CHECK.match(table_name):
			raise ValueError('Table name is invalid.')

		logger.debug('Check if "%s" exists.', table_name)

		sql = "SELECT table_name FROM user_tables WHERE table_name = :t"

		cur = self.cursor()
		cur.execute(sql, t=table_name)
		exists = 0 < cur.rowcount
		cur.close()

		return exists
