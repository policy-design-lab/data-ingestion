# Command-Line-Interface to Manage Policy Design Lab Database (PostgreSQL)

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Usage

```bash
usage: main.py [-h] --db_name DB_NAME [--db_user DB_USER] [--db_password DB_PASSWORD] [--db_host DB_HOST] [--db_port DB_PORT] [--drop_existing] [--log_level LOG_LEVEL] [--create-tables] [--create-database-schema]
               [--init-tables] [--insert-data]

Create a PostgreSQL database and tables, and insert/update data into the tables.

optional arguments:
  -h, --help            show this help message and exit
  --db_name DB_NAME, -d DB_NAME
                        Name of the database to create
  --db_user DB_USER, -u DB_USER
                        Username to connect to the database
  --db_password DB_PASSWORD, -p DB_PASSWORD
                        Password to connect to the database. We STRONGLY RECOMMEND using .pgpass file. If you use .pgpass file, this command-line argument can be ignored.
  --db_host DB_HOST     Host of the database
  --db_port DB_PORT     Port of the database
  --drop_existing, -x   Drop existing database if exists
  --log_level LOG_LEVEL, -l LOG_LEVEL
                        Log level
  --create-tables, -c   Create tables
  --create-database-schema, -C
                        Construct database and/or schema
  --init-tables, -i     Initialize tables
  --insert-data, -I     Insert data
```

## Example

```bash
python main.py -d "pdl_db" -u '' -p '' -c -C -i
```