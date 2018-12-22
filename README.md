# Jesse Maitland Python Assessment Task - Hey Jobs

Project created to submit for the application of Python Developer at Hey Jobs Berlin.

### Goal

Create a simple web scraper to scrape job adds from Berlin from the first page of HeyJobs.com and save them to a database.

Docker containers for postgres and python provided by Hey Jobs.

### Running Project

The project is built using the provided docker containers. Running the following docker commands will start up the containers in the correct order, 
and copy / run the project automatically in the provided scraper container. The data will then be available
to select from the database "heyjobs"

`docker-compose run --rm start_dependencies`

`docker-compose up scraper`

the scraper container can be accessed via bash by running
`docker-compose run --entrypoint /bin/bash scraper`

### Tests
tests can be run from the terminal

### Assumptions

- A job add is always wrapped in an `<a></a>` tag.
- A job uid always has 36 characters
- A job is always in the format `<a href=/en/jobs/uid></a>`
- A job title will have a class `<div class=job-card-title>Job Title</div>`
- Database tables can be dropped an rebuilt each time the scraper is run


### Libraries Used

#### Beautiful Soup 4

**Pros**

- well supported 3rd party library for parsing HTML
- parsing html can get messy with home rolled solution
- uses the python html parser
- solves the parsing problem quite nicely

**Cons**

- not part of python standard library
- a bit slow
- scraping / request must be made with another library

#### SQL Alchemy

**Pros**

- well supported most used python orm
- makes table creation / deletion easy
- handles simple crud very well, removing the need for messy SQL crud strings in the project
- raw SQL / stored procedures can still be executed if needed
- makes project less dependant on specific brand / flavour of SQL

**Cons**
- not part of python standard library
- must use another library such as alembic to manage migrations
- can create more work if DB tables are edited directly and not through the Alchemy Models.


### Programming Method - Why use a state machine?

while this scraper could have easily been implemented in a single script with fewer lines of code, fewer files and no directory structure
a state machine allows program flow to be easily understood, and later modified by simply adding / removing or modifying 
state objects and transition rules. 

#### Testing
unit tests can be written to test the function of each individual state, and the expected
output when passed good or bad data as it's input parameters. This scenario allows for testing
that the state machine advances to the correct / desired states for a known input

tests can be run from the project root directory using
`python -m unittest -v heyjobslib/tests.py`

### DB credentials

default credentials provided were used

`
dbname: 'heyjobs'
host: 'db'
port: 5432
user: 'test'
password: 'testpass'
`