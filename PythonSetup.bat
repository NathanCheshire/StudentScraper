@echo off

ECHO Creating a virtual environment for python

python -m venv venv

ECHO Sleeping for 10 seconds

ping 127.0.0.1 -n 11 > nul

ECHO Entering the virtual environment

CALL .\venv\Scripts\activate.bat

ECHO Installing requirements from requirements.txt

pip install -r requirements.txt

ECHO Creating students table

python .\CreateTables.py

ECHO Contents of the students table
docker exec -it student-scraper-postgres psql -U postgres -c "\d+ students"

ECHO Completed pg db and table setup, you may invoke `Python Poster.py` as you are in the virtual environment currently
