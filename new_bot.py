import json
import queue
import uuid
from threading import Thread

from tools import ws_connector
from credentials import credentials

class NewBot:
    def __init__(self, username, password, bot_name, server):
        self.username = username
        self.password = password
        self.bot_name = bot_name
        self.server = server

        self.host = credentials['swarm_node']['host']
        self.port = 8721
        self.token = credentials['swarm_node']['token']
        self.orders = queue.Queue()
        self.reports = queue.Queue()
        self.login()
        self.new_bot()

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

    def new_bot(self):
        order = {
            "bot": self.bot_name,
            "command": "new_bot",
            "parameters": {
                "id": str(uuid.uuid4()),
                "name": self.bot_name,
                "username": self.username,
                "password": self.password,
                "server": self.server
            }
        }
        self.orders.put((json.dumps(order),))
        response = json.loads(self.reports.get()[0])
        if 'success' in response.keys() and response['success']:
            return True
        return False


if __name__ == '__main__':
    new_bot = NewBot()