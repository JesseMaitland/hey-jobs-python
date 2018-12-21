from requests import get
from bs4 import BeautifulSoup
from .project_logging import logger_factory
from .models import session_factory, JobAdd


logger_name = __name__ + '_logger'
ex_logger_name = __name__ + '_ex_logger'

# get a logger to log things about the sate machine
logger = logger_factory(file_name='logs/scrape-machine.log',
                        logger_name=logger_name)

ex_logger = logger_factory(file_name='logs/exceptions.log',
                           logger_name=ex_logger_name,
                           print_stream=False)

class StateError(Exception):
    pass

class State:

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

    def run(self):
        pass

    def next(self):
        pass


class ExitProgram(State):

    def run(self):
        pass

    def next(self):
        logger.info('Program exits.....')
        exit(0)


class RequestPage(State):

    allowed = []
    default = ['ParsePage']

    def __init__(self, url):
        super(RequestPage, self).__init__()
        self.url = url
        self.success = False
        self.html = None

    def run(self):
        try:
            logger.info('requesting data from {}'.format(self.url))
            response = get(self.url)

            if not response.ok:
                raise StateError('a bad request was made to {} '.format(self.url))
            else:
                self.html = response.content

            self.success = True
        except Exception:
            logger.warning('There was an exception in the RequestPage state. Check exception log/exception.log for stack trace.')
            ex_logger.exception('There was an exception in the RequestPage state. the error was: ')

    def next(self):
        if self.success:
            logger.info('retrieved data successfully from {}'.format(self.url))
            return ParsePage(self.html)
        else:
            return Error()


class ParsePage(State):

    def __init__(self, data):
        super(ParsePage, self).__init__()
        self.data = data
        self.success = False
        self.soup = None
        self.job_adds = None
        self.db_job_adds = list()
        self.can_save = False

    def run(self):
        try:
            logger.info('scraping / parsing html from successful request.')

            # use beautiful soup to parse out this mess
            self.soup = BeautifulSoup(self.data, features="html.parser")

            # make sure we have valid html. if not we won't have anything to parse
            if not self.soup.find():
                raise StateError('invalid html received in ParsePage state.')

            self.job_adds = self.soup.find_all('a')
            self.strip_element()
            self.make_job_adds()

            # only mark success if we actually have job adds to post to the db.
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
            return SaveData()

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
    pass