import os
import json
from bs4.element import NavigableString
import requests
import re
import math
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium import webdriver   # for webdriver
from selenium.webdriver.support.ui import WebDriverWait  # for implicit and explict waits
from selenium.webdriver.chrome.options import Options  # for suppressing the browser

PATH = "chromedriver.exe"

INJECTION_NAME = open("logindata.txt").read().split(',')[0]
INJECTION_PASSWORD = open("logindata.txt").read().split(',')[1]

USERNAME_ID = "username"
PASSWORD_ID = "password"
BUTTON_ID = "btn btn-block btn-submit"

PUSH_TIMEOUT = 30
PAGE_SLEEP_TIMEOUT = 1
QUERRY_SLEEP_TIMEOUT = 1

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

def elementExists(driver, id):
    try:
        driver.find_element(By.ID, id)
    except:
        return False
    return True

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
    
def parseNonAscii(text):
    return re.sub(r'[^\x00-\x7F]+',' ', text)

def generatePairsList():
    ret = []

    for i in range(0,26):
        for j in range(0,26):
            ret.append(alphas[i] + alphas[j])

    return ret

def removeDuplicateLines(filename):
    try:
        if os.path.exists(filename):
            linesSeen = []
            newFilename = "FirstsParsed/" + os.path.basename(filename).split(".")[0] + '_Non_Duplicates.txt'
            newFileWriter = open(newFilename, "w+")

            with open('Firsts/First_Name_Contains_ab.txt') as f:
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
def mmMain():
    try:
        print("Begining scraping sequence")
        exe = os.path.exists(PATH)

        if exe:
            print("Executable found")

            option = webdriver.ChromeOptions()
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
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, directoryID)))
            print("Directory element loaded")
           
            #copy over cookies from duo authentication
            yummyCookies = driver.get_cookies()

            session = requests.Session()
            for cookie in yummyCookies:
                session.cookies.set(cookie['name'], cookie['value'])

            #for first in generatePairsList:
             #   for last in generatePairsList:
            first = "na"
            last = "ch"

            #get the number of records there are with this search to construct our loops accordingly
            totalResultsRet = post(session, '{"searchType":"Advanced","netid":"nvc29","field1":"lname","oper1":"contain","value1":"' + last + '","field2":"fname","oper2":"contain","value2":"' + first + '","field3":"title","oper3":"contain","value3":"","rsCount":"0","type":"s"}')
            totalResults = int(totalResultsRet.replace("<directory.person><count>","").replace("</count></directory.person>",""))
            pages = math.ceil(totalResults / 10.0)

            for page in range(pages + 1):
                print("Page",page,"of",pages,"for first:",first,"and last:",last)
                postData = '{"searchType":"Advanced","netid":"nvc29","field1":"lname","oper1":"contain","value1":"' + last + '","field2":"fname","oper2":"contain","value2":"' + first + '","field3":"title","oper3":"contain","value3":"","rsCount":"' + str(page) + '","type":"s"}'
                print(post(session, postData))

        else:
            print("Executable not found, download from: https://sites.google.com/chromium.org/driver/downloads?authuser=0")
    except Exception as e:
        print("Exception:", e)

POST = 'https://my.msstate.edu/web/home-community/main?p_p_id=MSUDirectory1612_WAR_directory1612&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=getSearchXml&p_p_cacheability=cacheLevelPage&p_p_col_id=column-2&p_p_col_pos=6&p_p_col_count=7'

#returns the text from a post to the state server
def post(session, payload):
    return session.post(POST, data = dict(formData = payload)).text

if __name__ == "__main__":
    #nathanMain()
    mmMain()