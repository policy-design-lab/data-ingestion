import argparse
import logging


class PolicyDesignLabDataCLI:
    def __init__(self):
        self.parser = None
        self.args = None
        self._setup_parser()
        self._setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)

    def print_args(self):
        print("\nArguments\tValues")
        print("======================")
        for key, value in self.args.__dict__.items():
            print(key, ":", value)
        print("======================\n")

    def _setup_parser(self):
        self.parser = argparse.ArgumentParser(
            description='Create a PostgreSQL database and tables, and insert/update data into the tables.',
            add_help=True)
        self.parser.add_argument('--db_name', '-d', type=str, required=True, help='Name of the database to create',
                                 default='')
        self.parser.add_argument('--db_user', '-u', type=str, required=False,
                                 help='Username to connect to the database',
                                 default='')
        self.parser.add_argument('--db_password', '-p', type=str, required=False,
                                 help='Password to connect to the database. We STRONGLY RECOMMEND using .pgpass file. '
                                      'If you use .pgpass file, this command-line argument can be ignored.',
                                 default='')
        self.parser.add_argument('--db_host', type=str, help='Host of the database', default='localhost')
        self.parser.add_argument('--db_port', type=int, help='Port of the database', default=5432)
        self.parser.add_argument('--drop_existing', '-x', action='store_true',
                                 help='Drop existing database if exists', default=False)
        self.parser.add_argument('--log_level', '-l', type=str, help='Log level', default='INFO')
        self.parser.add_argument('--create-tables', '-c', action='store_true', help='Create tables', default=False)
        self.parser.add_argument('--create-database', '-C', action='store_true', help='Create database', default=False)
        self.parser.add_argument('--init-tables', '-i', action='store_true', help='Initialize tables', default=False)
        self.parser.add_argument('--insert-data', '-I', action='store_true', help='Insert data',
                                 default=False)
        self.args = self.parser.parse_args()
        return

    @staticmethod
    def _setup_logging():
        logging.basicConfig(format='%(asctime)s %(levelname)-7s : %(name)s - %(message)s', level=logging.INFO)
        return
