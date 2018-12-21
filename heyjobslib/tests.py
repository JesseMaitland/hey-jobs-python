import unittest
from .machine import RequestPage, ParsePage, Error, SaveData



class TestRequestPage(unittest.TestCase):

    def setUp(self):
        self.good_url = 'http://www.google.com'
        self.bad_url = 'www.google.com'
        self.url_404 = 'http://www.google.com/boo'

    def test_success(self):
        r = RequestPage(self.good_url)
        r.run()
        self.assertTrue(r.success)
        self.assertTrue(isinstance(r.next(), ParsePage))

    def test_bad_url(self):
        r = RequestPage(self.bad_url)
        r.run()
        self.assertFalse(r.success)
        self.assertTrue(isinstance(r.next(), Error))

    def test_404_url(self):
        r = RequestPage(self.url_404)
        r.run()
        self.assertFalse(r.success)
        self.assertTrue(isinstance(r.next(), Error))


class TestParsePage(unittest.TestCase):

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

    def test_success(self):
        p = ParsePage(self.html)
        p.run()
        self.assertEqual(p.db_job_adds[0].title, 'A really great job!')
        self.assertEqual(p.db_job_adds[0].uid, '1e61e323-1e90-4b0c-a4cf-949ca74bbd7a')
        self.assertTrue(p.success)
        self.assertTrue(isinstance(p.next(), SaveData))
        self.assertEqual(len(p.db_job_adds), 2)

    def test_failure(self):
        p = ParsePage(self.garbage)
        p.run()
        self.assertFalse(p.success)
        self.assertTrue(isinstance(p.next(), Error))