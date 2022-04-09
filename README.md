# StudentScraper 
## By Nathan Cheshire

Student Scraper is a web scraping tool that uses Python and Selenium to scrape student details from MSU's student directory.

## Setup

For this stack make sure you can execute python scripts and have Docker Desktop installed. We're going to use Docker for the Postgres instance and python for general purpose scripting. Additionally, I have provided a `PostgresSetup.bat` which will do all the work of setting up Postgres and creating the appropriate database and table.

After the Postgres intance is up and running in a Docker container and you have ensured the database and table were created successfully, place your username and password for MyState inside of `Keys/state.key` in the format: `netid,password`. This will be used with selenium to send a DUO push to obtain cookies which will allow the sending of mass POST requests.

Lastly, assuming everything else is setup, you may invoke `python Poster.py` which will begin the POST sequence and insertions into the Postgres database.

## Method 1: WebCrawling via StudentCrawler.py

This method will simply search through all permutations of first,last containing aa aa, aa ab,...,zz zz, until all student records have been collected and saved to text files. This was my first approach to this problem and is quite inefficient so I would not recommend using `StudentCrawler.py`. This section did, however, teach me a lot about selenium, webscraping, and webcrawling. I was able to figure out how to pass both authentication pages using selenium via this approach.

## Method 2: POST requests via Poster.py

Directly accessing the backend and sending post requests to acquire data is a much faster and more efficient solution. By making a request in Chrome, one can press f12 and go to the networks tab to see any requests recently made. You can then take the request URL and POST data (formData in this case), and write a script to send POST requests and parse the returned data. First, method 2 starts a selenium instance and authenticates itself. The cookies generated via this authentication are then copied over to the python requests object (it isn't necessary to send them with every POST). Method 2 also inserts all parsed student data into a postgres backend for easy storage/access. Data visualizations with the collected student data can be seen below as well as in `MapGenerator.py`.

## StudentQueries.sql

This is mostly a scratch pad for me for testing and debugging purposes.

## Data/

Data holds the CSVs I generated from `MapGenerator.py` which are subsequently utilized for a USA state-by-state HTML Folium output depicting the percentage of students from each of the 50 states.

## MapQuest.py

This script is what I used to query the MapQuest API and convert all of the student addresses within my postgres local db to lat,lon pairs. Resultingly, this opens a plethora of possible data visualizations. Both the home address for each valid user were converted to lat, lon pairs which are stored in the same students table.

## MapGenerator.py

This is the main data visualization script file. It contains methods such as getting an aerial view of a student's home based soley on their netid, producing a heat map of all students at MSU, and even state by state visualizations for statitistics such as enrollment by state (as one would expect it's extremely biased towards MS since as of 12-8-21, 71.73% of students at MSU have a home address within Mississippi. This stat can be seen in `Data/StudentsByStateNormalized.csv`).

## Examples

## Figure 1 - Aerial Address Generation soley from netid

<img src="https://i.imgur.com/mS6MiE7.png" data-canonical-src="https://i.imgur.com/mS6MiE7.png" width = 400px height = 400px/>

## Figure 2 - Route from netid alpha to netid beta

<img src="https://i.imgur.com/GunFwRK.png" data-canonical-src="https://i.imgur.com/GunFwRK.png" width = 400px height = 400px/>

## Figure 3 - Heatmap

Utilizing all of the lat,lon pairs outputed via the `MapQuest.py` script, I used Follium to generate a heatmap of all students who had public addresses that attended MSU during the Fall 2021 semester. The Visualization for this can be seen at the following link: 
<b>https://nathancheshire.github.io/StudentHeatFall2021<b/>

## Figure 4 - StreetView Visualizations

As can be seen in `MapGenerator.py`, a method exists called `generateStreetViewImage()`. Using this method, which simply takes a netid, I can produce a figure showing the student a picture of their house as if I was standing outside. In testing this works for upwards of 70% I estimate for all students; a number I find acceptable. I plan to make a backend for this program which can be access via a Cyder account
