import datetime
import json
import queue
import traceback
from threading import Thread

import time

from tools import ws_connector, discord_bot, mongo
from credentials import credentials
from tools.discord_bot import DiscordMessageSender


class Scraper:
    def __init__(self):
        self.host = credentials['swarm_node']['host']
        self.port = 8721
        self.token = credentials['swarm_node']['token']
        self.orders = queue.Queue()
        self.reports = queue.Queue()
        self.connector_ok = [False]

    def login(self):
        """
        Logs in to the Swarm node

        :return: Bool success
        """
        t = Thread(target=self.ws_connection_bootstrapper)
        t.start()
        self.orders.put((json.dumps({'command': 'login', 'parameters': {'token': self.token}}), ))

        response = json.loads(self.reports.get()[0])
        if 'success' in response.keys() and response['success'] and response['command'] == 'login':
            self.connector_ok = [True]
            return True
        return False

    def ws_connection_bootstrapper(self):
        ws_connector.Connection(self.host, self.port, self.orders, self.reports)
        self.connector_ok = [False]

    def run(self, bot_name_pool):
        filtered = []
        for bot in bot_name_pool:
            if not mongo.get_profile(bot)['banned']:
                filtered.append(bot)
        bot_name_pool = filtered
        scraped_today, scraping_rounds, successful = 0, 0, 0
        hour = datetime.datetime.now().hour
        while bot_name_pool:
            scraping_rounds += 1
            if len(bot_name_pool) < 3:
                print('Warning: only {} bots left in scraping bots pool'.format(len(bot_name_pool)))

            # Emptying messages queue:
            for i in range(10):
                try:
                    print('Emptied:', json.loads(self.reports.get(timeout=0.01)[0]))
                except queue.Empty:
                    pass

            start = time.time()
            report = self.scrape(bot_name_pool[0])
            duration = time.time() - start
            if report['report']['success']:
                successful += 1
                scraped_today += report['report']['details']['Number of new entries']
                print('Successfully added {} data points in {} minutes, {} seconds'.format(report['report']['details']['Number of new entries'], round(duration // 60), round(duration % 60)))
            else:
                if 'banned' in report['report']['details']['Reason']:
                    print(bot_name_pool[0], 'has been banned')
                    print('Trying again in 30 minutes')
                    discord_bot.DiscordMessageSender('{} has been banned. There {} {} bot{} left in the scraper bots pool'.format(bot_name_pool[0], 'is' if len(bot_name_pool) <= 2 else 'are', len(bot_name_pool) - 1, '' if len(bot_name_pool) <= 2 else 's')).run(credentials['discord']['token'])
                    del bot_name_pool[0]
                    time.sleep(60 * 60)
                else:
                    print('Failed scraping auction houses in {} minutes, {} seconds'.format(round(duration // 60), round(duration % 60)))
                    print('Trying again in 5 minutes')
                    time.sleep(5 * 60)

            if hour == 22 and datetime.datetime.now().hour == 23:
                DiscordMessageSender(f'Today the scraper ran {scraping_rounds} times and was successful {successful} times. It added {scraped_today} entries to the database').run(credentials['discord']['token'])
            hour = datetime.datetime.now().hour

        print('No more bots available, shutting down')
        discord_bot.DiscordMessageSender('No more bots available to scrape HDVs').run(credentials['discord']['token'])

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
            try:
                if 'Your BlackFalconAPI is outdated' in response['report']['details']['Reason']:
                    print('API is outdated')
                if 'banned' in response['report']['details']['Reason']:
                    print('{} has been banned'.format(bot_name))
            except:
                pass
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
    try:
        scraper.run(['Powerseilla', 'Rysticity'])
    except:
        DiscordMessageSender(f'[{datetime.datetime.fromtimestamp(time.time())}] Scraper crashed \n`{traceback.format_exc()}`').run(credentials['discord']['token'])
        raise

