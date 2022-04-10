# StudentScraper 

## By Nathan Cheshire

Student Scraper is a web scraping tool that uses Python and Selenium to scrape student details from MSU's student directory.

### Setup

For this stack, make sure you can execute python scripts and have Docker Desktop installed (WLS is of course recommended). We're going to use Docker for the Postgres instance and python for general purpose scripting. Additionally, I have provided a `PostgresSetup.bat` which will do all the work of setting up Postgres and creating the appropriate database and table.

After the Postgres intance is up and running in a Docker container, and you have ensured the database and table were created successfully, place your username and password for MSU inside of `Keys/state.key` in the format: `netid,password`. This will be used with selenium to send a DUO push to obtain cookies which will allow the sending of mass POST requests. Make sure you accept this DUO push on your phone.

Lastly, following completion of the stuep, you may invoke `python Poster.py` which will begin the POST sequence and insertions into the Postgres database. I'd recommend you activate the virtual environment via `.\venv\Scripts\Activate.bat` before running the Poster script.

To obtain the lat,lon pairs, obtain a MapQuest API key and use that in combination with `MapQuest.py` to conver the stored addresses into lat,lon pairs. MapQuest free tier only allows 15K queries so you'll most likely need a second account for this step.

### Algorithm 1: Web Crawling

This method will simply search through all permutations of first,last containing aa aa, aa ab,...,zz zz, until all student records have been collected and saved to text files. This is a pretty inefficient approach but is a valid procedural algorithm that will work without missing any names, give enough time.

### Algorithm 2: Direct POST Requests

Directly accessing and sending post requests to the MSU backend is a much faster and more efficient solution. By making a request in Chrome, one can press F12 and go to the networks tab to see any requests recently made. You can then take the request URL and POST data (formData in this case), and use that to send POST requests and parse the returned data.

## Files

```
├── Data # the exported CSV/data files for clients
├── Drivers # the Selenium Chrome drivers
├── Figures # exported pngs from visualizations
├── json # the USA polygon json data
├── Keys # keys for MSU, MapQuest, Google, etc.
├── Maps # the exported html Folium renders
├── Query # scratch sql work
├── Tables # create table sql files
├── Visualizations # the visualization scripts
├── .gitignore
├── CreateTables.py # the script which creates the initial student table
├── Poster.py # the POST requestor script
├── PostgresSetup.bat # the setup batch script
├── PythonSetup.bat # the python environment setup script
├── README.md
├── requirements.txt # the Python requirements
└── StudentCrawler.py # the web crawler script
```

### StudentQueries.sql

This is mostly a scratch pad for my testing and debugging purposes.

## Data/

Data holds the CSVs I generated from `MapGenerator.py` which are subsequently utilized for a USA state-by-state HTML Folium output depicting the percentage of students from each of the 50 states.

## MapQuest.py

This script is what I used to query the MapQuest API and convert all of the student addresses within my postgres local db to lat,lon pairs. Resultingly, this opens a plethora of possible data visualizations. Both the home address for each valid user were converted to lat, lon pairs which are stored in the same students table.

## MapGenerator.py

This is the main data visualization script file. It contains methods such as getting an aerial view of a student's home based soley on their netid, producing a heat map of all students at MSU, and even state by state visualizations for statitistics such as enrollment by state (as one would expect it's extremely biased towards MS since as of 12-8-21, 71.73% of students at MSU have a home address within Mississippi. This stat can be seen in `Data/StudentsByStateNormalized.csv`).

## Results

### Figure 1 - Aerial Address Generation

<img src="https://i.imgur.com/mS6MiE7.png" data-canonical-src="https://i.imgur.com/mS6MiE7.png" width = 400px height = 400px/>

<br/>

### Figure 2 - Street Route Plotting

<img src="https://i.imgur.com/GunFwRK.png" data-canonical-src="https://i.imgur.com/GunFwRK.png" width = 400px height = 400px/>

<br/>

### Figure 3 - Heatmap

Utilizing all of the lat,lon pairs outputed via the `MapQuest.py` script, I used Follium (Python version of leaflet.js) to generate a heatmap of all students who had public addresses that attended MSU during the Fall 2021 semester. The Visualization for this can be seen at the following link: 
<b>https://nathancheshire.github.io/StudentHeatFall2021<b/>

### Figure 4 - Google Stree View

As can be seen in `MapGenerator.py`, a method exists called `generateStreetViewImage()`. Using this method, which simply takes a netid, I can produce a figure showing the student a picture of their house as if I was standing outside. In testing this works for upwards of 70% I estimate for all students; a number I find acceptable. I plan to make a backend for this program which can be access via a Cyder account
