import psycopg2

def main():
    print('Beginning visualizations...')

    con = psycopg2.connect(
            host = "cypherlenovo", 
            database = "msu_students" ,
            user = 'postgres',
            password = '1234',
            port = '5433'
        )

    cur = con.cursor()

    #get home addresses
    command = '''SELECT homestreet, homecity, homestate, homezip, homecountry 
                from students
                where homestreet != 'NULL';'''
    
    cur.execute(command)
    homeAddresses = cur.fetchall()
    print("Found",len(homeAddresses),"home addresses that are not null")

    #get officeaddresses
    command = '''SELECT officestreet, officecity, officestate, officezip, officecountry 
                from students
                where officestreet != 'NULL';'''
    
    cur.execute(command)
    officeAddresses = cur.fetchall()
    print("Found",len(officeAddresses),"office addresses that are not null")

    #visualzations after getting lat/lons

    #avoid memory leaks
    cur.close()
    con.close()

if __name__ == "__main__":
    main()