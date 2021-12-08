import psycopg2
import pandas as pd
import requests
import json

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

    #avoid memory leaks
    cur.close()
    con.close()

    #convert home addresses to string representations
    fullStringHomeAddresses = []

    for homeAddress in homeAddresses:
        fullStringHomeAddresses.append(homeAddress[0] + "," + homeAddress[1] + "," + 
                                       homeAddress[2] + "," + homeAddress[3] + "," +
                                       homeAddress[4])

    testAddress = 'stonks'
    key = open("geokey.key").read()

    params = {
        "key" : key,
        "location" : testAddress
    }

    response = requests.get('http://www.mapquestapi.com/geocoding/v1/address', params = params)

    data = json.loads(response.text)

    lat = data['results'][0]['locations'][0]['latLng']['lat']
    lng = data['results'][0]['locations'][0]['latLng']['lng']
    mapUrl = data['results'][0]['locations'][0]['mapUrl']

    #insert into officeAddresses/homeAddresses with PK as netid

if __name__ == "__main__":
    main()