# Jesse Maitland Python Assessment Task - Hey Jobs

Project created to submit for the application of Python Developer at Hey Jobs Berlin.

#### Goal

Create a simple web scraper to scrape job adds from Berlin from the first page of HeyJobs.com and save them to a database.

Docker containers for postgres and python provided by Hey Jobs.

#### Running Project

The project is built using the provided docker containers. Running the following docker commands will start up the containers in the correct order, 
and copy / run the project automatically in the provided scraper container. The data will then be available
to select from the database "heyjobs"

`docker-compose run --rm start_dependencies`

`docker-compose up scraper`


#### Assumptions

- A job add is always wrapped in an `<a></a>` tag.
- A job uid always has 36 characters
- A job is always in the format `<a href=/en/jobs/uid></a>`
- A job title will have a class `<div class=job-card-title>Job Title</div>`
- Database tables can be dropped an rebuilt each time the scraper is run


#### 
 