from requests import get
from bs4 import BeautifulSoup
from .project_logging import logger_factory
from .models import session_factory, JobAdd

# get a logger to log things about the sate machine
logger = logger_factory(file_name='logs/scrape-machine.log',
                        logger_name=__name__)


class State:

    def __init__(self):
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
        raise NotImplemented

    def next(self):
        raise NotImplemented


class Error(State):

    def run(self):
        pass

    def next(self):
        pass




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
                raise Exception('a bad request was made to {} '.format(self.url))
            else:
                self.html = response.content

            self.success = True
        except Exception:
            logger.exception('There was an exception in the RequestPage state. the error was: ')

    def next(self):
        if self.success:
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

    def run(self):
        try:
            self.soup = BeautifulSoup(self.data, features="html.parser")
            self.job_adds = self.soup.find_all('a')
            self.strip_element()
            self.make_job_adds()
            self.success = True
        except Exception:
            logger.exception('There ws an error in the parse page state ')

    def next(self):
        if self.success:
            return SaveData()
        else:
            return Error()

    def strip_element(self):
        good_job_adds = list()
        for job_add in self.job_adds:
            try:
                if '/en/jobs/' in job_add['href']:
                    good_job_adds.append(job_add)
            except KeyError:
                logger.exception('no key found for element {}'.format(job_add))
        self.job_adds = good_job_adds

    def make_job_adds(self):
        for job_add in self.job_adds:
            uid = self.parse_href(job_add)
            title = job_add.find(class_='job-card-title').text

            if uid and title:
                self.db_job_adds.append(JobAdd(uid=uid, title=title))

    def parse_href(self, href_str):
        str = ''
        try:
            str = href_str['href'].split('/')[3][:36]
        except IndexError:
            pass
        finally:
            return str


class SaveData(State):
    pass