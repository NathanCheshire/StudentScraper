from PIL import Image
from folium.plugins import heat_map
import requests
import pandas as pd
import psycopg2
import folium
from folium import plugins

def generateStaticImage(lat, lon, width, height):
    key = open("geokey.key").read()
    
    baseString = ('http://www.mapquestapi.com/staticmap/v5/map?' 
    + 'key=' + str(key) + '&type=map&size=' + str(width) + ',' 
    + str(height) + '&locations=' + str(lat) + ',' + str(lon) 
    + '%7Cmarker-sm-50318A-1&scalebar=true&zoom=15&rand=286585877')

    im = Image.open(requests.get(baseString, stream=True).raw)
    im.show()

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
    
def createWorldLabeledMap():
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

    #TODO maybe form an address too?

    waypoints = 500

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
        ).add_to(m)

    saveName = 'Maps/StudentNameMap_' + str(waypoints) + '_Waypoints.html'
    m.save(saveName)
    print('Map Generated and saved as',saveName)
    
if __name__ == '__main__':
    #generateStaticImage(33.449945,-88.781702,1000,1000)
    #createUsaHeatmap()
    createWorldLabeledMap()
