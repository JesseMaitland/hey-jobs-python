from requests import get
from bs4 import BeautifulSoup


url = 'https://jobs.heyjobs.co/en-de/jobs-in-Berlin'

result = get(url)


soup = BeautifulSoup(result.text)


