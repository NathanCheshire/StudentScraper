# StudentScraper 
## By Nathan Cheshire

Student Scraper is a web scraping tool that uses Python and Selenium to scrape student details from MSU's myState.

logindata.txt should exist in the same directory as `StudentScraper.py` and contain your netid and password in the following format: netid,password.

## Method 1: WebCrawling

This method will simply search through all permutations of first,last containing aa aa, aa ab,...,zz zz, until all student records have been collected and saved to text files. This was my first approach to this problem and is quite inefficient so I would not recommend using `nathanMain()`. This section did, however, teach me a lot about selenium, webscraping, and webcrawling. I was able to figure out how to get past both authentication pages using selenium via this approach.

## Method 2: POST requests

Directly accessing the backend and sending post requests to acquire data is a much faster and more efficient solution. By making a request in Chrome, one can press f12 and go to the networks tab to see any requests recently made. You can then take the request URL and POST data (formData) in this case, and write a script to send POST requests and parse the returned data. Additionallym method 2 inserts all parsed student data into a postgres backend for easy storage/access. Data visualizations with the collected student data are soon to come.