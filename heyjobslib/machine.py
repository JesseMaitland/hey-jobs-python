"""

This state machine runs as a web scraper which makes a request to

https://jobs.heyjobs.co/en-de/jobs-in-Berlin?page=1

The scraper then seeks to parse out the job add ids and titles. job adds are in the basic form of

<a href=/en/jobs/id(36)
    <div class=job-card-title> Title is here </div>
</a>


File is used to declare state machine classes. Each class is treated as a separate state that the program
can be in. the states are defined as


State Definitions:
-> InitMachine ->  fist state called to set up anything the rest of the machine will depend on
-> Error       ->  a state which is entered if any previous state encountered a critical problem
-> ExitProgram ->  this state is used to exit the state machine... hopfully with grace.
-> RequestPage ->  makes an http get request and stores the retrieved html
-> ParsePage   ->  parses out the retrieved html from RequestPage state
-> SaveDate    ->  saves parsed data from ParsPage to the db

Each state has a self.success flag, when set true, will allow the program to transition to the next state.

State Transitions:

-> InitMachine -> RequestPage
               |
               -> ExitProgram

-> RequestPage -> ParsePage
               |
               -> Error

-> ParsePage -> SaveData
             |
             -> Error
             |
             -> ExitProgram

-> SaveData -> ExitProgram
            |
            -> Error

-> Error -> ExitProgram


"""
from requests import get
from bs4 import BeautifulSoup
from .project_logging import logger_factory
from .models import session_factory, JobAdd, init_db


# 2 loggers are used to avoid printing exceptions to the console but rather to a file
# as they can be a bit noisy to look at when they are not important.
logger_name = __name__ + '_logger'
ex_logger_name = __name__ + '_ex_logger'

# get a logger to log info and higher to a file and also to the console
logger = logger_factory(file_name='logs/scrape-machine.log',
                        logger_name=logger_name)

# get a logger to log info about exceptions. these do not get logged to the console
ex_logger = logger_factory(file_name='logs/exceptions.log',
                           logger_name=ex_logger_name,
                           print_stream=False)

class StateError(Exception):
    """
    simple class allows throwing a StateError exception in the state machine
    """
    pass


class State:
    """
    acts as the base class for our state machine. all states must inherit this class
    """

    def __init__(self):
        """
        Set an instance state var so it can be easily called for reference
        """
        self.state = self.__str__().lower()

    def __repr__(self):
        """
        Leverages the __str__ method to describe the State.
        """
        return self.__str__()

    def __str__(self):
        """
        Returns the name of the State.
        """
        return self.__class__.__name__

    def run(self):
        """
        run this method to execute the code associated with this state
        :return:
        """
        raise NotImplemented

    def next(self):
        """
        run this method to advance to the next state. this method controls all transition rules.
        :return:
        """
        raise NotImplemented


class Error(State):
    """
    the state called when something bad or unexpected happens can be expanded to determine
    if the state machine could recover from ending up in this state rather than just exiting
    """
    def run(self):
        pass

    def next(self):
        logger.error('an unknown error has caused the program to exit. check /logs for more info.')
        return ExitProgram()


class ExitProgram(State):
    """
    class used to end execution of the state machine. teardown code can also be added here
    to destroy objects or so save program state before exit.
    """

    def run(self):
        pass

    def next(self):
        logger.info('Program exits.....')
        exit(0)


class InitMachine(State):
    """
    class used as the first state we will transition to. in this case
    we will init the db which will create the tables we need to hold our data
    """

    def __init__(self):
        super(InitMachine, self).__init__()
        self.success = False

    def run(self):
        """
        init state -- attempts to build the tables we need in the pg db as defined in the models.py file
        :return: None
        """
        try:
            logger.info('Creating db tables for database heyjobs')
            init_db()
            self.success = True
        except Exception:
            logger.info('There was a problem creating tables for db heyjobs. check logs/exceptions')
            ex_logger.exception('There was a problem creating tables for db heyjobs')

    def next(self):
        """
        if an exception was thrown during db table creation, we can't do anything so just quit.
        :return: ExitProgram
        """
        if self.success:
            logger.info('Creating tables for db heyjobs was successful.')
            return RequestPage('https://jobs.heyjobs.co/en-de/jobs-in-Berlin?page=1')
        else:
            return ExitProgram()


class RequestPage(State):

    """
    state makes an http get request to the desired url
    """

    def __init__(self, url):
        """
        :param url: the url we want to get html from
        """
        super(RequestPage, self).__init__()
        self.url = url
        self.success = False
        self.html = None

    def run(self):
        """
        makes a simple get request to the desired url and fetches the html from it
        :return:
        """
        try:
            logger.info('requesting data from {}'.format(self.url))
            response = get(self.url)

            if not response.ok:
                raise StateError('a bad request was made to {} '.format(self.url))
            else:
                self.html = response.content

            self.success = True
        except Exception:
            logger.warning('There was an exception in the RequestPage state. Check exception log/exception.log.')
            ex_logger.exception('There was an exception in the RequestPage state. the error was: ')

    def next(self):
        """
        this state can transition to
        ParsePage   -> we can transition here if the request worked out as planned passing the html to the parser
        Error       -> we go here if things don't work out. :(
        :return:
        """
        if self.success:
            logger.info('retrieved data successfully from {}'.format(self.url))
            return ParsePage(self.html)
        else:
            return Error()


class ParsePage(State):
    """
    class parses out the passed in html looking for job adds using Beautiful Soup

    """

    def __init__(self, data):
        """
        :param data: well formed html data from hey jobs page
        """
        super(ParsePage, self).__init__()
        self.data = data
        self.success = False
        self.soup = None
        self.job_adds = None
        self.db_job_adds = list()
        self.can_save = False

    def run(self):
        """
        runs job add parsing. each job add is wrapped in an HTML <a> tag.
        :return:
        """
        try:
            logger.info('scraping / parsing html from successful request.')

            # use beautiful soup to parse out this mess
            self.soup = BeautifulSoup(self.data, features="html.parser")

            # make sure we have valid html. if not we won't have anything to parse
            if not self.soup.find():
                raise StateError('invalid html received in ParsePage state.')

            # job adds are wrapped in an <a> html tag
            self.job_adds = self.soup.find_all('a')
            self.strip_element()
            self.make_job_adds()

            # only mark ability to save if we actually have job adds to post to the db.
            if len(self.db_job_adds) > 0:
                self.can_save = True

            # in every case if we get here the code ran without failure
            self.success = True

        except Exception:
            logger.warning('There was an exception in the ParsePage state. check logs/exception.log for stack trace.')
            ex_logger.exception('There ws an error in the parse page state ')

    def next(self):
        """
        This state can transition to
        ExitProgram -> if there is no data to process
        Error       -> if some problem happened while trying to parse data
        SaveData    -> if all is good and we should try to save to the db
        :return:
        """
        if self.success and self.can_save:
            logger.info('job adds parsed successfully')
            return SaveData(self.db_job_adds)

        elif self.success and not self.can_save:
            logger.info('there were no job adds recovered form the parsed html')
            return ExitProgram()

        else:
            return Error()

    def strip_element(self):
        """
        method attempts to strip out the <a> elements which are actually job adds
        assumes the format of <a href= /en/jobs/****>
        :return: a list of good job adds as beautiful soup Tag objects
        """
        good_job_adds = list()
        for job_add in self.job_adds:
            try:
                if '/en/jobs/' in job_add['href']:
                    good_job_adds.append(job_add)
            except KeyError:
                logger.exception('no key found for element {}'.format(job_add))
        self.job_adds = good_job_adds

    def make_job_adds(self):
        """
        takes the list of job adds as parsed from beautiful soup and makes
        a list of sql alchemy models
        :return: a list of sql alchemy JobAdd objects
        """
        for job_add in self.job_adds:
            uid = self.parse_href(job_add)
            title = job_add.find(class_='job-card-title').text

            if uid and title:
                self.db_job_adds.append(JobAdd(uid=uid, title=title))

    def parse_href(self, href_str):
        """
        method parses out the extra junk from the job add <a> href string
        assumes the format
        /en/job/jobID(36)
        this means the jobID is always the 3rd index, and the id is always 36 chars long
        :param href_str:
        :return:
        """
        str = ''
        try:
            str = href_str['href'].split('/')[3][:36]
        except IndexError:
            pass
        finally:
            return str


class SaveData(State):
    """
    class used to save parsed data to the db
    """
    def __init__(self, job_adds):
        super(SaveData, self).__init__()
        self.job_adds = job_adds
        self.success = False

    def run(self):
        """
        method gets a connection to the db and tries to save the job adds one at a time
        :return:
        """
        logger.info('Saving job adds to db...')
        db_session = session_factory()
        logger.info('created db session...')

        for job_add in self.job_adds:
            db_session.add(job_add)
            try:
                db_session.commit()
                logger.info('saved job to the database with ID: {}'.format(job_add.uid))
            except Exception:
                logger.info('there was a problem saving job ID {} to the db. check logs/exceptions'.format(job_add.uid))
                db_session.rollback()

    def next(self):
        """
        this state can transition to
        ExitProgram  -> because this is the last step
        :return:
        """
        return ExitProgram()


class ScrapeMachine():
    """
    class is used to advance / control the state machine
    """
    def __init__(self):
        self.init_state = InitMachine()
        self.current_state = self.init_state

    def run_machine(self):
        """
        continuously run the state machine based on the transition rules declared in the state objects above
        :return: None
        """
        while True:
            self.current_state.run()
            self.current_state = self.current_state.next()

