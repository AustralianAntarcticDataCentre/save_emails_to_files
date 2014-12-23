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

# Uses lambdas in case extra settings are required to define the type.
COLUMN_TYPE = dict(
	datetime=lambda settings: 'TIMESTAMP',
	float=lambda settings: 'NUMBER',
	int=lambda settings: 'INTEGER',
)

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
		self.con.autocommit = True
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
		exists = cur.fetchone() is not None
		cur.close()

		return exists

	def create_table(self, table_name, columns):
		"""
		Create a table containing database fields for CSV columns.


		Parameters
		----------

		table_name : str
			Name of the table to create.

		columns : dict
			Details on the CSV columns.


		Raises
		------

		ValueError
			If the table name is invalid.
		"""

		# Make sure the table name given is valid.
		if not TABLE_CHECK.match(table_name):
			raise ValueError('Table name is invalid.')

		csv_column_lookup = {}

		columns_sql_list = []

		# Loop each of the CSV column types defined in the settings.
		for csv_name, details in columns.items():
			# Update the CSV column name if another was given.
			csv_name = details.get('csv', csv_name)

			# Use the CSV column name if a database name is not given.
			col_name = details.get('field', csv_name)

			# Ensure the column name is valid.
			if not COLUMN_CHECK.match(col_name):
				continue

			# Ensure a type name was given.
			if 'type' not in details:
				continue

			col_type_maker = COLUMN_TYPE.get(details['type'])

			# Ensure an SQL type can be created.
			if col_type_maker is None:
				continue

			# Get the SQL to define this column type.
			col_type_sql = col_type_maker(details)

			# Add the column name and type in the SQL create table format.
			sql = '{0} {1}'.format(col_name, col_type_sql)
			columns_sql_list.append(sql)

		# Join the column definitions for the CREATE TABLE statement.
		columns_sql = ','.join(columns_sql_list)

		sql = "CREATE TABLE {0} ({1})".format(table_name, columns_sql)

		logger.debug(sql)

		cur = self.cursor()
		cur.execute(sql)
		cur.close()

	def insert_row(self, table_name, fields):
		"""
		Insert the values into the table.
		"""

		# Make sure the table name given is valid.
		if not TABLE_CHECK.match(table_name):
			raise ValueError('Table name is invalid.')

		#pairs = list(fields.items())
		#names, values = list(zip(*pairs))

		names = []
		values = []

		for name in fields.keys():
			if not COLUMN_CHECK.match(name):
				continue

			names.append(name)
			values.append(':' + name)

		names_sql = ','.join(names)
		values_sql = ','.join(values)

		sql_base = 'INSERT INTO {0} ({1}) VALUES ({2})'
		sql = sql_base.format(table_name, names_sql, values_sql)

		cur = self.cursor()
		cur.execute(sql, fields)
		cur.close()
