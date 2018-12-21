"""
main run program entry point simply imports the scraper state machine and sets it to run.
"""

from heyjobslib.machine import ScrapeMachine

if __name__ == '__main__':
    scrape_machine = ScrapeMachine()
    scrape_machine.run_machine()
