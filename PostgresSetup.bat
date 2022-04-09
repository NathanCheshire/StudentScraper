@echo off

for /f "tokens=1-4 delims=/-. " %%i in ('date /t') do (call :SET_DATE %%i %%j %%k %%l)
goto :START_DOCKER

:SET_DATE
if "%1:~0,1%" gtr "9" shift
for /f "skip=1 tokens=2-4 delims=(-)" %%m in ('echo,^|date') do (set %%m=%1&set %%n=%2&set %%o=%3)

if %mm% LSS 08 (set semester=spring) else (set semester=fall)

:START_DOCKER

ECHO Pulling postgres docker image
docker pull postgres

ECHO Creating volume for scraper
docker volume create student-scraper-postgres

ECHO Running container and binding to port 5432
docker run -d --name=student-scraper-postgres -p 5432:5432 \
        -v postgres-volume:/var/lib/postgresql/data -e POSTGRES_PASSWORD=1234 postgres

set db_name=MSU_%semester%_%yy%
ECHO Creating database with name %db_name%
docker exec -it student-scraper-postgres bash -c "psql -U postgres ; CREATE DATABASE juneblues;"

:EOF_SUCCESS
ECHO Completed pg db and table setup, proceed to Postger.py
EXIT
