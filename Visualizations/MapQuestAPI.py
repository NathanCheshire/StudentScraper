

import psycopg2
import requests
import json
import re

def calculate_coordinates(startFrom = 0, database = 'msu_fall_2021', 
                        table = 'students'):
    """
    For all the students within the provided database, computes the lat,lon
    coordinates of the student's address and inserts into the students table.
    :param startFrom: allows n number of entries to be skipped
    :param database: the pg database to select from the students table
    :param table: the database table, this should always be students
    """

    print('Beginning computations')

    # connection object for pg
    con = psycopg2.connect(
            host = "cypherlenovo", 
            database = database,
            user = 'postgres',
            password = '1234', # todo abstract out?
            port = '5433' # TODO configurable with docker?
    )

    # cursor object for queries
    cur = con.cursor()

    # find all the valid addresses in the provided table that 
    # don't have a lat, lon pair
    command = "SELECT netid, homestreet, homecity, homestate, homezip, homecountry " + \
              f"FROM {table} " + \
              "WHERE homestreet != 'NULL " + \
              "AND lat IS NULL AND lon IS NULL;"
    
    cur.execute(command)
    addresses = cur.fetchall()

    # inform how many addresses were found
    print("Found", len(addresses), \
        f"addresses that are not null from {table} and are do" \
            + " not have a computed (lat, lon) pair")

    # avoid memory leaks
    cur.close()
    con.close()

    # get the MapQuest API key
    try:
        key = open("Keys/geokey.key").read()
    except Exception as e:
        print('Exception occured when trying to access the MapQuest API key:', e)
        print('Exiting routine')

        return

    # for all the found addresses
    for addressInd in range(len(addresses)):
        # skip ones we were told to skip
        if addressInd < startFrom:
            continue

        # get current address
        address = addresses[addressInd]

        # inform which netid we are computing
        netid = address[0]
        print('On netid:', netid, '(' + str(addressInd + 1) + '/' + str(len(addresses)) + ')')

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
        response = get_request(key, addressString)

        # load the data using json
        data = json.loads(response.text)

        # parse the lat lon from the massive json response
        lat = data['results'][0]['locations'][0]['latLng']['lat']
        lon = data['results'][0]['locations'][0]['latLng']['lng']

        # insert the data into pg
        insert_lat_lon(netid, table, lat, lon)

def insert_lat_lon(netid, table, lat, lon, database = 'msu_fall_2021'):
    """
    Inserts the lat, lon values into the pg db students table for the provided netid.
    """

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
        command = f"UPDATE {table} " + \
                  f"SETS lat = {lat}, lon = {lon} " + \
                  f"WHERE netid = '{netid}'"
        print('Executing:', command)

        # execute and commit upon success
        cur.execute(command)
        con.commit()

        # avoid memory leaks
        cur.close()
        con.close()
    except Exception as e:
        print(f'Exception occured when attempting to update netid: {netid}\nException: ', e)
        pass

# the map quest api header to accompany a GET
MAPQUEST_HEADER = 'http://www.mapquestapi.com/geocoding/v1/address'

def get_request(key, location):
    """
    Posts and returns the returned json data from the map quest 
    api based on the header and provided parameters.
    """
    return requests.get(MAPQUEST_HEADER, params = {
        "key" : key,
        "location" : location
    })

if __name__ == "__main__":
    """
    Spin off the map quest API script to find convert valid addresses 
    to lat, lon pairs.
    """
    calculate_coordinates(startFrom = 0, database = 'msu_spring_2022', table = 'home_addresses')
