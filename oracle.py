"""
Oracle database connector.


Links
-----

- https://cx-oracle.readthedocs.org/en/latest/
"""

import logging
import re

import cx_Oracle


COLUMN_CHECK = re.compile(r'^\w+$')
TABLE_CHECK = re.compile(r'^\w+$')

logger = logging.getLogger(__name__)


class DatabaseServer:

	def __init__(self, connection_string):
		self.connection_string = connection_string
		self.con = None

	def __enter__(self):
		"""
		Open a database connection when the `with` statement starts.
		"""

		self.con = cx_Oracle.connect(self.connection_string)
		return self

	def __exit__(self, type, value, traceback):
		"""
		Close the database connection when the `with` statement ends.
		"""

		self.con.close()

	def cursor(self):
		"""
		Create a new database cursor for executing SQL.
		"""

		return self.con.cursor()

	def table_exists(self, table_name):
		"""
		Return True if the given table exists.


		Parameters
		----------

		table_name : str
			Name of the table to find.


		Raises
		------

		ValueError
			If the table name is invalid.


		Returns
		-------

		bool
			True if the table exists, False otherwise.
		"""

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

	def create_table(self, table_name, load_csv):
		"""
		Create a table containing database fields for CSV columns.


		Parameters
		----------

		table_name : str
			Name of the table to create.

		load_csv : dict
			Dictionary of details of CSV columns.


		Raises
		------

		ValueError
			If the table name is invalid.


		Returns
		-------
		dict
			Lookup table fields from CSV column names.
		"""

		# Make sure the table name given is valid.
		if not TABLE_CHECK.match(table_name):
			raise ValueError('Table name is invalid.')

		csv_column_lookup = {}

		columns = load_csv['columns']
		columns_sql_list = []

		for csv_name, details in columns:
			if 'name' in details:
				col_name = details['name']
			else:
				col_name = csv_name

			# Move to the next column if the name is invalid.
			if not COLUMN_CHECK.match(col_name):
				continue

			# Move to the next column if a type was not given.
			if 'type' not in details:
				continue

			col_type = details['type']

			if 'float' == col_type:
				col_sql = 'NUMBER'

			elif 'int' == col_type:
				col_sql = 'NUMBER'

			# Move to the next column if the type is not known.
			else:
				continue

			sql = '{0} {1}'.format(col_name, col_sql)
			columns_sql_list.append(sql)

			csv_column_lookup[csv_name] = col_name

		# Join the column definitions for the CREATE TABLE statement.
		columns_sql = ','.join(columns_sql_list)

		sql = "CREATE TABLE {0} ({1})".format(table_name, columns_sql)

		cur = self.cursor()
		cur.execute(sql)
		cur.close()

		return csv_column_lookup
