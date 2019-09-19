import pymongo
from credentials import credentials

def mongo_client():
    return pymongo.MongoClient(
        host=credentials['mongo']['host'],
        port=credentials['mongo']['port'],
        username=credentials['mongo']['username'],
        password=credentials['mongo']['password'],
    )

def get_profile(bot_name, client=None):
    if client is None:
        client = mongo_client()
    profile = client.blackfalcon.bots.find_one({'name': bot_name})
    if profile is None:
        raise Exception('Bot does not exist. Create a profile using the \'new_bot\' command first.')
    return profile


def get_account(username, client=None):
    if client is None:
        client = mongo_client()
    account = client.blackfalcon.account.find_one({'username': username})
    if account is None:
        raise Exception('Account does not exist.')
    return account


def update_account_full(username, new_account, client=None):
    if client is None:
        client = mongo_client()
    client.blackfalcon.account.replace_one({'username': username}, new_account)


def update_account(username, key, new_value):
    client = mongo_client()
    account = get_profile(username, client=client)
    account[key] = new_value
    update_account_full(username, account, client=client)
