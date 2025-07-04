import logging
import re

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
        self.create_tables_file = "../queries/create_tables.sql"
        self.initialize_tables_file = "../queries/initialize_tables.sql"
        self.merged_practice_standards = "../data/common/merged_practice_standards.csv"

    def connect(self, db_name=None, db_user=None, db_password=None, db_host=None, db_port=None):
        try:
            if db_name is not None:
                # Use password if provided through command line argument
                if db_password is not None:
                    self.connection = psycopg2.connect(user=db_user, password=db_password, host=db_host, port=db_port,
                                                       database=db_name)
                else:
                    self.connection = psycopg2.connect(user=db_user, host=db_host, port=db_port, database=db_name)
            else:
                # Use password if provided through command line argument
                if db_password is not None:
                    self.connection = psycopg2.connect(user=db_user, password=db_password, host=db_host, port=db_port)
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

    def create_database(self):
        self.connect(db_name="postgres", db_user=self.db_user, db_password=self.db_password, db_host=self.db_host,
                     db_port=self.db_port)
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
        self.connect(db_name=self.db_name, db_user=self.db_user, db_password=self.db_password, db_host=self.db_host,
                     db_port=self.db_port)

    def create_schema(self, schema_name):
        # create schema
        self.cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        self.connection.commit()
        self.logger.info(f"Schema {schema_name} created successfully or already exists")

    def create_tables(self, schema_name):
        self._execute_sql_file(self.create_tables_file, schema_name)
        self.logger.info("Tables created successfully")

    # Function to execute queries from a file
    def _execute_sql_file(self, filename, schema_name):
        # Open and read the SQL file
        with open(filename, 'r') as file:
            sql_content = file.read()

        # Replace all occurrences of ${SCHEMA} with schema_name
        sql_content = sql_content.replace('${SCHEMA}', schema_name)

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

    def initialize_tables(self, schema_name):
        self._execute_sql_file(self.initialize_tables_file, schema_name)

        # Initialize practice standards
        with open(self.merged_practice_standards, 'r') as file:
            data_frame = pd.read_csv(file)
            sql_insert_query = (f"INSERT INTO {schema_name}.practices (code, name, display_name, source) VALUES (%s, %s, %s, %s) "
                                "ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, display_name = EXCLUDED.display_name, source = EXCLUDED.source")

            for index, row in data_frame.iterrows():
                display_name = row['practice_name'] + " (" + row['practice_code'] + ")"
                self.cursor.execute(sql_insert_query,
                                    (row['practice_code'], row['practice_name'], display_name, row['source']))
                self.connection.commit()

        self.logger.info("Tables initialized successfully")

    def insert_data(self, data_frame, schema_name):
        total_rows = len(data_frame)
        # Iterate through the Pandas data frame and insert data into the tables
        for index, row in data_frame.iterrows():
            if index % 100 == 0:
                self.logger.info(f"Inserting row {index} of {total_rows} into the database")

            if row['entity_type'] == 'subtitle':
                # Find the title id, and the subtitle id from the subtitles table
                sql_select_query = f"SELECT title_id, id as subtitle_id FROM {schema_name}.subtitles WHERE name = %s"
                self.cursor.execute(sql_select_query, (row['entity_name'],))
                result = self.cursor.fetchone()
                if result:
                    title_id, subtitle_id = result
                    # Insert data into the payments table
                    sql_insert_query = (
                        f"INSERT INTO {schema_name}.payments (title_id, subtitle_id, program_id, sub_program_id, state_code, year, payment, recipient_count, contract_count, base_acres, farm_count) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ")
                    # "ON CONFLICT (title_id, subtitle_id, program_id, sub_program_id, state_code, year) DO UPDATE SET payment = EXCLUDED.payment")
                    self.cursor.execute(sql_insert_query,
                                        (title_id, subtitle_id, None, None, row["state_code"], row['year'],
                                         row['amount'],
                                         row['recipient_count'] if 'recipient_count' in row and not pd.isna(
                                             row['recipient_count']) else None,
                                         row['contract_count'] if 'contract_count' in row and not pd.isna(
                                             row['contract_count']) else None,
                                         row['base_acres'] if 'base_acres' in row and not pd.isna(
                                             row['base_acres']) else None,
                                         row['farm_count'] if 'farm_count' in row and not pd.isna(
                                             row['farm_count']) else None))
            elif row['entity_type'] == 'program':
                # Find the program id, title id, and the subtitle id from the program table
                sql_select_query = f"SELECT id, title_id, subtitle_id FROM {schema_name}.programs WHERE name = %s"
                self.cursor.execute(sql_select_query, (row['entity_name'],))
                result = self.cursor.fetchone()

                if result:
                    program_id, title_id, subtitle_id = result

                    practice_category_id = None
                    # Find practice_category_id from practice_categories table
                    if "practice_category" in row and not pd.isna(row["practice_category"]):
                        sql_select_query = f"SELECT id FROM {schema_name}.practice_categories WHERE name = %s AND program_id = %s"
                        self.cursor.execute(sql_select_query, (row['practice_category'], program_id))
                        practice_category_id = self.cursor.fetchone()[0]

                    # Insert data into the payments table
                    sql_insert_query = (
                        f"INSERT INTO {schema_name}.payments (title_id, subtitle_id, program_id, sub_program_id, practice_category_id, state_code, year, "
                        "payment, recipient_count, base_acres, farm_count, contract_count, practice_code, practice_code_variant, premium_policy_count, "
                        "liability_amount, premium_amount, premium_subsidy_amount, indemnity_amount, farmer_premium_amount, loss_ratio, net_farmer_benefit_amount) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    )
                    # "ON CONFLICT (title_id, subtitle_id, program_id, sub_program_id, state_code, year) DO UPDATE SET payment = EXCLUDED.payment")

                    practice_code_filtered = None
                    if "practice_code" in row and not pd.isna(row["practice_code"]):
                        # If practice code contain a three-digit code, extract that. Otherwise, use the entire string
                        if re.search(r'\d{3}', str(row["practice_code"])):
                            practice_code_filtered = re.search(r'\d{3}', str(row["practice_code"])).group()
                        else:
                            practice_code_filtered = row["practice_code"]

                    self.cursor.execute(sql_insert_query,
                                        (title_id, subtitle_id, program_id, None, practice_category_id,
                                         row["state_code"], row['year'],
                                         row['amount'] if 'amount' in row and not pd.isna(row['amount']) else None,
                                         row['recipient_count'] if 'recipient_count' in row and not pd.isna(
                                             row['recipient_count']) else None,
                                         row['base_acres'] if 'base_acres' in row and not pd.isna(
                                             row['base_acres']) else None,
                                         row['farm_count'] if 'farm_count' in row and not pd.isna(
                                             row['farm_count']) else None,
                                         row['contract_count'] if 'contract_count' in row and not pd.isna(
                                             row['contract_count']) else None,
                                         practice_code_filtered,
                                         str(row['practice_code']) if 'practice_code' in row and not pd.isna(
                                             row['practice_code']) else None,
                                         row['premium_policy_count'] if 'premium_policy_count' in row and not pd.isna(
                                             row['premium_policy_count']) else None,
                                         row['liability_amount'] if 'liability_amount' in row and not pd.isna(
                                             row['liability_amount']) else None,
                                         row['premium_amount'] if 'premium_amount' in row and not pd.isna(
                                             row['premium_amount']) else None,
                                         row[
                                             'premium_subsidy_amount'] if 'premium_subsidy_amount' in row and not pd.isna(
                                             row['premium_subsidy_amount']) else None,
                                         row['indemnity_amount'] if 'indemnity_amount' in row and not pd.isna(
                                             row['indemnity_amount']) else None,
                                         row['farmer_premium_amount'] if 'farmer_premium_amount' in row and not pd.isna(
                                             row['farmer_premium_amount']) else None,
                                         row['loss_ratio'] if 'loss_ratio' in row and not pd.isna(
                                             row['loss_ratio']) else None,
                                         row[
                                             'net_farmer_benefit_amount'] if 'net_farmer_benefit_amount' in row and not pd.isna(
                                             row['net_farmer_benefit_amount']) else None
                                         ))
            elif row['entity_type'] == 'sub_program':
                # Find the program id, title id, subtitle id, and sub_program id from joining sub_programs, programs, and titles
                # tables
                sql_select_query = f"SELECT p.id, p.title_id, p.subtitle_id, s.id FROM {schema_name}.programs p JOIN {schema_name}.sub_programs s ON p.id = s.program_id WHERE s.name = %s"
                self.cursor.execute(sql_select_query, (row['entity_name'],))
                result = self.cursor.fetchone()
                if result:
                    program_id, title_id, subtitle_id, sub_program_id = result
                    # Insert data into the payments table
                    sql_insert_query = (
                        f"INSERT INTO {schema_name}.payments (title_id, subtitle_id, program_id, sub_program_id, state_code, year, payment, recipient_count, contract_count, base_acres, farm_count) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ")
                    # "ON CONFLICT (title_id, subtitle_id, program_id, sub_program_id, state_code, year) DO UPDATE SET payment = EXCLUDED.payment")
                    self.cursor.execute(sql_insert_query,
                                        (title_id, subtitle_id, program_id, sub_program_id, row["state_code"],
                                         row['year'],
                                         row['amount'],
                                         row['recipient_count'] if 'recipient_count' in row and not pd.isna(
                                             row['recipient_count']) else None,
                                         row['contract_count'] if 'contract_count' in row and not pd.isna(
                                             row['contract_count']) else None,
                                         row['base_acres'] if 'base_acres' in row and not pd.isna(
                                             row['base_acres']) else None,
                                         row['farm_count'] if 'farm_count' in row and not pd.isna(
                                             row['farm_count']) else None))
            elif row['entity_type'] == 'sub_sub_program':
                # Find the program id, title id, subtitle id, sub_program id, and sub_sub_program id from joining sub_sub_programs, sub_programs, programs, and titles
                # tables

                sql_select_query = f"SELECT p.id, p.title_id, p.subtitle_id, s.id, ss.id FROM {schema_name}.programs p JOIN {schema_name}.sub_programs s ON p.id = s.program_id JOIN {schema_name}.sub_sub_programs ss ON s.id = ss.sub_program_id WHERE ss.name = %s"
                self.cursor.execute(sql_select_query, (row['entity_name'],))
                result = self.cursor.fetchone()
                if result:
                    program_id, title_id, subtitle_id, sub_program_id, sub_sub_program_id = result
                    # Insert data into the payments table
                    sql_insert_query = (
                        f"INSERT INTO {schema_name}.payments (title_id, subtitle_id, program_id, sub_program_id, sub_sub_program_id, state_code, year, payment, recipient_count, contract_count, base_acres, farm_count) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ")
                    # "ON CONFLICT (title_id, subtitle_id, program_id, sub_program_id, sub_sub_program_id, state_code, year) DO UPDATE SET payment = EXCLUDED.payment")
                    self.cursor.execute(sql_insert_query,
                                        (title_id, subtitle_id, program_id, sub_program_id, sub_sub_program_id,
                                         row["state_code"], row['year'],
                                         row['amount'],
                                         row['recipient_count'] if 'recipient_count' in row and not pd.isna(
                                             row['recipient_count']) else None,
                                         row['contract_count'] if 'contract_count' in row and not pd.isna(
                                             row['contract_count']) else None,
                                         row['base_acres'] if 'base_acres' in row and not pd.isna(
                                             row['base_acres']) else None,
                                         row['farm_count'] if 'farm_count' in row and not pd.isna(
                                             row['farm_count']) else None))
        self.connection.commit()

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            self.logger.info("PostgreSQL connection is closed")
