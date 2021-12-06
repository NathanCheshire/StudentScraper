import os
import requests
import re
import math
import psycopg2
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
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

#contains permutation slices
alphas = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 
                'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 
                'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

firstFileName = ""

#basic webscraping technique using front-end interaction
def nathanMain():
    try:
        print("Begining scraping sequence")
        exe = os.path.exists(PATH)

        if exe:
            print("Executable found")

            driver = webdriver.Chrome()
            driver.get("https://my.msstate.edu/")

            elem = driver.find_element(By.ID,USERNAME_ID)
            elem.clear()
            elem.send_keys(INJECTION_NAME)

            elem = driver.find_element(By.ID, PASSWORD_ID)
            elem.clear()
            elem.send_keys(INJECTION_PASSWORD)

            driver.find_element(By.NAME,'submit').click()

            #DUO handling
            masterElemnString = "login"
            myElem = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, masterElemnString)))
            print(f"DUO {masterElemnString} loaded")

            #switch to duo iFrame
            iFrameTitle = "duo_iframe"
            driver.switch_to.frame(iFrameTitle)

            #wait for push button to load and click it
            pushButtontext = "Send Me a Push"
            WebDriverWait(driver, PUSH_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{pushButtontext}')]"))).click()
            print("Push sent")

            #wait for directory to load
            directoryID = "portlet_MSUDirectory1612_WAR_directory1612"
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, directoryID)))
            print("Directory element loaded")

            #select student radio button
            driver.find_element(By.XPATH, "//input[@value='s']").click()

            #generate permutation lists
            firsts = generatePairsList()
            lasts = generatePairsList()

            #skip permutations we have finished
            skips = 0
            skipped = count_files('FirstsParsed')
            print('skipped:',skipped)

            for firstIndex in range(len(firsts)):
                if skips != skipped:
                    print("Skipping: first =",firsts[firstIndex])
                    skips += 1
                    continue

                #Create the file we're going to write to for this first pair
                global firstFileName
                firstFileName = "Firsts/First_Name_Contains_" + firsts[firstIndex] + ".txt"
                file = open(firstFileName,'w+')
                file.close()

                for last in lasts:
                    try:
                        #inect last name search
                        firstSearchFieldID = 'fld1_search_term'
                        elem = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, firstSearchFieldID)))
                        elem.clear()
                        elem.send_keys(last)

                        #inject first name search
                        secondSearchFieldID = 'fld2_search_term'
                        elem = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, secondSearchFieldID)))
                        elem.clear()
                        elem.send_keys(firsts[firstIndex])

                        #Submit search based on provided first and last name
                        searchText = "submit"
                        myElem = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, searchText)))
                        myElem.click()

                        #in case we're changing seraches wait for this to settle
                        time.sleep(1)

                        #Get how many pages were returned for this query
                        countElement = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, 'count')))
                        elementCount = int(re.search(r'\d+', countElement.get_attribute('innerHTML')).group())
                        print("---------------------------------")
                        print("Querry: first =",firsts[firstIndex],"last =",last)
                        print('Records returned:', elementCount)
                        numPages = int(math.ceil(elementCount / 10.0))
                        print('Number of pages:',numPages)
                        print("---------------------------------")

                        #immediately continue of query returned no results
                        if elementCount == 0:
                            continue

                        #for all pages returned from this query
                        page = 0
                        while page < numPages + 1:
                            #get information for each person on current page
                            for person in driver.find_elements(By.CLASS_NAME, "person"):
                                printPersonDetails(driver, person, 
                                    person.get_attribute('innerHTML'))

                            #if the pagenumber element exists, execute js to go to the next page
                            if elementExists(driver, 'pagenums'):
                                driver.execute_script("getDetails(0)") 
                                
                            #inc pages
                            page += 1

                            time.sleep(PAGE_SLEEP_TIMEOUT) 

                        time.sleep(QUERRY_SLEEP_TIMEOUT)
                    except:
                        continue

                print(firstFileName,' finished with all last permutations. Continuing to next first permutation')

            print('All permutations from first and last have been executed; exiting scraper')
        else:
            print("Executable not found, download from: https://sites.google.com/chromium.org/driver/downloads?authuser=0")
    except Exception as e:
        print("Exception:", e)

def count_files(in_directory):
    joiner= (in_directory + os.path.sep).__add__
    return sum(
        os.path.isfile(filename)
        for filename
        in map(joiner, os.listdir(in_directory))
    )

#gets and logs the given person's details
def printPersonDetails(driver, person, personName):
    classification = "NULL"
    major = "NULL"

    try:
        parent = person.find_element(By.XPATH, "..").find_element(By.XPATH, "..")
        pTags = parent.find_elements(By.CSS_SELECTOR, "p")
        classification = pTags[1].get_attribute('innerHTML')
        major = pTags[2].get_attribute('innerHTML')
    except:
        pass

    if len(classification) == 0:
        classification = ""
    if len(major) == 0:
        major = ""

    #Enter person details section
    person.send_keys(Keys.ENTER)

    #wait for details section to be loaded
    detailsID = 'details-section'
    detailsElement = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, detailsID)))

    parseHTML(detailsElement.get_attribute('innerHTML'), personName, classification, major)

    #go back to query results
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located ((By.ID, 'back'))).send_keys(Keys.ENTER)

#checks if an html element exists and is loaded by the current driver
def elementExists(driver, id):
    try:
        driver.find_element(By.ID, id)
    except:
        return False
    return True

#parses the html returned by the webcrawler
def parseHTML(studentDetails, name, classification, major):
    #user attributes
    studentName = name
    studentEmail = "NULL"
    studentHomePhone = 0
    studentCampusPhone = 0
    studentCampusAddress = []
    studentHomeAddress = []
   
    soup = BeautifulSoup(studentDetails, features="html.parser")
    pretty = soup.prettify()
    lines = pretty.split('\n')

    mode = "none"
    
    for line in lines:
        #parse away b tags
        if "<b>" in line or "</b>" in line or "<b/>" in line:
            continue
        #parse away break tags
        elif "<br>" in line or "<br/>" in line or "</br>" in line:
            continue
        #parse away a tags
        elif "</a>" in line or "<a" in line or "<a/>" in line:
            continue

        line = parseNonAscii(line)

        if line.strip() == "Email":
            mode = "email"
            continue
        elif line.strip() == "Phone":
            mode = "phone"
            continue
        elif line.strip() == "Campus Address":
            mode = "ca"
            continue
        elif line.strip() == "Home Address":
            mode = "ha"
            continue

        #precautionary continue for empty lines
        if len(line.strip()) < 3:
            continue

        if mode == "email" and line.strip() != "Email":
            studentEmail = line.strip()
        elif mode == "phone" and line.strip() != "Phone":
            if "Campus" in line:
                studentCampusPhone = ''.join(c for c in line if c.isdigit())
            else:
                studentHomePhone = ''.join(c for c in line if c.isdigit())
        elif mode == "ca":
            studentCampusAddress.append(line.strip())
        elif mode == "ha":
            studentHomeAddress.append(line.strip())

    #join address lines
    studentCampusAddress = " ".join(studentCampusAddress)
    studentHomeAddress = " ".join(studentHomeAddress)

    #null checks
    if studentHomePhone == 0:
        studentHomePhone = "NULL"
    if studentCampusPhone == 0:
        studentCampusPhone = "NULL"
    
    if len(studentCampusAddress.strip()) == 0:
        studentCampusAddress = "NULL"

    if len(studentHomeAddress.strip()) == 0:
        studentHomeAddress = "NULL"

    #comma checks
    studentHomeAddress = studentHomeAddress.replace(",", "")
    studentCampusAddress = studentCampusAddress.replace(",", "")

    file_object = open(firstFileName, 'a')
    file_object.write(studentName + ",")
    file_object.write(classification + ",")
    file_object.write(major + ",")
    file_object.write(studentEmail + ",")
    file_object.write(studentHomePhone + ",")
    file_object.write(studentCampusPhone + ",")
    file_object.write(studentHomeAddress + ",")
    file_object.write(studentCampusAddress)
    file_object.write("\n")
    file_object.close()

#removes nonascii chars from a string
def parseNonAscii(text):
    return re.sub(r'[^\x00-\x7F]+',' ', text)

#generates pairs from aa to zz, starts from the given value if it isn't aa
def generatePairsList(startFrom = 'aa'):
    ret = []

    startI = alphas.index(startFrom[0])
    startJ = alphas.index(startFrom[1])

    for i in range(startI,26):
        for j in range(startJ,26):
            ret.append(alphas[i] + alphas[j])

    return ret

#removes duplicate lines from the given file and outputs a new file
def removeDuplicateLines(filename):
    try:
        if os.path.exists(filename):
            linesSeen = []
            newFilename = os.path.dirname(os.path.realpath(filename)) + "/" + os.path.basename(filename).split(".")[0] + '_Non_Duplicates.txt'
            newFileWriter = open(newFilename, "w+")

            with open(filename) as f:
                lines = f.readlines()
                for line in lines:
                    if line not in linesSeen:
                        linesSeen.append(line)
                        newFileWriter.write(line)

            
            newFileWriter.close()
        else:
            print("Passed file DNE")
    except:
        pass

#webscraping method directly using the backend API provided user is authenticated
def apiMain():
    print("Begining scraping sequence")
    exe = os.path.exists(PATH)

    if exe:
        print("Executable found")

        #option = webdriver.ChromeOptions()
        #option.add_argument('headless')
        #driver = webdriver.Chrome(options = option)
        driver = webdriver.Chrome()
        
        driver.get("https://my.msstate.edu/")

        elem = driver.find_element(By.ID,USERNAME_ID)
        elem.clear()
        elem.send_keys(INJECTION_NAME)

        elem = driver.find_element(By.ID, PASSWORD_ID)
        elem.clear()
        elem.send_keys(INJECTION_PASSWORD)

        driver.find_element(By.NAME,'submit').click()

        #DUO handling
        masterElemnString = "login"
        myElem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, masterElemnString)))
        print(f"DUO {masterElemnString} loaded")

        #switch to duo iFrame
        iFrameTitle = "duo_iframe"
        driver.switch_to.frame(iFrameTitle)

        #wait for push button to load and click it
        pushButtontext = "Send Me a Push"
        WebDriverWait(driver, PUSH_TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{pushButtontext}')]"))).click()
        print("Push sent")

        #wait for directory to load to confirm we're in the system
        directoryID = "portlet_MSUDirectory1612_WAR_directory1612"
        WebDriverWait(driver, 40).until(
            EC.presence_of_element_located((By.ID, directoryID)))
        print("Directory element loaded")
        
        #copy over cookies from duo authentication
        yummyCookies = driver.get_cookies()

        session = requests.Session()
        for cookie in yummyCookies:
            session.cookies.set(cookie['name'], cookie['value'])
        
        vowels = ['a','e','i','o','u','y']
        #loop through all last name contains a vowel
        for last in vowels:
            #get the number of records there are with this search to construct our loops accordingly
            totalResultsRet = post(session, '{"searchType":"Advanced","netid":"nvc29","field1":"lname","oper1":"contain","value1":"' + last + '","field2":"fname","oper2":"contain","value2":"' + "" + '","field3":"title","oper3":"contain","value3":"","rsCount":"0","type":"s"}')
            totalResults = int(re.sub("[^0-9]", "", totalResultsRet))
            pages = math.ceil(totalResults / 10.0)
            print(pages,'pages for last:',last)

            if totalResults == 0:
                continue

            for page in range(pages + 1):
                print("Page",page,"of",pages,"last:",last)
                postData = '{"searchType":"Advanced","netid":"nvc29","field1":"lname","oper1":"contain","value1":"' + last + '","field2":"fname","oper2":"contain","value2":"' + "" + '","field3":"title","oper3":"contain","value3":"","rsCount":"' + str(page) + '","type":"s"}'
                parsePost(post(session, postData))

                #reasonable timeout
                time.sleep(0.5)

        print("Finished all last contains vowels, exiting scraper")

    else:
        print("Executable not found, download from: https://sites.google.com/chromium.org/driver/downloads?authuser=0")

POST = 'https://my.msstate.edu/web/home-community/main?p_p_id=MSUDirectory1612_WAR_directory1612&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=getSearchXml&p_p_cacheability=cacheLevelPage&p_p_col_id=column-2&p_p_col_pos=6&p_p_col_count=7'

def post(session, payload):
    return session.post(POST, data = dict(formData = payload)).text

#tags for parsing people
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

def parsePost(text):
    #create soup of text
    soup = BeautifulSoup(text, 'html.parser')
    #get all person tags to sub parse for information
    tag = soup.find_all(PERSON_TAG)

    for person in tag:
        personSoup = BeautifulSoup(str(person),'html.parser')

        first = re.compile(r'<.*?>').sub('', str(personSoup.find(FIRSTNAME_TAG))).replace("'","").replace('"',"")
        last = re.compile(r'<.*?>').sub('', str(personSoup.find(LASTNAME_TAG))).replace("'","").replace('"',"")
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
        homePhone = "NULL"
        officePhone = "NULL"
        
        for number in numbers:
            if "permanent" in str(number):
                homePhone = re.compile(r'<.*?>').sub('', str(number))
            elif "office" in str(number):
                officePhone = re.compile(r'<.*?>').sub('', str(number))

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

        insertPG(netid, email, first, last, picturePublic, picturePrivate, major,class_, homePhone,officePhone,
                pidm, selected, isStudent, isAffiliate, isRetired, homeStreet, homeCity, homeState, homeZip, homeCountry,
                officeStreet, officeCity, officeState, officeZip, officeCountry)   
#password is 1234
def insertPG(netid, email = "NULL",first = "NULL",last = "NULL",picturePublic = "NULL",picturePrivate = "NULL",major = "NULL",class_ = "NULL",
                homePhone = "NULL",officePhone = "NULL",pidm = "NULL",selected = "NULL",isStudent = "NULL",isAffiliate = "NULL", isRetired = "NULL",
                homeStreet = "NULL",homeCity = "NULL",homeState = "NULL",homeZip = "NULL",homeCountry = "NULL",
                officeStreet = "NULL",officeCity = "NULL",officeState = "NULL",officeZip = "NULL",officeCountry = "NULL"):
    
    con = psycopg2.connect(
        host = "cypherlenovo",
        database = "msu_students" ,
        user = 'postgres',
        password = '1234',
        port = '5433'
    )

    cur = con.cursor()
    command = "INSERT INTO students (netid,email,firstname,lastname,picturepublic,pictureprivate,major,class,homephone,officephone,pidm,selected,isstudent,isaffiliate,isretired,homestreet,homecity,homestate,homezip,homecountry,officestreet,officecity,officestate,officezip,officecountry) VALUES ('{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}','{8}','{9}','{10}','{11}','{12}','{13}','{14}','{15}','{16}','{17}','{18}','{19}','{20}','{21}','{22}','{23}','{24}')".format(netid,email,first,last,picturePublic,picturePrivate,major,class_,homePhone,officePhone,pidm,selected,isStudent,isAffiliate,isRetired,homeStreet,homeCity,homeState,homeZip,homeCountry,officeStreet,officeCity,officeState,officeZip,officeCountry)
    print(command)
    cur.execute(command)
    con.commit()

    cur.close()
    con.close()

if __name__ == "__main__":
    apiMain()
