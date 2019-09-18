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