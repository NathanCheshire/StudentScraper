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

PATH = "chromedriver.exe"

INJECTION_NAME = open("logindata.txt").read().split(',')[0]
INJECTION_PASSWORD = open("logindata.txt").read().split(',')[1]

USERNAME_ID = "username"
PASSWORD_ID = "password"
BUTTON_ID = "btn btn-block btn-submit"

PUSH_TIMEOUT = 30

alphas = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 
                'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 
                'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

def main():
    try:
        print("Begining sequence")
        exe = os.path.exists(PATH)

        if exe:
            print("Executable found, continuing")
            WEBSITE = "https://my.msstate.edu/"

            driver = webdriver.Chrome()
            driver.get(WEBSITE)

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
            myElem = WebDriverWait(driver, PUSH_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{pushButtontext}')]")))
            myElem.click()
            print("Push sent")

            #wait for directory to load
            directoryID = "portlet_MSUDirectory1612_WAR_directory1612"
            directory = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, directoryID)))
            print("Directory element loaded")

            #select student radio button
            driver.find_element(By.XPATH, "//input[@value='s']").click()

            #TODO: these will be generated and not explicitly defined lists
            firsts = ["aa"]
            lasts = ["aa","ab"]

            for first in firsts:
                for last in lasts:
                    try:
                        firstSearchFieldID = 'fld1_search_term'
                        elem = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, firstSearchFieldID)))
                        elem.clear()
                        elem.send_keys(last)

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

                        countElement = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, 'count')))
                        elementCount = int(re.search(r'\d+', countElement.get_attribute('innerHTML')).group())
                        print('Records returned:', elementCount)
                        numPages = int(math.ceil(elementCount / 10.0))
                        print('Number of pages:',numPages)

                        #if pages is greater than 1 then we need to go two above it
                        addative = 1 if numPages == 1 else 2

                        page = 0
                        while page < numPages + addative:
                            #get information for each person on current page
                            for person in driver.find_elements(By.CLASS_NAME, "person"):
                                printPersonDetails(driver, person)

                            if elementExists(driver, 'pagenums'):
                                driver.execute_script(f"getDetails({page})") 
                                page += 1

                            time.sleep(1) 
                        time.sleep(3)
                        print('Continuing with next input combiation')
                    except:
                        continue

            print('All permutations from first and last have been ran, exiting scraper')
        else:
            print("Executable not found")
    except Exception as e:
        print("Exception:",e)

def printPersonDetails(driver, person):
    #enter person
    person.send_keys(Keys.ENTER)

    detailsID = 'details-section'
    myElem = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, detailsID)))

    parseHTML(myElem.get_attribute('innerHTML'))

    #press back
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located ((By.ID, 'back'))).send_keys(Keys.ENTER)

def elementExists(driver, id):
    try:
        driver.find_element(By.ID, id)
    except:
        return False
    return True

def parseHTML(studentDetails):
    print(studentDetails)
    print('----------------------------')

def generatePairs():
    for i in range(0,26):
                for j in range(0,26):
                    for k in range(0,26):
                        for m in range(0,26):
                            first = alphas[i] + alphas[j]
                            last = alphas[k] + alphas[m]

if __name__ == "__main__":
    main()
                          