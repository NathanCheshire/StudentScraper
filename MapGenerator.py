from math import sin,cos,sqrt,atan2,radians
import openrouteservice as ors
from PIL import Image
import requests
import pandas as pd
import psycopg2
import folium
from folium import plugins
import re

# PR - Puerto Rico
# AE -> Armed Forces Europe
# AP -> Armed Forces Pacific
# DC -> District of Columbia
states = [ 'AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
           'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME',
           'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM',
           'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX',
           'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY']

#generates a static image based off of a lat/lon input
def generateStaticImage(lat, lon, width, height, save = False, saveNameParam = "NULL"):
    key = open("Keys/geokey.key").read()
    
    baseString = ('http://www.mapquestapi.com/staticmap/v5/map?' 
    + 'key=' + str(key) + '&type=map&size=' + str(width) + ',' 
    + str(height) + '&locations=' + str(lat) + ',' + str(lon) 
    + '%7Cmarker-sm-50318A-1&scalebar=true&zoom=15&rand=286585877')

    im = Image.open(requests.get(baseString, stream=True).raw)
    im.show()

    if save:
        saveName = 'Figures/' + str(lat) + "-" + str(lon) + ".png"  

        if saveNameParam != 'NULL':
            saveName = 'Figures/' + saveNameParam + ".png"
            
        im.save(saveName)
        print('Image saved as:',saveName)

#the party trick: generates a static 'google maps' like view of a student's house given their netid
def generateStaticImageFromNetid(netid, save = False, width = 1000, height = 1000, database = 'msu_fall_2021'):
    df = getPandasFrameFromPGQuery(f'select lat,lon from student_home_addresses where netid = \'{netid}\'', database = database)
    arr = df.values
    lat = arr[0][0]
    lon = arr[0][1]

    df = getPandasFrameFromPGQuery(f'select homestreet, homecity, homestate, homezip, homecountry from students where netid = \'{netid}\'', database = database)
    arr = df.values
    street = arr[0][0] 
    city = arr[0][1]
    state = arr[0][2]
    zip = arr[0][3]
    country = arr[0][4]

    if street == 'NULL':
        print('NetID address not found in local db, dammit Michael.')
        return

    saveName = str(street) + " " + str(city) + " " + str(state) + " " + str(zip) + " " + str(country)
    generateStaticImage(lat, lon, width, height, save, saveNameParam = saveName)

#the main one: generates a heap map from all lat/lon pairs in our student_home_addresses table for students
def createUsaHeatmap(database = 'msu_fall_2021'):
    print('Generating heatmap based on home addresses')

    df = getPandasFrameFromPGQuery('select lat,lon from student_home_addresses', database = database)
    df = df[['lat','lon']]
    
    df.head()

    m = folium.Map(location=[33.4504,-88.8184], zoom_start = 4)
    arr = df.values
    m.add_child(plugins.HeatMap(arr, radius = 15))
    m.save("Maps/StudentHeat.html")

    print('Heatmap generated and saved as StudentHeat.html')

#creates a waypoint map of all students from the specified state
def createStateLabelMap(stateID, database = 'msu_fall_2021'):
    if stateID not in states:
        print('Not a valid StateID, the following are valid stateIDs:')
        print(states)
        return

    print('Generating map with waypoints at addresses with firstname, lastname, and netid for state',stateID)

    query = '''select student_home_addresses.lat, student_home_addresses.lon, 
                              students.netid, students.firstname, students.lastname,
                              students.homecity, students.homestate, students.homestreet,
                              students.homezip, students.homecountry
                              from student_home_addresses
                              inner join students on student_home_addresses.netid = students.netid
                              where students.homestate = ''' + f'\'{stateID}\';'

    df = getPandasFrameFromPGQuery(query, database = database)

    m = folium.Map(location=[33.4504,-88.8184], zoom_start = 4)
    arr = df.values

    for i in range(0, len(arr)):
        lat = arr[i][0]
        lon = arr[i][1]
        netid = arr[i][2]
        firstname = arr[i][3]
        lastname = arr[i][4]
        city = arr[i][5]
        state = arr[i][6]
        street = arr[i][7]
        zip = arr[i][8]
        country = arr[i][9]

        html = f'''
        <h1>{firstname} {lastname}, {netid}</h1>
        <p>
        {street}<br/>{city}, {state}, {zip}<br/>{country}
        </p>
        '''
        
        iframe = folium.IFrame(html)
        popup = folium.Popup(iframe, min_width = 250, max_width = 250)

        folium.Marker(
            location=[lat, lon],
            popup = popup,
            tooltip = str(firstname + " " + lastname),
            icon = folium.Icon(color='darkred')
        ).add_to(m)

    saveName = 'Maps/StudentNameMap_' + str(stateID) + '_State.html'
    m.save(saveName)
    print('Map Generated and saved as',saveName)

#generates a folium map with waypoints representing each student, you can limit the number of waypoints since 
# folium sucks at rendering tons of waypoints for some reason even though it uses leaflet.js
def createWorldLabeledMap(waypoints = 500, database = 'msu_fall_2021'):
    print('Generating map with waypoints at addresses with firstname, lastname, and netid')

    query = '''select student_home_addresses.lat, student_home_addresses.lon, 
                              students.netid, students.firstname, students.lastname,
                              students.homecity, students.homestate, students.homestreet,
                              students.homezip, students.homecountry
                              from student_home_addresses
                              inner join students on student_home_addresses.netid = students.netid'''

    df = getPandasFrameFromPGQuery(query, database = database)

    m = folium.Map(location=[33.4504,-88.8184], zoom_start = 4)
    arr = df.values

    if waypoints == 0:
        waypoints = len(arr)

    for i in range(0, waypoints):
        lat = arr[i][0]
        lon = arr[i][1]
        netid = arr[i][2]
        firstname = arr[i][3]
        lastname = arr[i][4]
        city = arr[i][5]
        state = arr[i][6]
        street = arr[i][7]
        zip = arr[i][8]
        country = arr[i][9]

        html = f'''
        <h1>{firstname} {lastname}, {netid}</h1>
        <p>
        {street}<br/>{city}, {state}, {zip}<br/>{country}
        </p>
        '''
        
        iframe = folium.IFrame(html)
        popup = folium.Popup(iframe, min_width = 250, max_width = 250)

        folium.Marker(
            location=[lat, lon],
            popup = popup,
            tooltip = str(firstname + " " + lastname),
            icon = folium.Icon(color='darkred')
        ).add_to(m)

    saveName = 'Maps/StudentNameMap_' + str(waypoints) + '_Waypoints.html'
    m.save(saveName)
    print('Map Generated and saved as',saveName)

#generates a csv representing the number of students from MSU by state
def generateStudentByStateCSV(database = 'msu_fall_2021'):
    print('Generating csv data for students by home state')

    f = open('Data/StudentsByStateNormalized.csv','w+')
    f.write('State,StudentCount\n')

    #get total number to normalilze our data
    total = 0
    
    for stateAbrev in states:
        if stateAbrev != "DC":
            query = '''select count(homestate) 
                       from students 
                       where homestate = \'''' + stateAbrev + "\';"

            df = getPandasFrameFromPGQuery(query, database = database)
            arr = df.values
            total = total + arr[0][0]

    for stateAbrev in states:
        if stateAbrev != "DC":
            query = '''select count(homestate) 
                       from students 
                       where homestate = \'''' + stateAbrev + "\';"

            df = getPandasFrameFromPGQuery(query, database = database)
            arr = df.values
            f.write(stateAbrev + "," + str(float(arr[0][0]) / float(total)) + "\n")
    
    print('CSV generated')

# checks all the state abreviations within the student table
def checkStateAbreviations(database = 'msu_fall_2021'):
    query = '''select distinct homestate 
               from students 
               where homestate != 'NULL' and homestate != 'None';'''

    df = getPandasFrameFromPGQuery(query, database = database)
    arr = df.values
    
    for i in range(len(arr)):
        if arr[i][0].upper() not in states:
            print(arr[i][0],"is not a valid state abreviation")

def validateStateAbr(abrev):
    return abrev in states and abrev != 'DC'

#generates a map representing the students of MSU by state
def generateStateMap():
    stateMap = folium.Map(location=[40, -95], zoom_start=4)

    url = (
        "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data"
    )
    state_geo = f"{url}/us-states.json"

    state_data = pd.read_csv('Data/StudentsByStateNoMS.csv')

    folium.Choropleth(
        geo_data = state_geo,
        name = "Students by home state",
        data = state_data,
        columns = ["State", "StudentCount"],
        key_on = "feature.id",
        fill_color = "OrRd",
        fill_opacity = 0.7,
        line_opacity = 0.1,
        legend_name="% Of Students by State",
    ).add_to(stateMap)

    folium.LayerControl().add_to(stateMap)
    stateMap.save('Maps/StudentsByStateNoMS.html')

#generates a map using folium and openrouteservice to connect two netid addresses via
# a driveable route
def pathFromNetidToNetid(netid1, netid2, database = 'msu_fall_2021'):
    print('Generating path from',netid1,"to",netid2,"...")

    df = getPandasFrameFromPGQuery('''select student_home_addresses.lat, student_home_addresses.lon, 
                              students.netid, students.firstname, students.lastname,
                              students.homecity, students.homestate, students.homestreet,
                              students.homezip, students.homecountry
                              from student_home_addresses
                              inner join students on student_home_addresses.netid = students.netid
                              where students.netid in (\'''' + netid1 + "\',\'" + netid2 + "\');", database = database)

    m = folium.Map(location=[33.4504,-88.8184], zoom_start = 4)
    arr = df.values

    coordinates = []

    #add red waypoints to map
    for i in range(0, len(arr)):
        lat = arr[i][0]
        lon = arr[i][1]
        netid = arr[i][2]
        firstname = arr[i][3]
        lastname = arr[i][4]
        city = arr[i][5]
        state = arr[i][6]
        street = arr[i][7]
        zip = arr[i][8]
        country = arr[i][9]

        coordinates.append([float(lon), float(lat)])

        html = f'''
        <h1>{firstname} {lastname}, {netid}</h1>
        <p>
        {street}<br/>{city}, {state}, {zip}<br/>{country}
        </p>
        '''
        
        iframe = folium.IFrame(html)
        popup = folium.Popup(iframe, min_width = 250, max_width = 250)

        folium.Marker(
            location=[lat, lon],
            popup = popup,
            tooltip = str(firstname + " " + lastname),
            icon = folium.Icon(color='darkred') #maroon makes sense ig
        ).add_to(m)

    client = ors.Client(key = open("Keys/mapkey.key").read())
    route = client.directions(coordinates = coordinates, profile = 'driving-car', format = 'geojson')
    folium.GeoJson(route, name = ('Path from ' + str(netid1) + " to " + str(netid2))).add_to(m)

    saveName = 'Maps/StudentPathMap_' + str(netid1) + "_To_" + str(netid2) + '.html'
    m.save(saveName)
    print('Map Generated and saved as',saveName)

#generates a google maps link for the provided street,city,state,zip,country combo
def generateGoogleMapsLink(street = '400 S. Monroe St.', city = 'Tallahassee', 
        state = 'FL', zip = '32399-0001', country = 'United States'):
    specificQuery = (street.replace(' ', '%20') + '%20' + city.replace(' ', '%20') + '%20' + 
        state.replace(' ', '%20') + '%20' + zip.replace(' ', '%20') + '%20' + country.replace(' ', '%20'))

    rawQuery = 'https://www.google.com/maps/search/?api=1&query='

    return (rawQuery + specificQuery)

MSU_HEART_LAT = 33.453516040681706
MSU_HEART_LON = -88.78947571055713
EARTH_RADIUS = 6373.0

#calculates the average distance from each student to the heart of MSU (the drill field center)
def calculateAverageDistanceToState(database = 'msu_fall_2021'):
    print('Calculating average distance from home to MSU...')

    df = getPandasFrameFromPGQuery('''select student_home_addresses.lat, student_home_addresses.lon
                              from student_home_addresses;''')
    arr = df.values
    
    distanceSum = 0.0
    numVals = 0

    for i in range(len(arr)):
        lat = radians(arr[i][0])
        lon = radians(arr[i][1])

        dlat = radians(MSU_HEART_LAT) - lat
        dlon = radians(MSU_HEART_LON) - lon

        a = sin(dlat / 2)**2 + cos(lat) * cos(radians(MSU_HEART_LAT)) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distanceSum = distanceSum + EARTH_RADIUS * c
        numVals = numVals + 1

    averageDistanceKM = distanceSum / float(numVals)
    print('Average distance is', '%.3f' % averageDistanceKM,'kilometers')
    print('Average distance is', '%.3f' % (averageDistanceKM * 0.62137),'miles')

#generates and saves a street view image of the address associated with the provided netid
def generateStreetViewImage(netid, save = True):
    query = '''select homestreet, homecity, homestate, homezip, homecountry 
               from students 
               where netid =\'''' + netid + '\';'

    arr = getPandasFrameFromPGQuery(query).values
    
    street = arr[0][0]
    city = arr[0][1]
    state = arr[0][2]
    zip = arr[0][3]
    country = arr[0][4]

    specificQuery = (street.replace(' ', '%20') + '%20' + city.replace(' ', '%20') + '%20' + 
        state.replace(' ', '%20') + '%20' + zip.replace(' ', '%20') + '%20' + country.replace(' ', '%20'))

    maxSize = 640;

    key = open("Keys/googlemaps.key").read()

    base = ('https://maps.googleapis.com/maps/api/streetview?location=' + specificQuery +
             '&size=' + str(maxSize) + 'x' + str(maxSize) + '&key=' + key)

    im = Image.open(requests.get(base, stream=True).raw)
    im.show()

    if save:
        saveName = 'Figures/' + str(netid) + "_StreetView" + ".png"  
        im.save(saveName)
        print('Image saved as:', saveName)

#names passed in need to be the db name of the semester
def generateStudentsWhoSwitched(semester1, semester2):
    print(f'Comparing declared primary majors from semesters: {semester1} and {semester2}')

#returns the address for the netid for the current database
def getAddressFromNetID(netid, database):
    query = ('''select homestreet, homecity, homestate, homezip, homecountry 
               from ''' + database + ''' where netid =\'''' + netid + '\';')

    df = getPandasFrameFromPGQuery(query, database = database)
    arr = df.values
    
    street = arr[0][0]
    city = arr[0][1]
    state = arr[0][2]
    zip = arr[0][3]
    country = arr[0][4]

    return (street + ' ' + city + ' ' + state + ' ' + zip + ' ' + country);

#converts all whitspace of length 1 or greater to %20 to be used in a url
def parseSpacesForURL(string):
    return re.sub('[\s]+','%20', string)

#outputs a list of other students from the passed netid's city,state combo
def listStudentsInCityStateByNetid(netid, database = 'msu_fall_2021'):
    print(f'Finding students from {netid}\'s home town')

    query = ('''select firstname, lastname, netid, major, class, homephone, homestreet 
                            from students 
                            where homestate = (select homestate from students where netid = \'''' + netid + '''\') 
                            and homecity = (select homecity from students where netid = \'''' + netid + '''\') 
                            order by class, major''')
    
    saveName = 'Data/Students_From_' + netid + '_Town.csv'
    getPandasFrameFromPGQuery(query, database = database).to_csv(saveName)  
    print(f'File saved as {saveName}')

#outputs a list of other students from the passed netid's city,state combo
def listStudentsInCityState(city, state, database = 'msu_fall_2021'):
    print(f'Finding students from {city}, {state}')

    query = '''select firstname, lastname, netid, major, class, homephone, homestreet 
                            from students 
                            where homestate = \'''' + state + '''\' 
                            and homecity = \'''' + city + '''\'
                            order by class, major'''
    
    saveName = 'Data/Students_From_' + city + "_" + state + '.csv'
    getPandasFrameFromPGQuery(query, database = database).to_csv(saveName)  
    print(f'File saved as {saveName}')

#returns a pandas data frame resulting from executing the provided 
# sql query on the built connection using the provided credentials
def getPandasFrameFromPGQuery(sqlQuery, database = 'msu_fall_2021', 
        host = 'cypherlenovo', user = 'postgres', password = '1234', port = '5433'):

    con = psycopg2.connect(
        host = host,
        database = database,
        user = user,
        password = password,
        port = port
    )

    return pd.read_sql_query(sqlQuery,con)

def main():
    generateStreetViewImage('nvc29')

if __name__ == '__main__':
    main()