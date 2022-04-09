import psycopg2
from datetime import datetime;

def main():
    try:
        con = psycopg2.connect(
            host = "localhost",
            database = get_current_db(),
            user = 'postgres',
            password = '1234',
            port = '5432'
        )
        cur = con.cursor()
        cur.execute(open("Tables/create_students.sql", "r").read())

        cur.close()
        con.close()

    except Exception as ignored:
        pass

    
    print('Created students table')

def get_current_db():
    today = str(datetime.today())
    year = int(today[:4])
    month = int(today[5:7])
    return "msu_" + ("spring" if month < 8 else "fall") + "_" + str(year)


if __name__ == '__main__':
    main()