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

# list of state abbreviations within our MSU database
# these were acquired via the following query:
# SELECT distinct homestate FROM students
states = [ 'AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
           'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME',
           'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM',
           'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX',
           'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY']

def generateStaticImage(lat, lon, width, height, save = False, saveNameParam = "NULL"):
    '''
    Generates a static map quest aerial view of the provided lat,lon coordinate
    '''

    # extract our key
    key = open("Keys/geokey.key").read()
    
    # build the request string
    baseString = ('http://www.mapquestapi.com/staticmap/v5/map?' 
    + 'key=' + str(key) + '&type=map&size=' + str(width) + ',' 
    + str(height) + '&locations=' + str(lat) + ',' + str(lon) 
    + '%7Cmarker-sm-50318A-1&scalebar=true&zoom=15&rand=286585877')

    # get the image and show
    im = Image.open(requests.get(baseString, stream=True).raw)
    im.show()

    # save the image if told to
    if save:
        saveName = 'Figures/' + str(lat) + "-" + str(lon) + ".png"  

        # if we were given a specific name to use, use it
        if saveNameParam != 'NULL':
            saveName = 'Figures/' + saveNameParam + ".png"
            
        # save and inform of success
        im.save(saveName)
        print('Image saved as:',saveName)

def generateStaticImageFromNetid(netid, save = False, width = 1000, 
height = 1000, database = 'msu_fall_2021'):
    '''
    Generates a static image of a student's address based on their netid.
    '''

    # get pandas df and get lat and lon
    df = getPandasFrameFromPGQuery(
        (f'SELECT lat,lon FROM students WHERE netid = \'{netid}\''), database = database)
    arr = df.values
    lat = arr[0][0]
    lon = arr[0][1]

    # get information for image name
    df = getPandasFrameFromPGQuery(
        (f'SELECT homestreet, homecity, homestate, homezip, homecountry FROM students WHERE netid = \'{netid}\''), 
        database = database)
    arr = df.values
    street = arr[0][0] 
    city = arr[0][1]
    state = arr[0][2]
    zip = arr[0][3]
    country = arr[0][4]

    # if no address
    if street == 'NULL':
        print('NetID address not found in local db, dammit Michael.')
        return

    # generate and save image
    saveName = str(street) + " " + str(city) + " " + str(state) + " " + str(zip) + " " + str(country)
    generateStaticImage(lat, lon, width, height, save, saveNameParam = saveName)

def createHeatMap(table = 'student_home_addresses', database = 'msu_fall_2021'):
    '''
    Creates a heat map based on all the lat, lon 
    pairs within the provided database and table.
    '''

    print('Generating heatmap based on home addresses')

    # get lat and lon from table
    df = getPandasFrameFromPGQuery(f'SELECT lat,lon FROM {table}', database = database)
    df = df[['lat','lon']]
    
    # get all rows
    df.head()

    # initialize to starkville center point
    m = folium.Map(location=[33.4504,-88.8184], zoom_start = 4)
    arr = df.values

    # add all the values for the coordinates
    m.add_child(plugins.HeatMap(arr, radius = 15))

    # save map specific to provided data
    saveName = f"Maps/{table}_{database}_Heatmap.html"
    m.save(saveName)
    print(f'Heatmap generated and saved as {saveName}')

#creates a waypoint map of all students from the specified state
def createStateLabelMap(stateID, database = 'msu_fall_2021'):
    '''
    Creates a way point map of all students in the provided state.
    '''

    # ifi the state is invalid
    if stateID not in states:
        print('Not a valid StateID, the following are valid stateIDs:')
        print(states)
        return

    print('Generating map with waypoints at addresses for state',stateID)

    # create query to get relvanet data
    query = '''SELECT student_home_addresses.lat, student_home_addresses.lon, 
                              students.netid, students.firstname, students.lastname,
                              students.homecity, students.homestate, students.homestreet,
                              students.homezip, students.homecountry, students.major, students.class
                              from student_home_addresses
                              inner join students on student_home_addresses.netid = students.netid
                              where students.homestate = ''' + f'\'{stateID}\';'

    # execute query and init folium map
    df = getPandasFrameFromPGQuery(query, database = database)
    m = folium.Map(location=[33.4504,-88.8184], zoom_start = 4)
    arr = df.values

    # create way points and popup data
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
        major = arr[i][10]
        classification = arr[i][11]

        html = f'''
        <h1>{firstname} {lastname}, {netid}<br/>{major}, {classification}</h1>
        <p>
        {street}<br/>{city}, {state}, {zip}<br/>{country}
        </p>
        '''
        
        iframe = folium.IFrame(html)
        popup = folium.Popup(iframe, min_width = 250, max_width = 250)

        # create marker and add to map
        folium.Marker(
            location=[lat, lon],
            popup = popup,
            tooltip = str(firstname + " " + lastname),
            icon = folium.Icon(color='darkred')
        ).add_to(m)

    # create and save map
    saveName = 'Maps/StudentNameMap_' + str(stateID) + '_State.html'
    m.save(saveName)
    print('Map Generated and saved as',saveName)

def createWorldLabeledMap(waypoints = 500, database = 'msu_fall_2021'):
    '''
    Generates a folium map for the number of specified waypoints from the provided database.
    Folium sucks at rendering lots of waypoints for some reason although I believe this is a problem
    with leafletjs which Folium wraps.
    '''

    print(f'Generating map with {waypoints} waypoints')

    # create query and execute
    query = '''select student_home_addresses.lat, student_home_addresses.lon, 
                              students.netid, students.firstname, students.lastname,
                              students.homecity, students.homestate, students.homestreet,
                              students.homezip, students.homecountry, students.major, students.class
                              from student_home_addresses
                              inner join students on student_home_addresses.netid = students.netid'''
    df = getPandasFrameFromPGQuery(query, database = database)

    # init map at center of starkville and get values
    m = folium.Map(location=[33.4504,-88.8184], zoom_start = 4)
    arr = df.values

    # pass 0 to do all waypoints in the db, usually a bad idea
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
        major = arr[i][10]
        classification = arr[i][11]

        # add data to html styled popup
        html = f'''
        <h1>{firstname} {lastname}, {netid}<br/>{major},{classification}</h1>
        <p>
        {street}<br/>{city}, {state}, {zip}<br/>{country}
        </p>
        '''
        
        # create waypoint marker and add to map
        iframe = folium.IFrame(html)
        popup = folium.Popup(iframe, min_width = 250, max_width = 250)

        folium.Marker(
            location=[lat, lon],
            popup = popup,
            tooltip = str(firstname + " " + lastname),
            icon = folium.Icon(color='darkred')
        ).add_to(m)

    # create show and save waypoint
    saveName = 'Maps/StudentNameMap_' + str(waypoints) + '_Waypoints.html'
    m.save(saveName)
    print('Map Generated and saved as',saveName)

def generateStudentByStateNormalizedCSV(database = 'msu_fall_2021'):
    '''
    Generates a CSV of the percentage of students who attend MSU by state.
    '''

    saveName = 'Data/StudentsByStateNormalized.csv'

    # open and write header information
    print('Generating csv data for students by home state')
    f = open(saveName,'w+')
    f.write('State,StudentCount\n')

    # figure out the total number of students
    query = '''SELECT count(*) 
                FROM students;'''

    # add to total from our current query
    df = getPandasFrameFromPGQuery(query, database = database)
    arr = df.values

    total = arr[0][0]

    # for all states in our db
    for stateAbrev in states:
        # get number of students from that state
        query = '''SELECT count(homestate) 
                   FROM students 
                   WHERE homestate = \'''' + stateAbrev + "\';"
        df = getPandasFrameFromPGQuery(query, database = database)
        arr = df.values

        # save with state abrev to our file
        f.write(stateAbrev + "," + str(float(arr[0][0]) / float(total)) + "\n")
    
    print(f'CSV generated and saved as {saveName}')

# checks all the state abreviations within the student table
def checkStateAbreviations(database = 'msu_fall_2021'):
    '''
    Checks and validates all state abreviations found in the provided database.
    '''

    query = '''SELECT distinct homestate 
               FROM students 
               WHERE homestate != 'NULL' and homestate != 'None';'''

    df = getPandasFrameFromPGQuery(query, database = database)
    arr = df.values
    
    for i in range(len(arr)):
        if arr[i][0].upper() not in states:
            # output the ones not in the valid list defined above
            print(arr[i][0], "is not a valid state abreviation")

def generateStateMap():
    '''
    Generates a map showing students by state as a USA State color map.
    '''
    stateMap = folium.Map(location=[40, -95], zoom_start=4)

    # assuming this CSV has been generated using a function contained in this file
    state_data = pd.read_csv('Data/StudentsByState.csv')

    # create map from student data using us-states.json for state boundary data
    folium.Choropleth(
        geo_data = 'json/us-states.json',
        name = "Students by home state",
        data = state_data,
        columns = ["State", "StudentCount"],
        key_on = "feature.id",
        fill_color = "OrRd",
        fill_opacity = 0.7,
        line_opacity = 0.1,
        legend_name="Number of Students by State",
    ).add_to(stateMap)

    # finalize and save map
    folium.LayerControl().add_to(stateMap)
    stateMap.save('Maps/StudentsByState.html')

def pathFromNetidToNetid(netid1, netid2, database = 'msu_fall_2021'):
    '''
    Generates a map using OpenRouteService to connect two 
    netids together via a driveable path.
    '''

    # inform user of actions
    print('Generating path from', netid1, "to", netid2, "...")

    # execute query
    df = getPandasFrameFromPGQuery('''select student_home_addresses.lat, student_home_addresses.lon, 
                              students.netid, students.firstname, students.lastname,
                              students.homecity, students.homestate, students.homestreet,
                              students.homezip, students.homecountry, students.major, students.class
                              from student_home_addresses
                              inner join students on student_home_addresses.netid = students.netid
                              where students.netid in (\'''' + netid1 + "\',\'" + netid2 + "\');", database = database)

    arr = df.values

    # get center point for the map
    lat1 = arr[0][0]
    lon1 = arr[0][1]
    lat2 = arr[1][0]
    lon2 = arr[1][1]

    # start map center inbetween student coords
    m = folium.Map(location=[float(lat1) + float(lat2), float(lon1) + float(lon2)], zoom_start = 4)

    coordinates = []

    # add student waypoints to map
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
        major = arr[i][10]
        classification = arr[i][11]

        coordinates.append([float(lon), float(lat)])

        # create styled string to use for popup
        html = f'''
        <h1>{firstname} {lastname}, {netid}<br/>{major}, {classification}</h1>
        <p>
        {street}<br/>{city}, {state}, {zip}<br/>{country}
        </p>
        '''

        # create the popup and map
        iframe = folium.IFrame(html)
        popup = folium.Popup(iframe, min_width = 250, max_width = 250)

        folium.Marker(
            location=[lat, lon],
            popup = popup,
            tooltip = str(firstname + " " + lastname),
            icon = folium.Icon(color='darkred') #maroon makes sense ig
        ).add_to(m)

    # get ORS key and figure out coordinates to navigate to
    client = ors.Client(key = open("Keys/mapkey.key").read())
    route = client.directions(coordinates = coordinates, profile = 'driving-car', format = 'geojson')

    # add data to map
    folium.GeoJson(route, name = ('Path from ' + str(netid1) + " to " + str(netid2))).add_to(m)

    # output and save map
    saveName = 'Maps/StudentPathMap_' + str(netid1) + "_To_" + str(netid2) + '.html'
    m.save(saveName)
    print('Map Generated and saved as', saveName)

def generateGoogleMapsLink(street = '400 S. Monroe St.', city = 'Tallahassee', 
        state = 'FL', zip = '32399-0001', country = 'United States'):
    '''
    Generates a google maps link for the provided address
    '''

    specificQuery = (street.replace(' ', '%20') + '%20' + city.replace(' ', '%20') + '%20' + 
        state.replace(' ', '%20') + '%20' + zip.replace(' ', '%20') + '%20' + country.replace(' ', '%20'))
    return (GOOGLE_MAPS_HEADER + specificQuery)

################################################3
'''
General constants
'''
GOOGLE_MAPS_HEADER = 'https://www.google.com/maps/search/?api=1&query='

MSU_HEART_LAT = 33.453516040681706
MSU_HEART_LON = -88.78947571055713
EARTH_RADIUS = 6373.0

def calculateAverageDistanceToState(database = 'msu_fall_2021'):
    '''
    Calculates the average distance from each student to the heart of MSU (the drill field)
    '''

    print('Calculating average distance from home to MSU...')

    # get necessary data
    df = getPandasFrameFromPGQuery('''SELECT student_home_addresses.lat, student_home_addresses.lon
                              FROM student_home_addresses;''')
    arr = df.values
    
    distanceSum = 0.0
    numVals = 0

    # loop through coordinates
    for i in range(len(arr)):
        lat = radians(arr[i][0])
        lon = radians(arr[i][1])

        # get dist away for current student
        dlat = radians(MSU_HEART_LAT) - lat
        dlon = radians(MSU_HEART_LON) - lon

        # calculate math to determine distnace student is from MSU
        a = sin(dlat / 2)**2 + cos(lat) * cos(radians(MSU_HEART_LAT)) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        # add to running total
        distanceSum = distanceSum + EARTH_RADIUS * c
        numVals = numVals + 1

    averageDistanceKM = distanceSum / float(numVals)

    # print average distance in metric and english units
    print('Average distance is', '%.3f' % averageDistanceKM,'km')
    print('Average distance is', '%.3f' % (averageDistanceKM * 0.62137),'mi')

def generateStreetViewImage(netid, save = True):
    '''
    Generates a google maps street view image of
     the address associated with the provided netid.
    '''

    query = '''SELECT homestreet, homecity, homestate, homezip, homecountry 
               FROM students 
               WHERE netid =\'''' + netid + '\';'

    # extract data
    arr = getPandasFrameFromPGQuery(query).values
    
    street = arr[0][0]
    city = arr[0][1]
    state = arr[0][2]
    zip = arr[0][3]
    country = arr[0][4]

    # generate query per google maps standard
    specificQuery = (street.replace(' ', '%20') + '%20' + city.replace(' ', '%20') + '%20' + 
        state.replace(' ', '%20') + '%20' + zip.replace(' ', '%20') + '%20' + country.replace(' ', '%20'))

    maxSize = 640;

    # get google maps api key
    key = open("Keys/googlemaps.key").read()

    # create the request string and pull image
    base = ('https://maps.googleapis.com/maps/api/streetview?location=' + specificQuery +
             '&size=' + str(maxSize) + 'x' + str(maxSize) + '&key=' + key)

    im = Image.open(requests.get(base, stream=True).raw)
    im.show()

    if save:
        # save image if requested to do so
        saveName = 'Figures/' + str(netid) + "_StreetView" + ".png"  
        im.save(saveName)
        print('Image saved as:', saveName)

def generateStudentsWhoMoved(databaseone, databasetwo):
    '''
    Generates a list of students who have
    different addresses between the two semesters.
    '''

    print(f'Comparing addresses from semesters: {databaseone} and {databasetwo}')
    print("Assumptions: students table with schema outlined in SQL/create_tables.sql exists in each database")

    # get entire databases of relavent data
    studentsFirstSem = getPandasFrameFromPGQuery(
        'select netid, homestreet, homecity, homestate, homezip, homecountry from students', 
    database = databaseone)

    studentsSecondSem = getPandasFrameFromPGQuery(
        'select netid, homestreet, homecity, homestate, homezip, homecountry home from students', 
    database = databasetwo)

    firstSemArr = studentsFirstSem.values
    secondSemArr = studentsSecondSem.values

    # used to keep track of students already in db
    studentsWhoMovedNetIDs = []

    # init log
    saveName = f'Data/StudentsWhoMoved_{databaseone}_{databasetwo}.txt'
    addressLog = open(saveName, "w+")

    # todo this complexity is O(n^2) and is not optimal at all
    # we should convert this to a self-join so that there's only one pass through
    # reduces time by 26,000^(26,000 - 1) which is simply insane
    for firstSemStudent in firstSemArr:
        firstNetID = firstSemStudent[0]
        firstStreet = firstSemStudent[1]
        firstCity = firstSemStudent[2]
        firstState = firstSemStudent[3]
        firstZip = firstSemStudent[4]
        firstCountry = firstSemStudent[5]

        for secondSemStudent in secondSemArr:
            secondNetID = secondSemStudent[0]
            secondStreet = secondSemStudent[1]
            secondCity = secondSemStudent[2]
            secondState = secondSemStudent[3]
            secondZip = secondSemStudent[4]
            secondCountry = secondSemStudent[5]

            #if net ids match and the netid is not already in the table
            if (firstNetID == secondNetID and firstNetID not in studentsWhoMovedNetIDs
                and (firstStreet != secondStreet or 
                     firstCity != secondCity or
                     firstState != secondState or
                     firstZip != secondZip or
                     firstCountry != secondCountry)):
                studentsWhoMovedNetIDs.append(firstNetID)

                builtStr = (firstNetID + ' moved from: ' + firstStreet + ' ' 
                + firstCity + ' ' + firstState + ' ' + firstZip + ' ' 
                + firstCountry + ' to: ' + secondStreet + ' ' + secondCity + ' ' 
                + secondState + ' ' + secondZip + ' ' + secondCountry)

                # write  to file
                addressLog.write(builtStr + "\n")
    
    # close and inform user
    addressLog.close()
    print(f"Calculations complete and saved as {saveName}")

def generateStudentsWhoSwitched(databaseone, databasetwo, excludeNulls = True):
    '''
    Generates a list of students who switched majors between the provided databases.
    '''

    print(f'Comparing declared primary majors from semesters: {databaseone} and {databasetwo}')

    studentsFirstSem = getPandasFrameFromPGQuery(
        'select netid, major, firstname, lastname from students', 
    database = databaseone)
    
    studentsSecondSem = getPandasFrameFromPGQuery(
        'select netid, major from students', 
    database = databasetwo)

    firstSemArr = studentsFirstSem.values
    secondSemArr = studentsSecondSem.values

    # used to determine what students are not already in the list
    studentsWhoSwitchedNetIDs = []

    saveName = f'Data/StudentsSwitched_{databaseone}_{databasetwo}.txt'
    switchLog = open(saveName,"w+")

    # TODO look into a self-join here too
    for firstSemStudent in firstSemArr:
        firstNetID = firstSemStudent[0]
        firstMajor = firstSemStudent[1]
        firstname = firstSemStudent[2]
        lastname = firstSemStudent[3]

        for secondSemStudent in secondSemArr:
            secondNetID = secondSemStudent[0]
            secondMajor = secondSemStudent[1]

            #if net ids match and the netid is not already in the table
            if (firstNetID == secondNetID and firstNetID not in studentsWhoSwitchedNetIDs
                and (firstMajor != secondMajor)):
                    if (excludeNulls and (firstMajor == 'NULL' or secondMajor == 'NULL')):
                        continue

                    studentsWhoSwitchedNetIDs.append(firstNetID)
                
                    builtStr = (firstname + ' ' + lastname 
                    + ' (' + firstNetID + ') switched from ' + firstMajor + " to " + secondMajor)

                    switchLog.write(builtStr + "\n")
        
    switchLog.close()

    # inform of save
    print(f"Calculations complete and saved as {saveName}")    

def getAddressFromNetID(netid, database):
    '''
    Returns an address string associated with the provided netid.
    '''

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

def parseSpacesForURL(string):
    '''
    Converts all whitespace of length one or greater to a %20 to be used in a URL.
    '''

    return re.sub('[\s]+','%20', string)

#outputs a list of other students from the passed netid's city,state combo
def listStudentsInCityStateByNetid(netid, database = 'msu_fall_2021'):
    '''
    Outputs a list of students from the provided netid's home city and state.
    '''

    print(f'Finding students from {netid}\'s home town')

    query = ('''select firstname, lastname, netid, major, class, homephone, homestreet 
                            from students 
                            where homestate = (select homestate from students where netid = \'''' + netid + '''\') 
                            and homecity = (select homecity from students where netid = \'''' + netid + '''\') 
                            order by class, major''')
    # generate and execute query
    
    saveName = 'Data/Students_From_' + netid + '_Town.csv'
    getPandasFrameFromPGQuery(query, database = database).to_csv(saveName)  

    # save as a csv
    print(f'File saved as {saveName}')

def listStudentsInCityState(city, state, database = 'msu_fall_2021'):
    '''
    Generates a list of students from the provided netid's home state.
    '''

    print(f'Finding students from {city}, {state}')

    # generate and execute query
    query = '''select firstname, lastname, netid, major, class, homephone, homestreet 
                            from students 
                            where homestate = \'''' + state + '''\' 
                            and homecity = \'''' + city + '''\'
                            order by class, major'''
    
    saveName = 'Data/Students_From_' + city + "_" + state + '.csv'
    getPandasFrameFromPGQuery(query, database = database).to_csv(saveName) 

    # inform completed and saved 
    print(f'File saved as {saveName}')

def getPandasFrameFromPGQuery(sqlQuery, database = 'msu_fall_2021', 
        host = 'cypherlenovo', user = 'postgres', password = '1234', port = '5433'):
    '''
    Returns a pandas data from from the provided sql query to postgres based on
    the provided credentials which are used to establish a connection.
    '''

    # establish connection
    con = psycopg2.connect(
        host = host,
        database = database,
        user = user,
        password = password,
        port = port
    )

    return pd.read_sql_query(sqlQuery,con)

def createMajorList(majorLike, database = 'msu_spring_2022'):
    '''
    Creates a list of students and the data most clients 
    request that have the provided declared major.
    '''

    # generate and execute query
    query = '''select netid, email, firstname, lastname, major, 
    class, homephone, homestreet, homecity, homestate, homezip,
     homecountry from students where major like \'%''' + majorLike + '''%\';'''

    df = getPandasFrameFromPGQuery(query, database = database)
    arr = df.values

    # create save name and file
    saveName = str(majorLike) + '_' + str(database) + '.csv'
    log = open(('Data/' + saveName),"w+")

    # write header data
    log.write('Format:\n')
    log.write('netid,email,firstname,lastname,major,class,phonenumber,street,city,state,zip,country\n')

    # loop through query, extract information, write line
    for i in range(0, len(arr)):
        netid = str(arr[i][0])
        email = str(arr[i][1])
        firstname = str(arr[i][2])
        lastname = str(arr[i][3])
        major = str(arr[i][4])
        classer = str(arr[i][5])
        homephone = str(arr[i][6])
        homestreet = str(arr[i][7])
        homecity = str(arr[i][8])
        homestate = str(arr[i][9])
        homezip = str(arr[i][10])
        homecountry = str(arr[i][11])
       
        log.write((netid + ',' + email + ',' 
            + firstname + ',' + lastname + ',' + major + ',' 
            + classer + ',' + homephone + ',' + homestreet + ',' 
            + homecity + ',' + homestate + ',' + homezip + ',' + homecountry +'\n'))

    # close and inform where the data is
    log.close()
    print('Done, saved to Data/ as: ', saveName)

if __name__ == '__main__':
    # the main place functions are called is from here
    # currently we're generating lists of people by major for clients ;)

    #createMajorList(majorLike = 'Engineering', database = 'msu_spring_2022')

    pass