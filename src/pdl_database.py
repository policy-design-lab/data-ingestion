import logging
import re

import pandas as pd
from utils.county_matcher import match_counties
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
        self.create_views_file = "../queries/create_views.sql"
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

    def create_views(self, schema_name):
        self._execute_sql_file(self.create_views_file, schema_name)
        self.logger.info("Views created successfully")

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

    def get_counties_reference(self, schema_name: str) -> pd.DataFrame:
        """
        Returns the canonical counties reference from the database.
        Expects columns: state_code, name, fips_code
        """
        sql = f"SELECT state_code, name, fips_code FROM {schema_name}.counties"
        return pd.read_sql(sql, self.connection)

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

    def insert_data(self, data_frame, schema_name, geo_level="state"):
        total_rows = len(data_frame)

        # Geographic level of data to insert
        geo_key = "state_code"
        geo_column = "state_code"
        table_name = "payments"

        # If county data, switch the row data key and SQL column name
        if geo_level == "county":
            geo_key = "fips_code"
            geo_column = "county_fips_code"
            table_name = "payments_by_counties"

            # Load valid FIPS codes from the database to check for any missing before inserting the data
            counties_ref = self.get_counties_reference(schema_name)
            valid_fips = set(counties_ref['fips_code'].values)
            self.logger.info(f"Loaded {len(valid_fips)} valid FIPS codes from database")

            # Find FIPS codes in data that aren't in the database
            data_fips = set(data_frame['fips_code'].unique())
            missing_fips = data_fips - valid_fips

            if missing_fips:
                self.logger.warning(f"Found {len(missing_fips)} FIPS codes not in database. Adding them...")

                # Get unique county info for missing FIPS
                missing_counties = data_frame[data_frame['fips_code'].isin(missing_fips)][
                    ['fips_code', 'state_code', 'state', 'county']].drop_duplicates()

                # Insert missing counties into the counties table
                for _, county_row in missing_counties.iterrows():
                    insert_county_sql = f"""
                                INSERT INTO {schema_name}.counties (fips_code, state_code, name, remarks)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (fips_code) DO NOTHING
                            """
                    self.cursor.execute(insert_county_sql, (
                        county_row['fips_code'],
                        county_row['state_code'],
                        county_row['county'],
                        'Non-standard FIPS code from Title I data'
                    ))

                # self.connection.commit()
                self.logger.info(f"Added {len(missing_counties)} new counties to the database")

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
                        f"INSERT INTO {schema_name}.{table_name} (title_id, subtitle_id, program_id, sub_program_id, {geo_column}, year, payment, recipient_count, contract_count, base_acres, farm_count) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ")
                    # "ON CONFLICT (title_id, subtitle_id, program_id, sub_program_id, state_code, year) DO UPDATE SET payment = EXCLUDED.payment")
                    self.cursor.execute(sql_insert_query,
                                        (title_id, subtitle_id, None, None, row[geo_key], row['year'],
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
                        f"INSERT INTO {schema_name}.{table_name} (title_id, subtitle_id, program_id, sub_program_id, practice_category_id, {geo_column}, year, "
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
                                         row[geo_key], row['year'],
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
                        f"INSERT INTO {schema_name}.{table_name} (title_id, subtitle_id, program_id, sub_program_id, {geo_column}, year, payment, recipient_count, contract_count, base_acres, farm_count) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ")
                    # "ON CONFLICT (title_id, subtitle_id, program_id, sub_program_id, state_code, year) DO UPDATE SET payment = EXCLUDED.payment")
                    self.cursor.execute(sql_insert_query,
                                        (title_id, subtitle_id, program_id, sub_program_id, row[geo_key],
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
                        f"INSERT INTO {schema_name}.{table_name} (title_id, subtitle_id, program_id, sub_program_id, sub_sub_program_id, {geo_column}, year, payment, recipient_count, contract_count, base_acres, farm_count) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ")
                    # "ON CONFLICT (title_id, subtitle_id, program_id, sub_program_id, sub_sub_program_id, state_code, year) DO UPDATE SET payment = EXCLUDED.payment")
                    self.cursor.execute(sql_insert_query,
                                        (title_id, subtitle_id, program_id, sub_program_id, sub_sub_program_id,
                                         row[geo_key], row['year'],
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

    def insert_commodity_data(self, df: pd.DataFrame, schema_name: str):
        from psycopg2.extras import execute_values

        if df is None or df.empty:
            self.logger.info("No commodity data to insert.")
            return

        commodity_columns = {
            'commodity_code': 'code',
            'Commodity Name': 'name',
            "Commodity Abbrv": 'abbreviation',
        }
        df.rename(columns=commodity_columns, inplace=True)

        assert self.cursor and self.connection

        table = f"{schema_name}.commodities"

        # Clean NaN -> None
        df = df.where(pd.notna(df), None)

        # Ensure correct columns
        df = df[["code", "name", "abbreviation"]]

        rows = list(df.itertuples(index=False, name=None))

        sql = f"""
            INSERT INTO {table} (code, name, abbreviation)
            VALUES %s
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                abbreviation = EXCLUDED.abbreviation
        """

        execute_values(self.cursor, sql, rows)

        self.connection.commit()
        self.logger.info(f"Inserted/updated {len(rows)} commodities")


    def insert_county_data(self, data: pd.DataFrame, schema_name: str):
        """
        Insert county-level crop insurance data into payments_by_counties.
        Resolves county FIPS via generalized matching and inserts using county_fips_code.
        """
        assert self.cursor and self.connection

        if data is None or data.empty:
            self.logger.info("No county-level rows to insert.")
            return

        program_entity_name = data["entity_name"].iloc[0]
        self.logger.info(f"Ingest {program_entity_name} county data")

        # Load canonical counties reference
        counties_ref = self.get_counties_reference(schema_name)

        self.logger.info(f"Counties reference loaded: {len(counties_ref)} counties")

        # Clean + match to FIPS
        self.logger.info("Matching counties to FIPS using generalized normalization...")
        matched = match_counties(
            data_df=data,
            ref_df=counties_ref,
            state_col='state',
            county_col='county',
            fuzzy_threshold=0.92
        )

        unmatched = matched[matched['fips_code'].isna()]
        unique_pairs = (
            unmatched[['state', 'county', 'state_code', 'county_clean']]
            .drop_duplicates()
            .sort_values(['state_code', 'county_clean'])
        )

        if not unique_pairs.empty:
            print(f"Unique unmatched pairs ({len(unique_pairs)}):")
            print(unique_pairs.to_string(index=False))

        # Report unmatched
        still_unmatched = matched[matched['fips_code'].isna()]
        if not still_unmatched.empty:
            uniq = still_unmatched[['state', 'county', 'state_code', 'county_clean', 'fuzzy_score']].drop_duplicates()
            self.logger.warning(f"{len(still_unmatched)} rows unmatched after cleaning; {len(uniq)} unique pairs.")
            self.logger.debug(f"Sample unmatched:\n{uniq.head(25)}")

        # Keep only matched rows
        to_insert = matched[matched['fips_code'].notna()].copy()
        if to_insert.empty:
            self.logger.warning("No rows to insert after matching (all unmatched).")
            return

        self.logger.info(f"Matched {len(to_insert)} rows for insertion")

        # Create temporary table with county_fips_code (avoid name joins)
        temp_table_name = "temp_county_ci_data"
        self.cursor.execute(f"DROP TABLE IF EXISTS {temp_table_name}")
        create_temp_sql = f"""
            CREATE TEMPORARY TABLE {temp_table_name} (
                year smallint,
                state_code varchar(2),
                commodity_code smallint,
                county_fips_code varchar(5),
                state_name varchar(100),
                county_name varchar(100),
                county_clean varchar(120),
                policies_prem bigint,
                acres_insured numeric(18, 4),
                liabilities numeric(18, 2),
                premium numeric(18, 2),
                subsidy numeric(18, 2),
                indemnity numeric(18, 2),
                loss_ratio numeric,
                net_benefit numeric(18, 2),
                farmer_premium numeric(18, 2),
                entity_type varchar(50),
                entity_name varchar(100),
                match_type varchar(16),
                fuzzy_score numeric
            )
            """
        self.cursor.execute(create_temp_sql)

        insert_cols = [
            'year', 'state_code', 'commodity_code', 'fips_code', 'state', 'county', 'county_clean',
            'policies_prem', 'acres_insured', 'liabilities', 'premium', 'subsidy',
            'indemnity', 'loss_ratio', 'net_benefit', 'farmer_premium',
            'entity_type', 'entity_name', 'match_type', 'fuzzy_score'
        ]
        insert_sql = f"""
                INSERT INTO {temp_table_name}
                (year, state_code, commodity_code, county_fips_code, state_name, county_name, county_clean,
                 policies_prem, acres_insured, liabilities, premium, subsidy, indemnity,
                 loss_ratio, net_benefit, farmer_premium, entity_type, entity_name, match_type, fuzzy_score)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """

        # Convert NaN -> None
        to_insert = to_insert.replace({pd.NA: None}).where(pd.notna(to_insert), None)

        # rename dataframe to temporary database table schema
        dataframe_columns_to_temporary_table_columns = {
            'premium_policy_count': 'policies_prem',
            'base_acres': 'acres_insured',
            "liability_amount": 'liabilities',
            'premium_amount': 'premium',
            'premium_subsidy_amount': 'subsidy',
            'indemnity_amount': 'indemnity',
            'net_farmer_benefit_amount': 'net_benefit',
            'farmer_premium_amount': 'farmer_premium',
        }
        to_insert.rename(columns=dataframe_columns_to_temporary_table_columns, inplace=True)

        # TODO delete test code.
        for col in insert_cols:
            if col not in to_insert.columns:
                to_insert[col] = None
        test_rows = to_insert[insert_cols].head(5)

        for _, row in test_rows.iterrows():
        # for _, row in to_insert[insert_cols].iterrows():
            self.cursor.execute(insert_sql, (
                row['year'],
                row['state_code'],
                row['commodity_code'],
                row['fips_code'],
                row['state'],
                row['county'],
                row['county_clean'],
                row['policies_prem'],
                row['acres_insured'],
                row['liabilities'],
                row['premium'],
                row['subsidy'],
                row['indemnity'],
                row['loss_ratio'],
                row['net_benefit'],
                row['farmer_premium'],
                row.get('entity_type'),
                row.get('entity_name') or 'Crop Insurance',
                row.get('match_type'),
                row.get('fuzzy_score'),
            ))

        self.connection.commit()
        self.logger.info(f"Inserted {len(to_insert)} matched rows into temp table.")

        # Verify temp table has data
        self.cursor.execute(f"SELECT COUNT(*) FROM {temp_table_name}")
        temp_count = self.cursor.fetchone()[0]
        self.logger.info(f"Temp table has {temp_count} rows")

        if 'Crop Insurance' in program_entity_name:
        # Check if Title XI exists
            self.cursor.execute(f"SELECT id, name FROM {schema_name}.titles WHERE name LIKE '%Crop Insurance%'")
            program_name = 'Crop Insurance'
            title_name = 'Title IX: Crop Insurance'
        elif 'EQIP' in program_entity_name:
            self.cursor.execute(f"SELECT id, name FROM {schema_name}.titles WHERE name LIKE '%Conservation%'")
            program_name = 'Environmental Quality Incentives Program (EQIP)'
            title_name = 'Title II: Conservation'

        #TODO: handle other program county data
        title_result = self.cursor.fetchall()
        self.logger.info(f"Found titles: {title_result}")

        sql = f"""
            SELECT p.id, p.name, t.name as title_name 
            FROM {schema_name}.programs p
            JOIN {schema_name}.titles t ON p.title_id = t.id
            WHERE p.name = %s
        """

        print(sql)


        # Check if program exists
        self.cursor.execute(f"""
            SELECT p.id, p.name, t.name as title_name 
            FROM {schema_name}.programs p
            JOIN {schema_name}.titles t ON p.title_id = t.id
            WHERE p.name = %s
        """, (program_name,))
        program_result = self.cursor.fetchall()
        self.logger.info(f"Found programs: {program_result}")

        # Final insert using fips code - FIX: explicitly set subtitle_id and sub_program_id to NULL
        insert_final_sql = f"""
            INSERT INTO {schema_name}.payments_by_counties 
            (title_id, subtitle_id, program_id, sub_program_id, commodity_code, county_fips_code, year, 
             payment, premium_policy_count, base_acres, liability_amount, premium_amount, 
             premium_subsidy_amount, indemnity_amount, farmer_premium_amount, loss_ratio, 
             net_farmer_benefit_amount)
            SELECT 
                t.id as title_id,
                NULL as subtitle_id,
                p.id as program_id,
                NULL as sub_program_id,
                temp.commodity_code,
                temp.county_fips_code,
                temp.year,
                temp.net_benefit as payment,
                temp.policies_prem as premium_policy_count,
                temp.acres_insured as base_acres,
                temp.liabilities as liability_amount,
                temp.premium as premium_amount,
                temp.subsidy as premium_subsidy_amount,
                temp.indemnity as indemnity_amount,
                temp.farmer_premium as farmer_premium_amount,
                temp.loss_ratio,
                temp.net_benefit as net_farmer_benefit_amount
            FROM {temp_table_name} temp
            JOIN {schema_name}.titles t 
                 ON t.name = %s
            JOIN {schema_name}.programs p 
                 ON p.title_id = t.id 
                AND p.name = %s
            ON CONFLICT (title_id, subtitle_id, program_id, sub_program_id, year, county_fips_code, commodity_code) 
            DO UPDATE SET
                payment = EXCLUDED.payment,
                premium_policy_count = EXCLUDED.premium_policy_count,
                base_acres = EXCLUDED.base_acres,
                liability_amount = EXCLUDED.liability_amount,
                premium_amount = EXCLUDED.premium_amount,
                premium_subsidy_amount = EXCLUDED.premium_subsidy_amount,
                indemnity_amount = EXCLUDED.indemnity_amount,
                farmer_premium_amount = EXCLUDED.farmer_premium_amount,
                loss_ratio = EXCLUDED.loss_ratio,
                net_farmer_benefit_amount = EXCLUDED.net_farmer_benefit_amount
        """

        try:
            self.cursor.execute(
                insert_final_sql,
                (title_name, program_name)
            )
            rows_inserted = self.cursor.rowcount
            self.connection.commit()
            self.logger.info(f"Inserted/updated {rows_inserted} rows in payments_by_counties.")

            # Verify the insert worked
            self.cursor.execute(f"SELECT COUNT(*) FROM {schema_name}.payments_by_counties")
            final_count = self.cursor.fetchone()[0]
            self.logger.info(f"payments_by_counties now has {final_count} total rows")

        except Exception as e:
            self.logger.error(f"Error inserting into payments_by_counties: {e}")
            self.connection.rollback()
            raise

        # Drop temp table
        self.cursor.execute(f"DROP TABLE IF EXISTS {temp_table_name}")
        self.logger.info(f"{program_entity_name} county data inserted successfully.")

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            self.logger.info("PostgreSQL connection is closed")
