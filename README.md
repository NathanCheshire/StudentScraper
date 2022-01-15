# StudentScraper 
## By Nathan Cheshire

Student Scraper is a web scraping tool that uses Python and Selenium to scrape student details from MSU's myState directory.

logindata.txt should exist in the top level directory and contain your netid and password in the following format: `netid,password`.

## Method 1: WebCrawling via WebCrawler.py

This method will simply search through all permutations of first,last containing aa aa, aa ab,...,zz zz, until all student records have been collected and saved to text files. This was my first approach to this problem and is quite inefficient so I would not recommend using `WebCrawler.py`. This section did, however, teach me a lot about selenium, webscraping, and webcrawling. I was able to figure out how to pass both authentication pages using selenium via this approach.

## Method 2: POST requests via Poster.py

Directly accessing the backend and sending post requests to acquire data is a much faster and more efficient solution. By making a request in Chrome, one can press f12 and go to the networks tab to see any requests recently made. You can then take the request URL and POST data (formData in this case), and write a script to send POST requests and parse the returned data. First, method 2 starts a selenium instance and authenticates itself. The cookies generated via this authentication are then copied over to the python requests object (it isn't necessary to send them with every POST). Method 2 also inserts all parsed student data into a postgres backend for easy storage/access. Data visualizations with the collected student data can be seen below as well as in `MapGenerator.py`.

## StudentQueries.sql

Assuming you have created a Posgres database on your local machine with the same schema I outlined inside of `create_tables.sql` you should have success executing any of the queries inside of `StudentQueries.sql`. This is mostly a scratch pad for me for testing and debugging purposes. I did, however, make it public for educational purposes only ;)

## Data/

Data holds the CSVs I generated from `MapGenerator.py` which are subsequently utilized for a USA state-by-state HTML Folium output depicting the percentage of students from each of the 50 states.

## MapQuestAPI.py

This script is what I used to query the MapQuest api and convert all of the student addresses within my postgres local db to lat,lon pairs. Resultingly, this opens a plethora of possible data visualizations. Both the home address and office address for each valid user was converted to lat, lon pairs which are stored in their respective tables: home_addresses, office_addresses. This schemas include the netid as the PK, as well as a double for both the lat and lon.

## MapGenerator.py

This is the main data visualization script file. It contains methods such as getting an aerial view of a student's home based soley on their netid, producing a heat map of all students at MSU, and even state by state visualizations for statitistics such as enrollment by state (as one would expect it's extremely biased towards MS since as of 12-8-21, 71.73% of students at MSU have a home address within Mississippi. This stat can be seen in `Data/StudentsByStateNormalized.csv`).

## Example

By calling `generateStaticImageFromNetid()` and passing in a netid such as `wvb26`, I can produce the following figure within seconds. I find this an exceptionally cool party trick (if you're into parties and all that).

## Figure 1 - Aerial Address Generation soley from netid

<img src="https://i.imgur.com/mS6MiE7.png" data-canonical-src="https://i.imgur.com/mS6MiE7.png" width = 400px height = 400px/>

## Example 2

By calling `pathFromNetidToNetid()` and passing in two netids, I can produce the following figure depicting the addresses of the two students as well as a path from point to point navigatable by common roads. These waypoints also include exact student information such as full name, netid, and an html formatted address.

## Figure 2 - Route from netid to netid

<img src="https://i.imgur.com/GunFwRK.png" data-canonical-src="https://i.imgur.com/GunFwRK.png" width = 400px height = 400px/>

## Example 3 - Generalized Visualization

Utilizing all of the lat,lon pairs outputed via the `MapQuestAPI.py` script, I used Follium to generate a heatmap of all students who had public addresses that attended MSU during the Fall 2021 semester. The Visualization for this can be seen at the following link: 
<b>https://nathancheshire.github.io/StudentHeatFall2021<b/>

## Example 4 - StreetView Visualizations

As can be seen in `MapGenerator.py`, a method exists called `generateStreetViewImage()`. Using this method, which simply takes a netid, I can produce a figure showing the student a picture of their house as if I was standing outside. Not creepy at all I swear, it's for research purposes!
