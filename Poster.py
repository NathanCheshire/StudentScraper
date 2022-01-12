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

#relative path to exe
PATH = "chromedriver.exe"

#your account details, I'm storing them inside of a file that is ignored by git for security reasons :P
INJECTION_NAME = open("logindata.txt").read().split(',')[0]
INJECTION_PASSWORD = open("logindata.txt").read().split(',')[1]

#IDs to get past login page
USERNAME_ID = "username"
PASSWORD_ID = "password"
BUTTON_ID = "btn btn-block btn-submit"

#timeouts
PUSH_TIMEOUT = 30
PAGE_SLEEP_TIMEOUT = 1
QUERRY_SLEEP_TIMEOUT = 1

vowels = ['a','e','i','o','u','y']

#webscraping method directly using the backend API provided user is authenticated
def apiMain(startVowel = 'a', startPage = '0', studentMode = True):
    print("Begining post sequence...")
    exe = os.path.exists(PATH)

    if exe:
        print("Executable found")

        yummyCookies = getCookies()

        #the fact that cookies don't timeout is insane like what are you doing state?
        session = requests.Session()
        for cookie in yummyCookies:
            session.cookies.set(cookie['name'], cookie['value'])

        #loop through all last name contains a vowel
        for vowelIndex in range(len(vowels)):
            #start at starting vowel in case we're resuming the script after pausing it
            if vowelIndex < vowels.index(startVowel):
                continue

            personType = 's' if studentMode else 'f'

            #get the number of records there are with this search to construct our loops accordingly
            formData = constructFormString(vowels[vowelIndex], '0', 'nvc29', personType)
            totalResultsRet = post(session, formData)

            print('Attempting to parse for page number:',totalResultsRet)
            totalResults = int(re.sub("[^0-9]", "", totalResultsRet))

            pages = math.ceil(totalResults / 10.0)
            print(pages,'pages for last:', vowels[vowelIndex])

            if totalResults == 0:
                continue  

            for page in range(pages + 1):
                #only skip pages if we're also on the start vowel
                if vowels[vowelIndex] == startVowel and int(page) < int(startPage):
                    continue

                print("Page",page,"of",pages,"for last contains", vowels[vowelIndex])
                parsePost(post(session, constructFormString(vowels[vowelIndex], str(page), 'nvc29', personType)), personType)

                #reasonable timeout
                time.sleep(0.25)

        print("Finished all last contains vowels, exiting scraper")

    else:
        print("Executable not found, download from: https://sites.google.com/chromium.org/driver/downloads?authuser=0")

def constructFormString(lnameContains, page, netid, personType = 's'):
    return ('{"searchType":"Advanced","netid":"' + netid + 
    '","field1":"lname","oper1":"contain","value1":"' + lnameContains +
    '","field2":"fname","oper2":"contain","value2":"' + "" +
    '","field3":"title","oper3":"contain","value3":"","rsCount":"' + str(page) + '","type":"' + personType + '"}')

def getPostString():
    return 'https://my.msstate.edu/web/home-community/main?p_p_id=MSUDirectory1612_WAR_directory1612&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=getSearchXml&p_p_cacheability=cacheLevelPage&p_p_col_id=column-2&p_p_col_pos=6&p_p_col_count=7'

def post(session, payload):
    return session.post(getPostString(), data = dict(formData = payload)).text

#tags for parsing people ##################################

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

ADDRESS_STREET_TAG = 'street1'
ADDRESS_CITY_TAG = 'city'
ADDRESS_STATE_TAG = 'state'
ADDRESS_ZIP_TAG = 'zip'
ADDRESS_COUNTRY_TAG = 'country'

###########################################################

def parsePost(text, personType):
    if personType == 's':
        parsePostStudent(text)
    elif personType == 'f':
        parsePostFaculty(text)

def parsePostStudent(text):
    #create soup of text
    soup = BeautifulSoup(text, 'html.parser')
    #get all person tags to sub parse for information
    tag = soup.find_all(PERSON_TAG)

    for person in tag:
        personSoup = BeautifulSoup(str(person),'html.parser')

        first = re.compile(r'<.*?>').sub('', str(personSoup.find(FIRSTNAME_TAG)))
        last = re.compile(r'<.*?>').sub('', str(personSoup.find(LASTNAME_TAG)))
        picturePublic = re.compile(r'<.*?>').sub('', str(personSoup.find(PICTUREPUBLIC_TAG)))
        picturePrivate = re.compile(r'<.*?>').sub('', str(personSoup.find(PICTUREPRIVATE_TAG)))
        email = re.compile(r'<.*?>').sub('', str(personSoup.find(EMAIL_TAG)))

        rolesTags = personSoup.find(ROLES_TAG)
        studentTags = BeautifulSoup(str(rolesTags),'html.parser').find(STUDENT_ROLE_TAG)
        major = "NULL"
        class_ = "NULL"
        if studentTags != None:
            major = re.compile(r'<.*?>').sub('', str(studentTags.find(MAJOR_TAG)))
            class_ = re.compile(r'<.*?>').sub('', str(studentTags.find(CLASS_TAG)))

        numbers = personSoup.find_all('tel')
        homePhone = 0
        officePhone = 0
        
        for number in numbers:
            if "permanent" in str(number):
                homePhone = re.compile(r'<.*?>').sub('', str(number))
            elif "office" in str(number):
                officePhone = re.compile(r'<.*?>').sub('', str(number))
            else: #this is for faculty since their number is just listed as "Phone"
                homePhone = re.compile(r'<.*?>').sub('', str(number))

        addresses = personSoup.find_all('adr')

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
                
        stat = personSoup.find_all("person")[0]

        netid = stat['netid']
        pidm = stat['pidm']
        selected = stat['selected']
        isStudent = stat['student']
        isAffiliate = stat['affiliate']
        isRetired = stat['retired']

        insertPGStudents(netid, email, first, last, picturePublic, picturePrivate, major,class_, homePhone,officePhone,
                pidm, selected, isStudent, isAffiliate, isRetired, homeStreet, homeCity, homeState, homeZip, homeCountry,
                officeStreet, officeCity, officeState, officeZip, officeCountry)

def parsePostFaculty(text):
    soup = BeautifulSoup(text, 'html.parser')
    #get all person tags to sub parse for information
    tag = soup.find_all(PERSON_TAG)

    for person in tag:
        personSoup = BeautifulSoup(str(person),'html.parser')

        stat = personSoup.find_all("person")[0]

        netid = stat['netid']
        pidm = stat['pidm']
        selected = stat['selected']
        isStudent = stat['student']
        isAffiliate = stat['affiliate']
        isRetired = stat['retired']

        picturePublic = re.compile(r'<.*?>').sub('', str(personSoup.find(PICTUREPUBLIC_TAG)))
        picturePrivate = re.compile(r'<.*?>').sub('', str(personSoup.find(PICTUREPRIVATE_TAG)))

        first = re.compile(r'<.*?>').sub('', str(personSoup.find(FIRSTNAME_TAG))) 
        last = re.compile(r'<.*?>').sub('', str(personSoup.find(LASTNAME_TAG)))
        prefName = re.compile(r'<.*?>').sub('', str(personSoup.find('preferred')))
        namePrefix = re.compile(r'<.*?>').sub('', str(personSoup.find('prefix')))

        officePhone = re.compile(r'<.*?>').sub('', str(personSoup.find('tel')))

        #sometimes this is their netid @msstate.edu and sometimes
        # it's their dep, I guess they choose their pref email
        email = re.compile(r'<.*?>').sub('', str(personSoup.find('email')))

        roleSoup = BeautifulSoup(str(personSoup.find('roles')), 'html.parser')

        orgn = re.compile(r'<.*?>').sub('', str(roleSoup.find('orgn'))).replace('&amp;',"&")
        title = re.compile(r'<.*?>').sub('', str(roleSoup.find('title'))).replace('&amp;',"&")

        addressSoup = BeautifulSoup(str(personSoup.find('adr')), 'html.parser') 
        
        street1 = re.compile(r'<.*?>').sub('', str(addressSoup.find('street1')))
        street2 = re.compile(r'<.*?>').sub('', str(addressSoup.find('street2')))
        city = re.compile(r'<.*?>').sub('', str(addressSoup.find('city'))) 
        state = re.compile(r'<.*?>').sub('', str(addressSoup.find('state')))
        zip = re.compile(r'<.*?>').sub('', str(addressSoup.find('zip'))) 
        country = re.compile(r'<.*?>').sub('', str(addressSoup.find('country')))

        #null checks
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

        insertPGFaculty(netid,pidm,selected,isStudent,isAffiliate,isRetired, picturePublic,
                picturePrivate,first,last,prefName,namePrefix, officePhone, email, orgn, title,
                street1,street2,city,state,zip,country)

#inserts into the students table with the proper schema data
def insertPGStudents(netid, email = "NULL",first = "NULL",last = "NULL",picturePublic = "NULL",picturePrivate = "NULL",major = "NULL",class_ = "NULL",
                homePhone = 0,officePhone = 0, pidm = "NULL",selected = "NULL",isStudent = "NULL",isAffiliate = "NULL", isRetired = "NULL",
                homeStreet = "NULL",homeCity = "NULL",homeState = "NULL",homeZip = "NULL",homeCountry = "NULL",
                officeStreet = "NULL",officeCity = "NULL",officeState = "NULL",officeZip = "NULL",officeCountry = "NULL"):

    #try catch since duplicates will be skipped
    try:
        con = psycopg2.connect(
            host = "cypherlenovo", #beep boop machine name
            database = DATABASE , #db name
            user = 'postgres',
            password = '1234',
            port = '5433' #default port is 5432
        )

        for local in locals():
            local = local.replace("'","\'").replace('"','\"')

        cur = con.cursor()

        #todo re-run since we miss stuff like this: firststreet = 'Popp'S'
        for local in locals():
            if "'" in local or '"' in local:
                local = local.strip("'").strip('"');


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

        print('Executing',command)
        cur.execute(command)
        con.commit()

        #avoid memory leaks
        cur.close()
        con.close()
    except Exception as e:
        print(e)
        pass

def insertPGFaculty(netid,pidm,selected,isStudent,isAffiliate,isRetired, picturePublic,
                picturePrivate,firstname,lastname,prefName,namePrefix, officePhone, email, orgn, title,
                street1,street2,city,state,zip,country):
    #try catch since duplicates will be skipped
    try:
        con = psycopg2.connect(
            host = "cypherlenovo", #beep boop machine name
            database = DATABASE , #db name
            user = 'postgres',
            password = '1234',
            port = '5433' #default port is 5432
        )

        #escape any possible quotes
        for local in locals():
            local = local.replace("'","\'").replace('"','\"')

        cur = con.cursor()
        command = """INSERT INTO faculty (netid,pidm,selected,isstudent,isaffiliate,
                    isretired,picturepublic,pictureprivate,firstname,lastname,prefname,
                    nameprefix,officephone,email,orgn,title,street1,street2,
                    city,state,zip,country)VALUES ('{0}','{1}','{2}','{3}','{4}','{5}',
                    '{6}','{7}','{8}','{9}','{10}','{11}','{12}','{13}','{14}','{15}',
                    '{16}','{17}','{18}','{19}','{20}','{21}')""".format(netid,pidm,selected,isStudent
                    ,isAffiliate,isRetired, picturePublic,picturePrivate,firstname,lastname,prefName,
                    namePrefix, officePhone, email, orgn, title,street1,street2,city,state,zip,country)
        print('Executing',command)
        cur.execute(command)
        con.commit()

        #avoid memory leaks
        cur.close()
        con.close()
    except Exception as e:
        print(e)
        pass

def getCookies():
    print("Getting 24 hour cookies...")
    exe = os.path.exists(PATH)

    if exe:
        option = webdriver.ChromeOptions()

        #don't open chrome window
        option.add_argument('headless')
        driver = webdriver.Chrome(options = option)
        
        driver.get("https://my.msstate.edu/")

        elem = driver.find_element(By.ID,USERNAME_ID)
        elem.clear()
        elem.send_keys(INJECTION_NAME)

        elem = driver.find_element(By.ID, PASSWORD_ID)
        elem.clear()
        elem.send_keys(INJECTION_PASSWORD)

        driver.find_element(By.NAME,'submit').click()

        #Wait for Duo to load
        masterDuoID = "login"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, masterDuoID)))
        print(f"DUO {masterDuoID} loaded")

        #switch to duo iFrame, this took me like 3 hours to figure out kek
        iFrameTitle = "duo_iframe"
        driver.switch_to.frame(iFrameTitle)

        #click remember me for 24 hours
        twentyFourHours = "dampen_choice"
        WebDriverWait(driver, PUSH_TIMEOUT).until(
            EC.presence_of_element_located((By.NAME, twentyFourHours))).click()

        #wait for push button to load and click it
        pushButtontext = "Send Me a Push"
        WebDriverWait(driver, PUSH_TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{pushButtontext}')]"))).click()
        print("Push sent")

        #wait for directory to load to confirm we're authenticated
        directoryID = "portlet_MSUDirectory1612_WAR_directory1612"
        WebDriverWait(driver, 40).until(
            EC.presence_of_element_located((By.ID, directoryID)))
        print("Authentication complete")
        
        #copy over cookies from duo authentication
        yummyCookies = driver.get_cookies()

        return yummyCookies

DATABASE = 'msu_spring_2022'

if __name__ == "__main__":
    apiMain(studentMode = True)