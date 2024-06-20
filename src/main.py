import logging
from data_parser import DataParser
from pdl_cli import PolicyDesignLabDataCLI
from pdl_database import PDLDatabase

# Write a command line program to create a PostgreSQL database and tables, and insert/update data into the tables.


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    cli = PolicyDesignLabDataCLI()
    cli.print_args()
    database = PDLDatabase(cli.args.db_name, cli.args.db_user, cli.args.db_password, cli.args.db_host,
                           cli.args.db_port)
    if not cli.args.create_database_schema:
        database.connect()
    if cli.args.drop_existing:
        response = input(" Are you sure you want to drop the existing database? (y/n): ")
        if response.lower() == 'y':
            database.drop_database()
        else:
            print("Continuing without dropping the database")
    if cli.args.create_database_schema:
        database.create_database_and_schema()
    if cli.args.create_tables:
        database.create_tables()
    if cli.args.init_tables:
        database.initialize_tables()

    title_i_data_parser = DataParser(2014, 2021, "Title 1: Commodities",
                                     "../data/title-i", "title_1_version_1.csv",
                                     base_acres_csv_filename_arc_co="ARC-CO Base Acres by Program.csv",
                                     base_acres_csv_filename_plc="PLC Base Acres by Program.csv",
                                     farm_payee_count_csv_filename_arc_co="ARC-CO Recipients by Program.csv",
                                     farm_payee_count_csv_filename_arc_ic="ARC-IC Recipients by Program.csv",
                                     farm_payee_count_csv_filename_plc="PLC Recipients by Program.csv",
                                     total_payment_csv_filename_arc_co="ARC-CO.csv",
                                     total_payment_csv_filename_arc_ic="ARC-IC.csv",
                                     total_payment_csv_filename_plc="PLC.csv",
                                     dmc_sada_csv_filename="Dairy-Disaster.csv"
                                     )
    title_i_data_parser.format_data()

    title_ii_data_parser = DataParser(2018, 2022, "Title 2: Conservation",
                                      "../data/title-ii", "",
                                      crp_csv_filename="CRP_total_compiled_August_24_2023.csv",
                                      acep_csv_filename="ACEP.csv",
                                      rcpp_csv_filename="RCPP.csv",
                                      eqip_csv_filename="EQIP Farm Bill.csv",
                                      csp_csv_filename="CSP Farm Bill.csv")
    title_ii_data_parser.format_data()

    # TODO: Add feature to update data or insert data for specific programs.
    if cli.args.insert_data:
        # Title I data ingestion
        logger.info("Starting Title I data ingestion...")
        database.insert_data(title_i_data_parser.program_data)
        database.insert_data(title_i_data_parser.dmc_data)
        database.insert_data(title_i_data_parser.sada_data)
        logger.info("Title I data ingestion complete.")

        # Title II data ingestion
        logger.info("Starting Title II data ingestion...")
        database.insert_data(title_ii_data_parser.program_data)
        logger.info("Title II data ingestion complete.")
    database.close()
