###################################################################################
#
#   file for unit tests. Test classes test how each state functions.
#
###################################################################################

import unittest
import logging
from .machine import RequestPage, ParsePage, Error, SaveData, ExitProgram


# disable logging while running unit tests to declutter test output
logging.disable(logging.CRITICAL)


class TestRequestPage(unittest.TestCase):

    """
    class tests the RequestPage State
    """

    def setUp(self):
        self.good_url = 'http://www.google.com'
        self.bad_url = 'www.google.com'
        self.url_404 = 'http://www.google.com/boo'

    def test_success_pagerequest(self):
        """
        makes a get request to a good url. should return a ParsePage state
        :return:
        """
        r = RequestPage(self.good_url)
        r.run()
        self.assertTrue(r.success)
        self.assertTrue(isinstance(r.next(), ParsePage))

    def test_bad_url_pagerequest(self):
        """
        bad url should return an Error state
        :return:
        """
        r = RequestPage(self.bad_url)
        r.run()
        self.assertFalse(r.success)
        self.assertTrue(isinstance(r.next(), Error))

    def test_404_url_pagerequest(self):
        """
        404 not found should return an Error state
        :return:
        """
        r = RequestPage(self.url_404)
        r.run()
        self.assertFalse(r.success)
        self.assertTrue(isinstance(r.next(), Error))


class TestParsePage(unittest.TestCase):

    """
        class tests ParsePage state
    """

    def setUp(self):
        self.html = """
        <div> </div>
        <a href=/en/jobs/1e61e323-1e90-4b0c-a4cf-949ca74bbd7a>
            <div class='job-card-title'>A really great job!</div>
        </a>
        <a href=/en/jobs/1e61e323-1e90-4b0c-a4cf-949ca74bbd7b>
            <div class='job-card-title'>A really bad job!</div>
        </a>
        </div>
        """
        self.garbage = "akjhdsflkajhdfkja*$(hdlkfjhadslkfj!(#*$)_@hadlkfjhaf,mand.nlchaipher8ydpcia61nerlkthqrhEF"
        self.bad_html = "<div><div></div></div>"

    def test_success_parse(self):
        """
        tests successful parsing of job add html should create a proper DB JobAdd model
        and also return a SaveData state
        :return:
        """
        p = ParsePage(self.html)
        p.run()
        self.assertEqual(p.db_job_adds[0].title, 'A really great job!')
        self.assertEqual(p.db_job_adds[0].uid, '1e61e323-1e90-4b0c-a4cf-949ca74bbd7a')
        self.assertTrue(p.success)
        self.assertTrue(isinstance(p.next(), SaveData))
        self.assertEqual(len(p.db_job_adds), 2)
        self.assertEqual(len(p.db_job_adds[0].uid), 36)

    def test_failure_parse(self):
        """
        passing invalid html should return an error state
        :return:
        """
        p = ParsePage(self.garbage)
        p.run()
        self.assertFalse(p.success)
        self.assertTrue(isinstance(p.next(), Error))

    def test_no_jobs_parse(self):
        """
        passing good html with no jobs should return success, but not ok to save.
        should return an exit program state
        :return:
        """
        p = ParsePage(self.bad_html)
        p.run()
        self.assertTrue(p.success)
        self.assertFalse(p.can_save)
        self.assertTrue(p.next(), ExitProgram)

