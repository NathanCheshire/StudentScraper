from PIL import Image
import requests

def generateStaticImage(lat, lon, width, height):
    key = open("geokey.key").read()
    
    baseString = ('http://www.mapquestapi.com/staticmap/v5/map?' 
    + 'key=' + str(key) + '&type=map&size=' + str(width) + ',' 
    + str(height) + '&locations=' + str(lat) + ',' + str(lon) 
    + '%7Cmarker-sm-50318A-1&scalebar=true&zoom=15&rand=286585877')

    im = Image.open(requests.get(baseString, stream=True).raw)
    im.show()

if __name__ == '__main__':
    generateStaticImage(33.449945,-88.781702,1000,1000)
    