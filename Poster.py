import os
import requests
import re
import math
import psycopg2
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.chrome.service import Service

# relative path to exe
PATH = "Drivers/chrome_98_driver.exe"

INJECTION_NAME = open("Keys/state.key").read().split(',')[0]
INJECTION_PASSWORD = open("Keys/state.key").read().split(',')[1]

# the list to loop through of what the lastname should contain
lastnameContains = ['a','e','i','o','u','y']

def apiMain(startVowel = 'a', startPage = '0', studentMode = True):
    '''
    Post requestor which sends a post request for each lastname contains 
    in our contains list above and parses the results into the locally setup pg db.

    This utilizes and exploits CAS, DUO, Banner, and just generally poor
    security on MSU's end. Why the hell am I able to send 24,000 post requests in the matter
    of 5 hours?

    Note: see SQL/create_tables.sql for the table schemas and create statements.
    '''

    print("Begining post sequence...")

    # ensure the browser driver for selenium exists
    exe = os.path.exists(PATH)

    if exe:
        print("Executable found")

        # get the cookies for the post request
        yummyCookies = getCookies()

        # the fact that cookies don't timeout is insane
        # transfer cookies over to our session object
        session = requests.Session()
        for cookie in yummyCookies:
            session.cookies.set(cookie['name'], cookie['value'])

        # for all lastname contains
        for containsIndex in range(len(lastnameContains)):
            # skip ones we have already done
            # (this script supports stopping and resuming at where you left off
            # by passing an appropriate startVowel and startPage)
            if containsIndex < lastnameContains.index(startVowel):
                continue

            # depending on the provided person, figure out what post request person type to send
            personType = 's' if studentMode else 'f'

            # find out how many results were returned for this post 
            # request so we know how many pages there are to loop through
            formData = constructFormString(lastnameContains[containsIndex], '0', 'nvc29', personType)
            totalResultsRet = post(session, formData)

            # inform of page we are parsing
            print('Attempting to parse for page number:',totalResultsRet)

            # regex to parse the returned results to an int
            totalResults = int(re.sub("[^0-9]", "", totalResultsRet))

            # find out how many pages were returned
            pages = math.ceil(totalResults / 10.0)
            print(pages,'pages for last:', lastnameContains[containsIndex])

            # if no results then simply continue
            # this is after the above print statement so that the 
            # user knows there were 0 records here
            if totalResults == 0:
                continue  

            # for all the pages found by this returned request
            for page in range(pages + 1):
                # skip past the pages we've already done for this vowel
                if lastnameContains[containsIndex] == startVowel and int(page) < int(startPage):
                    continue

                # inform of page we are on
                print("Page", page, "of", pages, "for last contains", lastnameContains[containsIndex])

                # parse the post associated with the current page we should be on
                parsePost(post(session, constructFormString(lastnameContains[containsIndex], 
                            str(page), 'nvc29', personType)), personType)

                # wait a little so that we're not spamming the MSU backend
                # this isn't even necessary though. More good web security on their end, ggnore
                time.sleep(0.25)

        print("Finished all last contains vowels, exiting scraper")

    else:
        print("Executable not found, download from: https://sites.google.com/chromium.org/driver/downloads?authuser=0")

def constructFormString(lnameContains, page, netid, personType = 's'):
    """
    Returns a string for our form data POST request based on
    what the last name should contain, the page number, our (you the script user) netid,
    and the expected person type, e.g. 's' for student or 'f' for faculty.

    Note: page numbers are deduced separately since we must know how many pages there are
    in order to access them all.
    """

    return ('{"searchType":"Advanced","netid":"' + netid + 
    '","field1":"lname","oper1":"contain","value1":"' + lnameContains +
    '","field2":"fname","oper2":"contain","value2":"' + "" +
    '","field3":"title","oper3":"contain","value3":"","rsCount":"' + str(page) + '","type":"' + personType + '"}')

# the POST header
POST_STRING = '''https://my.msstate.edu/web/home-community/main?
                p_p_id=MSUDirectory1612_WAR_directory1612&p_p_lifecycle=
                2&p_p_state=normal&p_p_mode=view&p_p_resource_id=getSearchXml&p_p_
                cacheability=cacheLevelPage&p_p_col_id=column-2&p_p_col_pos=6&p_p_col_count=7'''

def post(session, payload):
    '''
    Sends a post request to the MSU student directory backend 
    with the provided session (cookies too) and payload.
    '''

    return session.post(POST_STRING, data = dict(formData = payload)).text

###########################################################
'''
Tags for parsing people from a returned POST request
'''

PERSON_TAG = 'person'
LASTNAME_TAG = 'lastname'
FIRSTNAME_TAG = 'firstname'
PICTUREPUBLIC_TAG = 'picturepublic'
PICTUREPRIVATE_TAG = 'pictureprivate'
EMAIL_TAG = 'email'

ROLES_TAG = 'roles'
STUDENT_ROLE_TAG = 'student'
MAJOR_TAG = 'major'
CLASS_TAG = 'class'

PHONE_TAG = 'tel'
ADDRESS_TAG = 'adr'

ADDRESS_STREET_TAG = 'street1'
ADDRESS_CITY_TAG = 'city'
ADDRESS_STATE_TAG = 'state'
ADDRESS_ZIP_TAG = 'zip'
ADDRESS_COUNTRY_TAG = 'country'

###########################################################

def parsePost(postResponse, personType):
    """
    Parses the provided returned post string based on the person type given.
    """
    if personType == 's':
        parsePostStudent(postResponse)
    elif personType == 'f':
        parsePostFaculty(postResponse)

def parsePostStudent(postResponse):
    '''
    Parses the provided post response as student data 
    and inserts the found students into the local pg database.
    '''
    
    # for all person tags found
    for person in BeautifulSoup(postResponse, 'html.parser').find_all(PERSON_TAG):

        # master person soup
        personSoup = BeautifulSoup(str(person),'html.parser')

        # get important data
        first = re.compile(r'<.*?>').sub('', str(personSoup.find(FIRSTNAME_TAG)))
        last = re.compile(r'<.*?>').sub('', str(personSoup.find(LASTNAME_TAG)))
        email = re.compile(r'<.*?>').sub('', str(personSoup.find(EMAIL_TAG)))

        # picture data for some reason
        picturePublic = re.compile(r'<.*?>').sub('', str(personSoup.find(PICTUREPUBLIC_TAG)))
        picturePrivate = re.compile(r'<.*?>').sub('', str(personSoup.find(PICTUREPRIVATE_TAG)))

        # find student roles
        rolesTags = personSoup.find(ROLES_TAG)
        studentTags = BeautifulSoup(str(rolesTags),'html.parser').find(STUDENT_ROLE_TAG)

        # find student's major and classification
        major = "NULL"
        class_ = "NULL"

        if studentTags != None:
            major = re.compile(r'<.*?>').sub('', str(studentTags.find(MAJOR_TAG)))
            class_ = re.compile(r'<.*?>').sub('', str(studentTags.find(CLASS_TAG)))

        # parse phone numbers, defaults are 0 since these are ints in our db
        numbers = personSoup.find_all(PHONE_TAG)
        homePhone = 0
        officePhone = 0
        
        # find proper numbers
        for number in numbers:
            if "permanent" in str(number):
                homePhone = re.compile(r'<.*?>').sub('', str(number))
            elif "office" in str(number):
                officePhone = re.compile(r'<.*?>').sub('', str(number))
            else: #this is for faculty since their number is just listed as "Phone"
                homePhone = re.compile(r'<.*?>').sub('', str(number))

        # find the addresses of the student
        addresses = personSoup.find_all(ADDRESS_TAG)

        # initialize home and office address data
        homeStreet = "NULL"
        homeCity = "NULL"
        homeState = "NULL"
        homeZip = "NULL"
        homeCountry = "NULL"

        officeStreet = "NULL"
        officeCity = "NULL"
        officeState = "NULL"
        officeZip = "NULL"
        officeCountry = "NULL"

        # for all the found addresses, parse the data
        for address in addresses:
            if "permanent" in str(address):
                homeStreet = re.compile(r'<.*?>').sub('', str(personSoup.find(ADDRESS_STREET_TAG)))
                homeCity = re.compile(r'<.*?>').sub('', str(personSoup.find(ADDRESS_CITY_TAG)))
                homeState = re.compile(r'<.*?>').sub('', str(personSoup.find(ADDRESS_STATE_TAG)))
                homeZip = re.compile(r'<.*?>').sub('', str(personSoup.find(ADDRESS_ZIP_TAG)))
                homeCountry = re.compile(r'<.*?>').sub('', str(personSoup.find(ADDRESS_COUNTRY_TAG)))
            elif "office" in str(address):
                officeStreet = re.compile(r'<.*?>').sub('', str(personSoup.find(ADDRESS_STREET_TAG)))
                officeCity = re.compile(r'<.*?>').sub('', str(personSoup.find(ADDRESS_CITY_TAG)))
                officeState = re.compile(r'<.*?>').sub('', str(personSoup.find(ADDRESS_STATE_TAG)))
                officeZip = re.compile(r'<.*?>').sub('', str(personSoup.find(ADDRESS_ZIP_TAG)))
                officeCountry = re.compile(r'<.*?>').sub('', str(personSoup.find(ADDRESS_COUNTRY_TAG)))
                
        # find person statistics 
        stat = personSoup.find_all("person")[0]

        # primary and candidate key
        netid = stat['netid']
        pidm = stat['pidm']

        # some random boleans
        selected = stat['selected']
        isStudent = stat['student']
        isAffiliate = stat['affiliate']
        isRetired = stat['retired']

        # finally insert into our db with our parsed studetnt data
        insertPGStudents(netid, email, first, last, picturePublic, picturePrivate, major,class_, homePhone,officePhone,
                pidm, selected, isStudent, isAffiliate, isRetired, homeStreet, homeCity, homeState, homeZip, homeCountry,
                officeStreet, officeCity, officeState, officeZip, officeCountry)

def parsePostFaculty(postResponse):
    '''
    Parses the provided post request return string as faculty 
    objects to insert into the currently set pg database.
    '''

    # for all person tags in this post request
    for person in BeautifulSoup(postResponse, 'html.parser').find_all(PERSON_TAG):
        # primary html soup to parse
        personSoup = BeautifulSoup(str(person),'html.parser')

        # primary statistics html
        stat = personSoup.find_all("person")[0]

        # parse key and candidate key
        netid = stat['netid']
        pidm = stat['pidm']

        # some random booleans
        selected = stat['selected']
        isStudent = stat['student']
        isAffiliate = stat['affiliate']
        isRetired = stat['retired']

        # picture data for some reason
        picturePublic = re.compile(r'<.*?>').sub('', str(personSoup.find(PICTUREPUBLIC_TAG)))
        picturePrivate = re.compile(r'<.*?>').sub('', str(personSoup.find(PICTUREPRIVATE_TAG)))

        # parse name data
        first = re.compile(r'<.*?>').sub('', str(personSoup.find(FIRSTNAME_TAG))) 
        last = re.compile(r'<.*?>').sub('', str(personSoup.find(LASTNAME_TAG)))
        prefName = re.compile(r'<.*?>').sub('', str(personSoup.find('preferred')))
        namePrefix = re.compile(r'<.*?>').sub('', str(personSoup.find('prefix')))

        # parse phone
        officePhone = re.compile(r'<.*?>').sub('', str(personSoup.find(PHONE_TAG)))

        # parse email; interestingly, sometimes this is netid@msstate.edu
        # and sometimes it's their name @depemail.edu
        email = re.compile(r'<.*?>').sub('', str(personSoup.find('email')))

        # parse role html
        roleSoup = BeautifulSoup(str(personSoup.find('roles')), 'html.parser')

        # parse role data
        orgn = re.compile(r'<.*?>').sub('', str(roleSoup.find('orgn'))).replace('&amp;',"&")
        title = re.compile(r'<.*?>').sub('', str(roleSoup.find('title'))).replace('&amp;',"&")

        # parse address html
        addressSoup = BeautifulSoup(str(personSoup.find(ADDRESS_TAG)), 'html.parser') 
        
        # parse address
        street1 = re.compile(r'<.*?>').sub('', str(addressSoup.find('street1')))
        street2 = re.compile(r'<.*?>').sub('', str(addressSoup.find('street2')))
        city = re.compile(r'<.*?>').sub('', str(addressSoup.find('city'))) 
        state = re.compile(r'<.*?>').sub('', str(addressSoup.find('state')))
        zip = re.compile(r'<.*?>').sub('', str(addressSoup.find('zip'))) 
        country = re.compile(r'<.*?>').sub('', str(addressSoup.find('country')))

        # check for invalid data and insert NULL
        if first == None:
            first = "NULL"
        if last == None:
            last = "NULL"
        if prefName == None:
            prefName = "NULL"
        if namePrefix == None:
            namePrefix = "NULL"
        if officePhone == None:
            officePhone = "NULL"
        if email == None:
            email = "NULL"
        if orgn == None:
            orgn = "NULL"
        if title == None:
            title = "NULL"
        if street1 == None:
            street1 = "NULL"
        if street2 == None:
            street2 = "NULL"
        if city == None:
            city = "NULL"
        if state == None:
            state = "NULL"
        if zip == None:
            zip = "NULL"
        if country == None:
            country = "NULL"

        # finally, after parsing and corrections, insert into the table
        insertPGFaculty(netid,pidm,selected,isStudent,isAffiliate,isRetired, picturePublic,
                picturePrivate,first,last,prefName,namePrefix, officePhone, email, orgn, title,
                street1,street2,city,state,zip,country)

# the database to use, change this to the
# name of your database when using a new one
# also ensure your table exists with the schema outlined in SQL/create_tables.sql
DATABASE = 'msu_spring_2022'

def insertPGStudents(netid, email = "NULL",first = "NULL",last = "NULL",picturePublic = "NULL",picturePrivate = "NULL",major = "NULL",class_ = "NULL",
                homePhone = 0,officePhone = 0, pidm = "NULL",selected = "NULL",isStudent = "NULL",isAffiliate = "NULL", isRetired = "NULL",
                homeStreet = "NULL",homeCity = "NULL",homeState = "NULL",homeZip = "NULL",homeCountry = "NULL",
                officeStreet = "NULL",officeCity = "NULL",officeState = "NULL",officeZip = "NULL",officeCountry = "NULL"):

    '''
    Inserts a new row into the students table in the 
    currently set database with the provided information.
    '''

    # for all our local variables in scope, escape quotes
    # don't declare any variables in scope before this
    for local in locals():
        local = local.replace("'","\'").replace('"','\"')

    # duplicates throw an exception since we cannot insert with the same primary key
    try:
        # create the connection to our local db
        con = psycopg2.connect(
            host = "cypherlenovo", # your beep boop machine name
            database = DATABASE , # your database name as set above. Ex: "msu_fall_2021"
            user = 'postgres', # typical
            password = '1234', # your password for your db
            port = '5433' # default port is 5432 but whatever you set it to
        )

        # create our cursor
        cur = con.cursor()
        
        # note: replacing all ' and " here with nothing used to be performed
        # but due to the locals() loop above, is no longer needed

        # build the insert command we are going to execute
        command = """INSERT INTO students (netid,email,firstname,lastname,
        picturepublic,pictureprivate,major,class,homephone,officephone,pidm,
        selected,isstudent,isaffiliate,isretired,homestreet,homecity,homestate,
        homezip,homecountry,officestreet,officecity,officestate,officezip,
        officecountry) VALUES ('{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}',
        '{8}','{9}','{10}','{11}','{12}','{13}','{14}','{15}','{16}','{17}',
        '{18}','{19}','{20}','{21}','{22}','{23}','{24}')""".format(netid,email,
        first,last,picturePublic,picturePrivate,major,class_,homePhone,officePhone,
        pidm,selected,isStudent,isAffiliate,isRetired,homeStreet,homeCity,homeState,
        homeZip,homeCountry,officeStreet,officeCity,officeState,officeZip,officeCountry)

        # inform user of the command to execute
        print('Executing', command)

        # execute and commit if successful
        cur.execute(command)
        con.commit()

        # avoid memory leaks
        cur.close()
        con.close()
    except Exception as e:
        # typically this simply means that the user was already in the table
        print(e)
        pass

def insertPGFaculty(netid,pidm,selected,isStudent,isAffiliate,isRetired, picturePublic,
                picturePrivate,firstname,lastname,prefName,namePrefix, officePhone, email, orgn, title,
                street1,street2,city,state,zip,country):
    '''
    Create a new row in the faculty table and
    inserts a faculty object with the provided data.
    '''

     # escape any possible quotes
    for local in locals():
        local = local.replace("'","\'").replace('"','\"')

    try:
        # create a connection for our local db
        con = psycopg2.connect(
            host = "localhost", # your beep boop machine name
            database = DATABASE , # local db name as defined above
            user = 'postgres', # default
            password = '1234', # your pg admin password
            port = '5433' # your pg port
        )

        # create a cursor to execute our statement
        cur = con.cursor()

        # create the insert command
        command = """INSERT INTO faculty (netid,pidm,selected,isstudent,isaffiliate,
        isretired,picturepublic,pictureprivate,firstname,lastname,prefname,
        nameprefix,officephone,email,orgn,title,street1,street2,
        city,state,zip,country)VALUES ('{0}','{1}','{2}','{3}','{4}','{5}',
        '{6}','{7}','{8}','{9}','{10}','{11}','{12}','{13}','{14}','{15}',
        '{16}','{17}','{18}','{19}','{20}','{21}')""".format(netid,pidm,selected,isStudent
        ,isAffiliate,isRetired, picturePublic,picturePrivate,firstname,lastname,prefName,
        namePrefix, officePhone, email, orgn, title,street1,street2,city,state,zip,country)

        # inform the user of the insert command
        print('Executing', command)
        
        # execute and commit if successful
        cur.execute(command)
        con.commit()

        # avoid memory leaks
        cur.close()
        con.close()
    except Exception as e:
        # usually this means the faculty was already in the table
        print(e)
        pass

#############################################################
'''
Cookie acquiring
'''

# element names for getting cookies from DUO
USERNAME_ID = "username"
PASSWORD_ID = "password"
BUTTON_ID = "btn btn-block btn-submit"

DRIVER_ARGS = ['headless']

STATE_URL = 'https://my.msstate.edu/'

# timeouts used
PUSH_TIMEOUT = 30

def getCookies():
    """
    Acquires cookies which last at least 24 hours
    (CAS cookies for MSU banner don't expire sometimes, suck it CAS)
    """

    print("Getting 24 hour cookies...")

    # make sure the selenium driver exists
    exe = os.path.exists(PATH)

    if exe:
        # get the chrome driver (as a user you may 
        # need to change this per our browser and selenium usage)
        option = webdriver.ChromeOptions()

        for arg in DRIVER_ARGS:
            option.add_argument(arg)

        driver = webdriver.Chrome(options = option, 
        service = Service(PATH))
        
        # go to url
        driver.get(STATE_URL)

        # navigate to username field and inject username
        elem = driver.find_element(By.ID, USERNAME_ID)
        elem.clear()
        elem.send_keys(INJECTION_NAME)

        # navigate to password field and inject password
        elem = driver.find_element(By.ID, PASSWORD_ID)
        elem.clear()
        elem.send_keys(INJECTION_PASSWORD)

        # find and click submit button
        driver.find_element(By.NAME, 'submit').click()

        # wait for Duo to load
        masterDuoID = "login"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, masterDuoID)))
        print(f"DUO {masterDuoID} loaded")

        # switch to duo iFrame (this took me like 3 hours to figure out kek)
        iFrameTitle = "duo_iframe"
        driver.switch_to.frame(iFrameTitle)

        # click "remember me for 24 hours"
        twentyFourHours = "dampen_choice"
        WebDriverWait(driver, PUSH_TIMEOUT).until(
            EC.presence_of_element_located((By.NAME, twentyFourHours))).click()

        # wait for push button to load and click it
        pushButtontext = "Send Me a Push"
        WebDriverWait(driver, PUSH_TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{pushButtontext}')]"))).click()
        print("Push sent")

        # wait for user to accept duo push and for the subsequent 
        # directory to load to confirm we were properly authenticated
        directoryID = "portlet_MSUDirectory1612_WAR_directory1612"
        WebDriverWait(driver, 40).until(
            EC.presence_of_element_located((By.ID, directoryID)))
        print("Authentication complete")
        
        # copy over the delicious cookies from duo authentication, oh so yummy
        yummyCookies = driver.get_cookies()

        return yummyCookies

# start off poster and select person type
if __name__ == "__main__":
    apiMain(studentMode = True)