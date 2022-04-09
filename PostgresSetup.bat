:: pull the image from Docker hub
docker pull postgres

:: create the volume
docker volume create student-scraper-postgres

::run and bind to proper port
docker run -d --name=student-scraper-postgres -p 5432:5432 -v postgres-volume:/var/lib/postgresql/data -e POSTGRES_PASSWORD=1234 postgres

:: uncomment to enter the shell if needed
::docker exec -it student-scraper-postgres psql -U postgres

:: TODO create tables from schemas

