import psycopg2
import requests
import json
import re

def calculateCoordinates(startFrom = 0, database = 'msu_fall_2021', 
                        fromTable = 'students', insertTable = 'home_addresses'):
    '''
    For all the students within the provided database, computes the lat,lon
    coordinates of the student's address and inserts into a home_addresses
    or office_addresses table.

    Note: the fromTable must have the same schema outlined in SQL/create_tables.sql.
    Additionally, insertTable must have the same schema outlined as well.
    '''

    # inform user begining
    print('Beginning insertions')

    # connection object for pg
    con = psycopg2.connect(
            host = "cypherlenovo", 
            database = database,
            user = 'postgres',
            password = '1234',
            port = '5433'
    )

    # cursor object for queries
    cur = con.cursor()

    # find all the valid addresses in the provided table that 
    # have not been calculated for the insertTable
    command = '''SELECT netid, homestreet, homecity, homestate, homezip, homecountry 
                 FROM ''' + fromTable + ''' 
                 WHERE homestreet != 'NULL' 
                 AND netid not in (select netid from ''' + insertTable + ''');'''
    
    cur.execute(command)
    addresses = cur.fetchall()

    # inform how many addresses were found
    print("Found", len(addresses), f"addresses that are not null from {fromTable} and are not in {insertTable}")

    # avoid memory leaks
    cur.close()
    con.close()

    # get our MapQuestAPI key
    key = open("Keys/geokey.key").read()

    # for all the found addresses
    for addressInd in range(len(addresses)):
        # skip ones already completed
        if addressInd < startFrom:
            continue

        # get current address
        address = addresses[addressInd]
        netid = address[0]
        print('On netid:', netid,addressInd + 1,'/', len(addresses))

        # continue if netid already in table since we don't want to make another
        # geo request since we only get 15K free for a valid email
        if '(\'' + netid + '\',)' in str(getNetIDs(insertTable, database = database)):
            continue

        # build address string
        addressString = ''

        if address[1] != 'NULL':
            addressString = addressString + address[1] + ','
        if address[2] != 'NULL':
            addressString = addressString + address[2] + ','
        if address[3] != 'NULL':
            addressString = addressString + address[3] + ','
        if address[4] != 'NULL':
            addressString = addressString + address[4] + ','
        if address[5] != 'NULL':
            addressString = addressString + address[5]
    
        # fix possible comma issues
        addressString = re.sub(',{2,}',',',addressString)

        # get the map quest API repsonse
        response = getResponse(key, addressString)

        # load the data using json
        data = json.loads(response.text)

        # parse the lat lon from the massive json response
        lat = data['results'][0]['locations'][0]['latLng']['lat']
        lon = data['results'][0]['locations'][0]['latLng']['lng']

        # insert the data into pg
        insertAddress(netid, insertTable, lat, lon)


def getNetIDs(tablename = 'students', database = 'msu_fall_2021'):
    '''
    Returns a list of netids in the provided table.
    '''
    # create connection for pg db
    con = psycopg2.connect(
            host = "cypherlenovo",
            database = database,
            user = 'postgres',
            password = '1234',
            port = '5433'
        )

    # return netids in this table
    cur = con.cursor()
    command = "select netid from " + tablename
    cur.execute(command)

    return cur.fetchall()

def insertAddress(netid, table, lat = "NULL", lon = "NULL", database = 'msu_fall_2021'):
    '''
    Inserts the student with the given lat,lon values into the pg db.
    '''

    #try catch since duplicates will be skipped
    try:

        # create db connection
        con = psycopg2.connect(
            host = "cypherlenovo",
            database = database,
            user = 'postgres',
            password = '1234',
            port = '5433'
        )

        # create cursor to execute command
        cur = con.cursor()
        command = "INSERT INTO " + table + " (netid,lat,lon) VALUES ('{0}','{1}','{2}')".format(netid,lat,lon)
        print('Executing:',command)

        # execute and commit upon success
        cur.execute(command)
        con.commit()

        # avoid memory leaks
        cur.close()
        con.close()
    except Exception as e:
        print(e)
        pass

MAPQUEST_HEADER = 'http://www.mapquestapi.com/geocoding/v1/address'

def getResponse(key, location):
    '''
    Posts and returns the returned data from the map quest api based on the header and provided parameters
    '''
    return requests.get(MAPQUEST_HEADER, params = {
        "key" : key,
        "location" : location
    })

if __name__ == "__main__":
    '''
    Spin off the map quest API script to find lat,lon pairs for valid addresses
    '''
    calculateCoordinates(startFrom = 0, database = 'msu_spring_2022', insertTable = 'home_addresses')
