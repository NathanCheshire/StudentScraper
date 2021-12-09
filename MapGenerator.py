from os import stat
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

def generateStaticImage(lat, lon, width, height, save = False):
    key = open("geokey.key").read()
    
    baseString = ('http://www.mapquestapi.com/staticmap/v5/map?' 
    + 'key=' + str(key) + '&type=map&size=' + str(width) + ',' 
    + str(height) + '&locations=' + str(lat) + ',' + str(lon) 
    + '%7Cmarker-sm-50318A-1&scalebar=true&zoom=15&rand=286585877')

    im = Image.open(requests.get(baseString, stream=True).raw)
    im.show()
    im.save('Figures/' + str(lat) + "-" + str(lon) + ".png")

def generateStaticImageFromNetid(netid, save = False):
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

    generateStaticImage(lat, lon, 1000, 1000, save)

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
                              students.homecity, students.homestate
                              from home_addresses
                              inner join students on home_addresses.netid = students.netid''', con)

    m = folium.Map(location=[33.4504,-88.8184], zoom_start = 4)
    arr = df.values

    latIndex = 0
    lonIndex = 1
    netidIndex = 2
    firstnameIndex = 3
    lastnameIndex = 4
    cityIndex = 5
    stateIndex = 6

    if waypoints == 0:
        waypoints = len(arr)

    for i in range(0, waypoints):
        lat = arr[i][latIndex]
        lon = arr[i][lonIndex]
        netid = arr[i][netidIndex]
        firstname = arr[i][firstnameIndex]
        lastname = arr[i][lastnameIndex]
        city = arr[i][cityIndex]
        state = arr[i][stateIndex]

        folium.Marker(
            location=[lat, lon],
            popup = str(firstname + "\n" + lastname + "\n" + netid + "\n" + city + "\n" + state),
            icon = folium.Icon(color='darkred')
        ).add_to(m)

    saveName = 'Maps/StudentNameMap_' + str(waypoints) + '_Waypoints.html'
    m.save(saveName)
    print('Map Generated and saved as',saveName)

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
        validateStateAbreviation(arr[i][0])

def validateStateAbreviation(abrev):
    if abrev.upper() not in states:
        print(abrev,"is not a valid state abreviation")

def validateStateAbr(abrev):
    return abrev in states and abrev != 'DC'

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

if __name__ == '__main__':
    #createUsaHeatmap()

    #todo this method can't handle all the addresses, find a better way to show waypoints
    #createWorldLabeledMap(waypoints = 500)

    #generateStaticImageFromNetid('', save = True)

    #removing MS did not help that much, think of a better method, maybe a wider color range
    generateStateMap()