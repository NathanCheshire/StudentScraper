import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

args = sys.argv

if len(args) != 2:
    print("Invalid args")
else:
    db_name = args[1]
    con = psycopg2.connect(user='postgres', password = '1234', host='localhost')
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cur = con.cursor()

    cur.execute(f'CREATE DATABASE {db_name}')
    print(f'Created database {db_name}')

    cur.close()
    con.close()

    con = psycopg2.connect(database = db_name,user = 'postgres', 
            password = '1234', port = '5432')

    cur = con.cursor()

    print('Creating tables')
    cur.execute(open("Tables/create_students.sql", "r").read())
    print('Created table students')