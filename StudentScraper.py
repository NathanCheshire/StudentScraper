import os
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

from Student import Student

PATH = "chromedriver.exe"

INJECTION_NAME = open("logindata.txt").read().split(',')[0]
INJECTION_PASSWORD = open("logindata.txt").read().split(',')[1]

USERNAME_ID = "username"
PASSWORD_ID = "password"
BUTTON_ID = "btn btn-block btn-submit"

PUSH_TIMEOUT = 30
PAGE_SLEEP_TIMEOUT = 1
QUERRY_SLEEP_TIMEOUT = 2.5

alphas = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 
                'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 
                'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

def main():
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

            for first in firsts:
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
                        elem.send_keys(first)

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
                        print('Records returned:', elementCount)
                        numPages = int(math.ceil(elementCount / 10.0))
                        print('Number of pages:',numPages)

                        #for all pages returned from this query
                        page = 0
                        while page < numPages + 1:
                            #get information for each person on current page
                            for person in driver.find_elements(By.CLASS_NAME, "person"):
                                printPersonDetails(driver, person, person.get_attribute('innerHTML'))

                            #if the pagenumber element exists, execute js to go to the next page
                            if elementExists(driver, 'pagenums'):
                                driver.execute_script("getDetails(0)") 
                                
                            #inc pages
                            page += 1

                            time.sleep(PAGE_SLEEP_TIMEOUT) 
                        time.sleep(QUERRY_SLEEP_TIMEOUT)

                        print('Continuing with next input permutation')
                    except:
                        continue

            print('All permutations from first and last have been executed; exiting scraper')
        else:
            print("Executable not found, download from: https://sites.google.com/chromium.org/driver/downloads?authuser=0")
    except Exception as e:
        print("Exception:",e)

def printPersonDetails(driver, person, personName):
    #Enter person details section
    person.send_keys(Keys.ENTER)

    #wait for details section ot be loaded
    detailsID = 'details-section'
    detailsElement = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, detailsID)))

    parseHTML(detailsElement.get_attribute('innerHTML'), personName)

    #go back to query results
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located ((By.ID, 'back'))).send_keys(Keys.ENTER)

def elementExists(driver, id):
    try:
        driver.find_element(By.ID, id)
    except:
        return False
    return True

#todo parse out information and store into excell sheet
def parseHTML(studentDetails, name):
    #user attributes
    studentName = name
    studentEmail = "NULL"
    studentPhone = []
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
            studentPhone.append(line.strip())
        elif mode == "ca":
            studentCampusAddress.append(line.strip())
        elif mode == "ha":
            studentHomeAddress.append(line.strip())

    student = Student(studentName, studentEmail, 
        studentPhone, " ".join(studentCampusAddress), " ".join(studentHomeAddress))
    
    print(student.toString())

def parseNonAscii(text):
    return re.sub(r'[^\x00-\x7F]+',' ', text)

def generatePairsList():
    ret = []

    for i in range(0,26):
        for j in range(0,26):
            ret.append(alphas[i] + alphas[j])

    return ret
                    

if __name__ == "__main__":
    main()
                          