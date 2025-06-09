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
    # Connect to the database if not creating a new database
    if not cli.args.create_database:
        database.connect(database.db_name, database.db_user, database.db_password, database.db_host, database.db_port)
    # Drop the existing database based on the user input
    if cli.args.drop_existing:
        response = input(" Are you sure you want to drop the existing database? (y/n): ")
        if response.lower() == 'y':
            database.drop_database()
        else:
            print("Continuing without dropping the database")
    schema_name = cli.args.schema_name
    if cli.args.create_database:
        database.create_database()
    if cli.args.create_schema:
        database.create_schema(schema_name)
    if cli.args.create_tables:
        database.create_tables(schema_name)
    if cli.args.init_tables:
        database.initialize_tables(schema_name)

    title_i_data_parser = DataParser(2014, 2023, "Title 1: Commodities",
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

    title_ii_data_parser = DataParser(2014, 2023, "Title 2: Conservation",
                                      "../data/title-ii", "",
                                      crp_csv_filename="CRP-total compiled (January 28 2025).csv",
                                      acep_csv_filename="ACEP.csv",
                                      rcpp_csv_filename="RCPP.csv",
                                      eqip_csv_filename="EQIP Farm Bill.csv",
                                      csp_csv_filename="CSP Farm Bill.csv")
    title_ii_data_parser.format_data()

    snap_data_parser = DataParser(2018, 2022, "Supplemental Nutrition Assistance Program (SNAP)",
                                  "../data/snap", "",
                                  snap_monthly_participation_filename="snap_monthly_participation.csv",
                                  snap_cost_filename="snap_costs.csv")
    snap_data_parser.format_data()

    crop_insurance_data_parser = DataParser(2014, 2023, "Crop Insurance",
                                            "../data/crop-insurance", "",
                                            ci_state_year_benefit_filename="ci_state_year_benefits 2014-2023.csv")
    crop_insurance_data_parser.format_data()

    if cli.args.insert_data:
        # Title I data ingestion
        logger.info("Starting Title I data ingestion...")
        database.insert_data(title_i_data_parser.program_data, schema_name)
        database.insert_data(title_i_data_parser.dmc_data, schema_name)
        database.insert_data(title_i_data_parser.sada_data, schema_name)
        logger.info("Title I data ingestion complete.")

        # Title II data ingestion
        logger.info("Starting Title II data ingestion...")
        database.insert_data(title_ii_data_parser.program_data, schema_name)
        logger.info("Title II data ingestion complete.")

        # Title IV data ingestion
        logger.info("Starting Title IV data ingestion...")
        database.insert_data(snap_data_parser.snap_data, schema_name)
        logger.info("Title IV data ingestion complete.")

        # Title XI data ingestion
        logger.info("Starting Title XI data ingestion...")
        database.insert_data(crop_insurance_data_parser.ci_data, schema_name)
        logger.info("Title XI data ingestion complete.")

    database.close()
