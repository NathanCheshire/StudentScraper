from math import sin,cos,sqrt,atan2,radians
import openrouteservice as ors
from PIL import Image
import requests
import pandas as pd
import psycopg2
import folium
from folium import plugins

# PR - Puerto Rico
# AE -> Armed Forces Europe
# AP -> Armed Forces Pacific
# DC -> District of Columbia

#credit: https://gist.github.com/JeffPaine/3083347 
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
def generateStaticImageFromNetid(netid, save = False, width = 1000, height = 1000):
    con = psycopg2.connect(
        host = "cypherlenovo",
        database = "msu_students",
        user = 'postgres',
        password = '1234',
        port = '5433'
    )

    df = pd.read_sql_query(f'select lat,lon from home_addresses where netid = \'{netid}\'', con)
    arr = df.values
    lat = arr[0][0]
    lon = arr[0][1]

    con = psycopg2.connect(
        host = "cypherlenovo",
        database = "msu_students",
        user = 'postgres',
        password = '1234',
        port = '5433'
    )

    df = pd.read_sql_query(f'select homestreet, homecity, homestate, homezip, homecountry from students where netid = \'{netid}\'', con)
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

#the main one: generates a heap map from all lat/lon pairs in our home_addresses table for students
def createUsaHeatmap():
    print('Generating heatmap based on home addresses')

    con = psycopg2.connect(
        host = "cypherlenovo",
        database = "msu_students",
        user = 'postgres',
        password = '1234',
        port = '5433'
    )

    df = pd.read_sql_query('select lat,lon from home_addresses', con)
    df = df[['lat','lon']]
    
    df.head()

    m = folium.Map(location=[33.4504,-88.8184], zoom_start = 4)
    arr = df.values
    m.add_child(plugins.HeatMap(arr, radius = 15))
    m.save("Maps/StudentHeat.html")

    print('Heatmap generated and saved as StudentHeat.html')

#TODO
def createStateLabelMap(stateID):
    if stateID not in states:
        print('Not a valid StateID, the following are valid stateIDs:')
        print(states)
        return

    print('Generating map with waypoints at addresses with firstname, lastname, and netid for state',stateID)

    con = psycopg2.connect(
        host = "cypherlenovo",
        database = "msu_students",
        user = 'postgres',
        password = '1234',
        port = '5433'
    )

    df = pd.read_sql_query('''select home_addresses.lat, home_addresses.lon, 
                              students.netid, students.firstname, students.lastname,
                              students.homecity, students.homestate, students.homestreet,
                              students.homezip, students.homecountry
                              from home_addresses
                              inner join students on home_addresses.netid = students.netid
                              where students.homestate = ''' + f'\'{stateID}\';', con)

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

    saveName = 'Maps/StudentNameMap_' + str(stateID) + '.html'
    m.save(saveName)
    print('Map Generated and saved as',saveName)

#generates a folium map with waypoints representing each student
def createWorldLabeledMap(waypoints = 500):
    print('Generating map with waypoints at addresses with firstname, lastname, and netid')

    con = psycopg2.connect(
        host = "cypherlenovo",
        database = "msu_students",
        user = 'postgres',
        password = '1234',
        port = '5433'
    )

    df = pd.read_sql_query('''select home_addresses.lat, home_addresses.lon, 
                              students.netid, students.firstname, students.lastname,
                              students.homecity, students.homestate, students.homestreet,
                              students.homezip, students.homecountry
                              from home_addresses
                              inner join students on home_addresses.netid = students.netid''', con)

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
def generateStudentByStateCSV():
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

            con = psycopg2.connect(
                host = "cypherlenovo",
                database = "msu_students",
                user = 'postgres',
                password = '1234',
                port = '5433'
            )

            df = pd.read_sql_query(query, con)
            arr = df.values
            total = total + arr[0][0]

    for stateAbrev in states:
        if stateAbrev != "DC":
            query = '''select count(homestate) 
                       from students 
                       where homestate = \'''' + stateAbrev + "\';"

            con = psycopg2.connect(
                host = "cypherlenovo",
                database = "msu_students",
                user = 'postgres',
                password = '1234',
                port = '5433'
            )

            df = pd.read_sql_query(query, con)
            arr = df.values
            f.write(stateAbrev + "," + str(float(arr[0][0]) / float(total)) + "\n")
    
    print('CSV generated')

# checks al the state abreviations within the student table
def checkStateAbreviations():
    query = '''select distinct homestate 
               from students 
               where homestate != 'NULL' and homestate != 'None';'''

    con = psycopg2.connect(
        host = "cypherlenovo",
        database = "msu_students",
        user = 'postgres',
        password = '1234',
        port = '5433'
    )

    df = pd.read_sql_query(query, con)
    arr = df.values
    
    for i in range(len(arr)):
        if arr[i][0].upper() not in states:
            print(arr[i][0],"is not a valid state abreviation")

def validateStateAbr(abrev):
    return abrev in states and abrev != 'DC'

#generates a map representing the students of MSU by statae
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
def pathFromNetidToNetid(netid1, netid2):
    print('Generating path from',netid1,"to",netid2,"...")

    con = psycopg2.connect(
        host = "cypherlenovo",
        database = "msu_students",
        user = 'postgres',
        password = '1234',
        port = '5433'
    )

    df = pd.read_sql_query('''select home_addresses.lat, home_addresses.lon, 
                              students.netid, students.firstname, students.lastname,
                              students.homecity, students.homestate, students.homestreet,
                              students.homezip, students.homecountry
                              from home_addresses
                              inner join students on home_addresses.netid = students.netid
                              where students.netid in (\'''' + netid1 + "\',\'" + netid2 + "\');", con)

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

def generateGoogleMapsLink(street = '400 S. Monroe St.', city = 'Tallahassee', 
        state = 'FL', zip = '32399-0001', country = 'United States'):
    specificQuery = (street.replace(' ', '%20') + '%20' + city.replace(' ', '%20') + '%20' + 
        state.replace(' ', '%20') + '%20' + zip.replace(' ', '%20') + '%20' + country.replace(' ', '%20'))

    rawQuery = 'https://www.google.com/maps/search/?api=1&query='

    return (rawQuery + specificQuery)

MSU_HEART_LAT = 33.453516040681706
MSU_HEART_LON = -88.78947571055713
EARTH_RADIUS = 6373.0

def calculateAverageDistanceToState():
    print('Calculating average distance from home to MSU...')

    con = psycopg2.connect(
        host = "cypherlenovo",
        database = "msu_students",
        user = 'postgres',
        password = '1234',
        port = '5433'
    )

    df = pd.read_sql_query('''select home_addresses.lat, home_addresses.lon
                              from home_addresses;''', con)
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

def generateStreetViewImage(street, city, state, zip, country, width = 1000, height = 1000, save = False):
    print('Acquiring street view image for provided address; save:',str(save))
    #https://developers.google.com/maps/documentation/streetview/overview
    #You'll need a google api key for this, gross

def main(args1, args2 = "", args3 = ""):
    if args1 == 'heatmap':
        createUsaHeatmap()
    elif args1 == 'static image from netid':
        generateStaticImageFromNetid(args2, save = args3)
    elif args1 == 'world labeled map':
        #todo this method can't handle all the addresses, find a better way to show waypoints
        createWorldLabeledMap(waypoints = args2)
    elif args1 == 'state map':
        #removing MS did not help that much, think of a better method, maybe a wider color range
        generateStateMap()
    elif args1 == 'path from netid to netid':
        #TODO waypoints should have a link to googlemaps to how to get there from current location
        pathFromNetidToNetid(args2, args3)
    elif args1 == 'avg dist':
        calculateAverageDistanceToState()
    elif args1 == 'state labeled map':
        createStateLabelMap(args2)

def generateStudentsWhoSwitched(semester1,semester2):
    print('Comparing declared primary majors from each semester')
    pass

if __name__ == '__main__':
    main('state labeled map','LA')