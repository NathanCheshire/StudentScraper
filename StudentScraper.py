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

PATH = "c:/users/nathan/downloads/chromedriver.exe"


INJECTION_NAME = open("logindata.txt").read().split(',')[0]
INJECTION_PASSWORD = open("logindata.txt").read().split(',')[1]

USERNAME_ID = "username"
PASSWORD_ID = "password"
BUTTON_ID = "btn btn-block btn-submit"

PUSH_TIMEOUT = 30

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

            #todo loop through these changing stuff perhaps to get everyone possible
            # check if nothing is returned and continue if so, 
            # otherwise continue for pages and such
            first = 'Nathan'
            last = ''

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

            for page in range(numPages + 1):  
                #get information for each person on current page
                for person in driver.find_elements(By.CLASS_NAME, "person"):
                    printPersonDetails(driver, person)


                if elementExists(driver, 'pagenums'):
                    driver.execute_script(f"getDetails({page})")  
                time.sleep(1) 

            #debugging sleep
            time.sleep(600)
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

    #this is what you should be parsing and saving to an excel sheet
    print("-------------------------------")
    print('Raw HTML:')
    print(myElem.get_attribute('innerHTML'))

    #press back
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located ((By.ID, 'back'))).send_keys(Keys.ENTER)

def elementExists(driver, id):
    try:
        driver.find_element(By.ID, id)
    except:
        return False
    return True

if __name__ == "__main__":
    main()