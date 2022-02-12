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
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait 

# relative path to selenium driver exe
PATH = "chromedriver.exe"

# your msu netid and password stored in the following format: "netid,password"
INJECTION_NAME = open("logindata.txt").read().split(',')[0]
INJECTION_PASSWORD = open("logindata.txt").read().split(',')[1]

# element ids for duo
USERNAME_ID = "username"
PASSWORD_ID = "password"
BUTTON_ID = "btn btn-block btn-submit"

# timeouts
PUSH_TIMEOUT = 30
PAGE_SLEEP_TIMEOUT = 1
QUERRY_SLEEP_TIMEOUT = 1

# permutations for the firstname to contain
alphas = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 
                'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 
                'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

# the filename to output the results to
firstFileName = ""

def crawl(studentMode = True):
    """
    Webscrapes from the MSU student directory using selenium to find 
    all students in the database and save their information to a file.
    """

    try:
        # ensure selenium driver exists
        print("Begining scraping sequence")
        exe = os.path.exists(PATH)

        if exe:
            print("Executable found")

            # create driver object based on seleium exe
            driver = webdriver.Chrome()
            driver.get("https://my.msstate.edu/")

            # find the CAS username field and input our username
            elem = driver.find_element(By.ID, USERNAME_ID)
            elem.clear()
            elem.send_keys(INJECTION_NAME)

            # find the CAS password field and input our password
            elem = driver.find_element(By.ID, PASSWORD_ID)
            elem.clear()
            elem.send_keys(INJECTION_PASSWORD)

            # find and click teh submit button
            driver.find_element(By.NAME,'submit').click()

            # wait for DUO to load
            masterElemnString = "login"
            myElem = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, masterElemnString)))
            print(f"DUO {masterElemnString} loaded")

            # switch to the DUO iFrame
            iFrameTitle = "duo_iframe"
            driver.switch_to.frame(iFrameTitle)

            # wait for the push button to load and click it
            pushButtontext = "Send Me a Push"
            WebDriverWait(driver, PUSH_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{pushButtontext}')]"))).click()
            print("Push sent")

            # wait for the student directory element to load
            directoryID = "portlet_MSUDirectory1612_WAR_directory1612"
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, directoryID)))
            print("Directory element loaded")

            personType = 's' if studentMode else 'f'

            # select student/faculty RadioButton
            driver.find_element(By.XPATH, f"//input[@value='{personType}']").click()

            # generate permutations to loop through
            firsts = generatePairsList()
            lasts = generatePairsList()

            # skip permutations we have already performed
            skips = 0
            skipped = count_files('FirstsParsed')
            print('skipped:', skipped)

            # outer loop for first permutations, inner loop implies a runtime of O(n^2)
            for firstIndex in range(len(firsts)):
                if skips != skipped:
                    print("Skipping: first =", firsts[firstIndex])
                    skips += 1
                    continue

                # create the file we're going to write to for the firstname permutation
                global firstFileName
                firstFileName = "Firsts/First_Name_Contains_" + firsts[firstIndex] + ".txt"

                # open our file with overwrite permissions
                file = open(firstFileName,'w+')
                file.close()

                # inner loop for last permutations
                for last in lasts:
                    try:
                        # inject the lastname string into the field
                        firstSearchFieldID = 'fld1_search_term'
                        elem = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, firstSearchFieldID)))
                        elem.clear()
                        elem.send_keys(last)

                        # inject the firstname string into the field
                        secondSearchFieldID = 'fld2_search_term'
                        elem = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, secondSearchFieldID)))
                        elem.clear()
                        elem.send_keys(firsts[firstIndex])

                        # click submit 
                        searchText = "submit"
                        myElem = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, searchText)))
                        myElem.click()

                        # wait for results to load
                        time.sleep(0.5)

                        # find the number of students returned
                        countElement = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, 'count')))
                        elementCount = int(re.search(r'\d+', countElement.get_attribute('innerHTML')).group())

                        print("---------------------------------")
                        print("Querry: first =",firsts[firstIndex],"last =",last)
                        print('Records returned:', elementCount)

                        # find the number of pages
                        numPages = int(math.ceil(elementCount / 10.0))
                        print('Number of pages:',numPages)
                        print("---------------------------------")

                        # if no results returned, continue
                        if elementCount == 0:
                            continue

                        # loop through pages returned from this query
                        page = 0
                        while page < numPages + 1:
                            # get information for each person on current page
                            for person in driver.find_elements(By.CLASS_NAME, "person"):
                                printPersonDetails(driver, person, 
                                    person.get_attribute('innerHTML'))

                            # if the pagenumber element exists, execute the 
                            # javascript function to go to the next page
                            if elementExists(driver, 'pagenums'):
                                driver.execute_script("getDetails(0)") 
                                
                            # inc page counter
                            page += 1

                            # sleep an adequate time to avoid spamming the backend
                            time.sleep(PAGE_SLEEP_TIMEOUT) 

                        # sleep even more time
                        time.sleep(QUERRY_SLEEP_TIMEOUT)
                    except Exception as e:
                        # we don't care about errors here
                        continue

                # finished with 1/26th of the permutations
                print(firstFileName,' finished with all last permutations. Continuing to next first permutation')

            # final closing message
            print('All permutations from first and last have been executed; exiting scraper')
        else:
            # inform user where to get a selenium driver
            print("Executable not found, download from: https://sites.google.com/chromium.org/driver/downloads?authuser=0")
    except Exception as e:
        print("Exception:", e)

def count_files(in_directory):
    '''
    Counts the files contained in the provided directory
    '''

    joiner= (in_directory + os.path.sep).__add__
    return sum(
        os.path.isfile(filename)
        for filename
        in map(joiner, os.listdir(in_directory))
    )
def printPersonDetails(driver, person, personName):
    '''
    Finds person details from the provided person html.
    '''

    # init data to find
    classification = "NULL"
    major = "NULL"

    try:
        # parse html tags to find data above
        parent = person.find_element(By.XPATH, "..").find_element(By.XPATH, "..")
        pTags = parent.find_elements(By.CSS_SELECTOR, "p")
        classification = pTags[1].get_attribute('innerHTML')
        major = pTags[2].get_attribute('innerHTML')
    except:
        pass

    # if no data found, set to NULL
    if len(classification) == 0:
        classification = "NULL"
    if len(major) == 0:
        major = "NULL"

    # enter the expanded details section
    person.send_keys(Keys.ENTER)

    # wait for the section to load
    detailsID = 'details-section'
    detailsElement = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, detailsID)))

    # parse the html of the returned data section
    parseHTML(detailsElement.get_attribute('innerHTML'), personName, classification, major)

    # click back to return to the returned student results
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located ((By.ID, 'back'))).send_keys(Keys.ENTER)

def elementExists(driver, id):
    '''
    Returns whether the provided id exists within the driver.
    '''
    try:
        driver.find_element(By.ID, id)
    except:
        return False
    return True

def parseHTML(studentDetails, name, classification, major):
    '''
    Parses the html and found details from the student html.
    '''

    # user attributes
    studentName = name
    studentEmail = "NULL"
    studentHomePhone = 0
    studentCampusPhone = 0
    studentCampusAddress = []
    studentHomeAddress = []
   
    mode = "none"
    
    # this is a bad way to parse the html but whatever
    for line in BeautifulSoup(studentDetails, features="html.parser").prettify().split('\n'):
        # parse away bold tags
        if "<b>" in line or "</b>" in line or "<b/>" in line:
            continue
        # parse away break tags
        elif "<br>" in line or "<br/>" in line or "</br>" in line:
            continue
        # parse away a tags
        elif "</a>" in line or "<a" in line or "<a/>" in line:
            continue

        # parse away non-ascii chars within the current line
        line = parseNonAscii(line)

        # figure out what the line contains
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

        # if nothing to parse
        if len(line.strip()) < 3:
            continue

        # based on mode, set the data attribute
        if mode == "email" and line.strip() != "Email":
            studentEmail = line.strip()
        
        # campus or home phone
        elif mode == "phone" and line.strip() != "Phone":
            if "Campus" in line:
                studentCampusPhone = ''.join(c for c in line if c.isdigit())
            else:
                studentHomePhone = ''.join(c for c in line if c.isdigit())

        # campus address
        elif mode == "ca":
            studentCampusAddress.append(line.strip())
        
        # home address
        elif mode == "ha":
            studentHomeAddress.append(line.strip())

    # join addresses with associated data
    studentCampusAddress = " ".join(studentCampusAddress)
    studentHomeAddress = " ".join(studentHomeAddress)

    # empty phone number checks
    if studentHomePhone == 0:
        studentHomePhone = "0"
    if studentCampusPhone == 0:
        studentCampusPhone = "0"
    
    # empty address checks
    if len(studentCampusAddress.strip()) == 0:
        studentCampusAddress = "NULL"
    if len(studentHomeAddress.strip()) == 0:
        studentHomeAddress = "NULL"

    # comma checks as to not break our csv
    studentHomeAddress = studentHomeAddress.replace(",", "")
    studentCampusAddress = studentCampusAddress.replace(",", "")

    # write user object to file
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
    '''
    Removes any non-ascii characters from a string
    '''
    return re.sub(r'[^\x00-\x7F]+',' ', text)

def generatePairsList(startFrom = 'aa'):
    '''
    Generates pairs of double letters from aa, ab, ac,
    ... , zy, zz starting from the provided value.
    '''

    ret = []

    startI = alphas.index(startFrom[0])
    startJ = alphas.index(startFrom[1])

    for i in range(startI,26):
        for j in range(startJ,26):
            ret.append(alphas[i] + alphas[j])

    return ret
    
def removeDuplicateLines(filename):
    """
    Removes any duplicate lines from the provided file and
     ouputs a new file with the duplicates removed.
    """

    try:
        if os.path.exists(filename):
            linesSeen = []
            newFilename = (os.path.dirname(os.path.realpath(filename))
             + "/" + os.path.basename(filename).split(".")[0] + '_Non_Duplicates.txt')
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

# start crawling
if __name__ == "__main__":
    crawl()