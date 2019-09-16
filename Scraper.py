import json
import queue
from threading import Thread

import time

from tools import ws_connector
from credentials import credentials


class Scraper:
    def __init__(self):
        self.host = credentials['swarm_node']['host']
        self.port = 8721
        self.token = credentials['swarm_node']['token']
        self.orders = queue.Queue()
        self.reports = queue.Queue()

    def login(self):
        """
        Logs in to the Swarm node

        :return: Bool success
        """
        t = Thread(
            target=ws_connector.Connection,
            args=(self.host, self.port, self.orders, self.reports)
        )
        t.start()
        self.orders.put((json.dumps({'command': 'login', 'parameters': {'token': self.token}}), ))

        response = json.loads(self.reports.get()[0])
        if 'success' in response.keys() and response['success']:
            return True
        return False

    def run(self, bot_name):
        while 1:
            start = time.time()
            report = self.scrape(bot_name)
            duration = time.time() - start
            if report['report']['success']:
                print('Successfully added {} data points in {} minutes, {} seconds'.format(report['report']['details']['Number of new entries'], round(duration // 60), round(duration % 60)))
            else:
                print('Failed scraping auction houses in {} minutes, {} seconds'.format(round(duration // 60), round(duration % 60)))
                print('Trying again in 5 minutes')
                time.sleep(5 * 60)

    def scrape(self, bot_name):
        """
        Connects and scrapes
        If the bot is subscribed, it will scrape all Bonta's auction houses.
        If not subscribed, it will only scrape Astrub

        :param bot_name: the bot to be used for scraping
        :return: bool success
        """
        self.orders.put((json.dumps({'bot': bot_name, 'command': 'connect'}), ))
        response = json.loads(self.reports.get()[0])
        if 'report' not in response.keys() or 'success' not in response['report'].keys() or not response['report']['success']:
            print('Could not connect')
            if 'Your BlackFalconAPI is outdated' in response['report']['details']['Reason']:
                print('API is outdated')
            return response

        self.orders.put((json.dumps({'bot': bot_name, 'command': 'auctionh_get_all_prices'}), ))
        response = json.loads(self.reports.get()[0])
        if 'report' not in response.keys() or 'success' not in response['report'].keys() or not response['report']['success']:
            print('Scraping failed')
            return response
        return response


if __name__ == '__main__':
    scraper = Scraper()
    scraper.login()
    scraper.run('Smaggie')
    # scraper.run('Jouisseudae')

