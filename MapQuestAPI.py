import psycopg2
import pandas as pd
import requests
import json

def main(startFrom = 0):
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
    command = '''SELECT netid, homestreet, homecity, homestate, homezip, homecountry 
                from students
                where homestreet != 'NULL';'''
    
    cur.execute(command)
    homeAddresses = cur.fetchall()
    print("Found",len(homeAddresses),"home addresses that are not null")

    #avoid memory leaks
    cur.close()
    con.close()

    key = open("geokey.key").read()

    #for all home addresses, insert into home_addresses table
    for homeAddressInd in range(len(homeAddresses)):
        if homeAddressInd < startFrom:
            continue

        homeAddress = homeAddresses[homeAddressInd]
        netid = homeAddress[0]
        print('On netid:',netid,homeAddressInd,'/',len(homeAddresses))

        #continue if netid already in table since we don't want to make a geo request
        if '(\'' + netid + '\',)' in str(getNetIDs('home_addresses')):
            continue
       
        addressString = homeAddress[1] + "," + homeAddress[2] + "," + homeAddress[3] + "," + homeAddress[4] + "," + homeAddress[5]
    
        #strip nulls out
        addressString = addressString.replace('NULL','')

        response = getResponse(params = generateParams(key, addressString))
        data = json.loads(response.text)

        lat = data['results'][0]['locations'][0]['latLng']['lat']
        lng = data['results'][0]['locations'][0]['latLng']['lng']

        insertAddress(netid, "home_addresses", lat, lng)

    #insert into officeAddresses/homeAddresses with PK as netid

def getNetIDs(tablename = 'students'):
    con = psycopg2.connect(
            host = "cypherlenovo",
            database = "msu_students",
            user = 'postgres',
            password = '1234',
            port = '5433'
        )

    cur = con.cursor()
    command = "select netid from " + tablename
    cur.execute(command)

    return cur.fetchall()

def insertAddress(netid, table, lat = "NULL", lon = "NULL"):
    #try catch since duplicates will be skipped
    try:
        con = psycopg2.connect(
            host = "cypherlenovo",
            database = "msu_students",
            user = 'postgres',
            password = '1234',
            port = '5433'
        )

        cur = con.cursor()
        command = "INSERT INTO " + table + " (netid,lat,lon) VALUES ('{0}','{1}','{2}')".format(netid,lat,lon)
        print('Executing:',command)
        cur.execute(command)
        con.commit()

        #avoid memory leaks
        cur.close()
        con.close()
    except Exception as e:
        print(e)
        pass

def generateParams(key, location):
    params = {
        "key" : key,
        "location" : location
    }

    return params

def getResponse(params):
    return requests.get('http://www.mapquestapi.com/geocoding/v1/address', params = params)

if __name__ == "__main__":
    main(startFrom=15000)
