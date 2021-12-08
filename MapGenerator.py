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
    m.save("StudentHeat.html")

    print('Heatmap generated and saved as StudentHeat.html')
    
if __name__ == '__main__':
    #generateStaticImage(33.449945,-88.781702,1000,1000)
    createUsaHeatmap()
    #todo label each person by their first and last name and netid below that
