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

    def run(self):
        try:
            soup = BeautifulSoup(self.data)
            job_adds = soup.find_all('a')
            job_adds = self.strip_element(job_adds)
        except Exception:
            logger.exception('There ws an error in the parse page state ')

    def strip_element(self, anchors):
        good_anchors = list()
        for anchor in anchors:
            try:
                if '/en/jobs/' in anchor['href']:
                    good_anchors.append(anchor)
            except KeyError:
                logger.exception('no key found for element {}'.format(anchor))
        return good_anchors

    def make_job_adds(self, element):