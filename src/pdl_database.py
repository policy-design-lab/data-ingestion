import logging

import pandas as pd
import psycopg2
from psycopg2 import Error


class PDLDatabase:
    def __init__(self, db_name, db_user, db_password, db_host, db_port):
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        self.connection = None
        self.cursor = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connect(db_name=db_name, db_user=db_user, db_password=db_password, db_host=db_host, db_port=db_port)
        self.create_tables_file = "../queries/create_tables.sql"
        self.initialize_tables_file = "../queries/initialize_tables.sql"

    def connect(self, db_name=None, db_user=None, db_password=None, db_host=None, db_port=None):
        try:
            if db_name is not None:
                self.connection = psycopg2.connect(user=db_user, host=db_host, port=db_port, database=db_name)
            else:
                self.connection = psycopg2.connect(user=db_user, host=db_host, port=db_port)
            self.connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.connection.cursor()
            self.logger.info(self.connection.get_dsn_parameters())
            self.logger.info("Connected to PostgreSQL database!\n")
        except (Exception, Error) as error:
            self.logger.error("Error while connecting to PostgreSQL", error)

    def drop_database(self):
        self.close()
        self.connect(db_name="postgres", db_user=self.db_user, db_password=self.db_password, db_host=self.db_host,
                     db_port=self.db_port)
        self.cursor.execute(f"DROP DATABASE IF EXISTS {self.db_name}")
        self.close()
        self.logger.info(f"Database {self.db_name} dropped successfully")

    def create_database_and_schema(self):
        self.connect(db_user=self.db_user, db_password=self.db_password, db_host=self.db_host, db_port=self.db_port)
        # create database if not exists
        self.cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{self.db_name}'")
        exists = self.cursor.fetchone()
        if not exists:
            self.cursor.execute(f"CREATE DATABASE {self.db_name}")
            self.logger.info(f"Database {self.db_name} created successfully")
        else:
            self.logger.info(f"Database {self.db_name} already exists")

        # close connection
        self.close()

        # connect to the database
        self.connect(db_name=self.db_name, db_user=self.db_user, db_password=self.db_password, db_host=self.db_host)

        # create schema
        self.cursor.execute(f"CREATE SCHEMA IF NOT EXISTS pdl")
        self.connection.commit()
        self.logger.info(f"Schema pdl created successfully or already exists")

    def create_tables(self):
        self._execute_sql_file(self.create_tables_file)
        self.logger.info("Tables created successfully")

    # Function to execute queries from a file
    def _execute_sql_file(self, filename):
        # Open and read the SQL file
        with open(filename, 'r') as file:
            sql_content = file.read()

        # Split the file into individual statements
        sql_statements = sql_content.split(';')

        # Execute each statement
        for statement in sql_statements:
            # Skip any empty statements that result from the split
            if statement.strip() != "":
                try:
                    self.cursor.execute(statement)
                    self.logger.info(f"Statement executed: {statement}")
                    self.connection.commit()
                except psycopg2.DatabaseError as e:
                    self.logger.error(f"An error occurred: {e}")
                    self.connection.rollback()
                except Exception as e:
                    self.logger.error(f"An unexpected error occurred: {e}")
                    self.connection.rollback()

    def initialize_tables(self):
        self._execute_sql_file(self.initialize_tables_file)
        self.logger.info("Tables initialized successfully")

    def insert_data(self, data_frame):
        # Iterate through the Pandas data frame and insert/update data into the tables
        for index, row in data_frame.iterrows():
            if row['entity_type'] == 'subtitle':
                # Find the title id, and the subtitle id from the subtitles table
                sql_select_query = "SELECT title_id, id as subtitle_id FROM pdl.subtitles WHERE name = %s"
                self.cursor.execute(sql_select_query, (row['entity_name'],))
                result = self.cursor.fetchone()
                if result:
                    title_id, subtitle_id = result
                    # Insert/update data into the payments table
                    sql_insert_query = (
                        "INSERT INTO pdl.payments (title_id, subtitle_id, program_id, sub_program_id, state_code, year, payment, recipient_count, base_acres) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ")
                    # "ON CONFLICT (title_id, subtitle_id, program_id, sub_program_id, state_code, year) DO UPDATE SET payment = EXCLUDED.payment")
                    self.cursor.execute(sql_insert_query,
                                        (title_id, subtitle_id, None, None, row["state_code"], row['year'],
                                         row['amount'],
                                         row['recipient_count'] if 'recipient_count' in row and not pd.isna(
                                             row['recipient_count']) else None,
                                         row['base_acres'] if 'base_acres' in row and not pd.isna(
                                             row['base_acres']) else None))
            elif row['entity_type'] == 'program':
                # Find the program id, title id, and the subtitle id from the program table
                sql_select_query = "SELECT id, title_id, subtitle_id FROM pdl.programs WHERE name = %s"
                self.cursor.execute(sql_select_query, (row['entity_name'],))
                result = self.cursor.fetchone()
                if result:
                    program_id, title_id, subtitle_id = result
                    # Insert/update data into the payments table
                    sql_insert_query = (
                        "INSERT INTO pdl.payments (title_id, subtitle_id, program_id, sub_program_id, state_code, year, payment, recipient_count, base_acres) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ")
                    # "ON CONFLICT (title_id, subtitle_id, program_id, sub_program_id, state_code, year) DO UPDATE SET payment = EXCLUDED.payment")
                    self.cursor.execute(sql_insert_query,
                                        (title_id, subtitle_id, program_id, None, row["state_code"], row['year'],
                                         row['amount'],
                                         row['recipient_count'] if 'recipient_count' in row and not pd.isna(
                                             row['recipient_count']) else None,
                                         row['base_acres'] if 'base_acres' in row and not pd.isna(
                                             row['base_acres']) else None))
            elif row['entity_type'] == 'sub_program':
                # Find the program id, title id, subtitle id, and sub_program id from joining sub_programs, programs, and titles
                # tables
                sql_select_query = "SELECT p.id, p.title_id, p.subtitle_id, s.id FROM pdl.programs p JOIN pdl.sub_programs s ON p.id = s.program_id WHERE s.name = %s"
                self.cursor.execute(sql_select_query, (row['entity_name'],))
                result = self.cursor.fetchone()
                if result:
                    program_id, title_id, subtitle_id, sub_program_id = result
                    # Insert/update data into the payments table
                    sql_insert_query = (
                        "INSERT INTO pdl.payments (title_id, subtitle_id, program_id, sub_program_id, state_code, year, payment, recipient_count, base_acres) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ")
                    # "ON CONFLICT (title_id, subtitle_id, program_id, sub_program_id, state_code, year) DO UPDATE SET payment = EXCLUDED.payment")
                    self.cursor.execute(sql_insert_query,
                                        (title_id, subtitle_id, program_id, sub_program_id, row["state_code"],
                                         row['year'],
                                         row['amount'],
                                         row['recipient_count'] if 'recipient_count' in row and not pd.isna(
                                             row['recipient_count']) else None,
                                         row['base_acres'] if 'base_acres' in row and not pd.isna(
                                             row['base_acres']) else None))

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            self.logger.info("PostgreSQL connection is closed")
