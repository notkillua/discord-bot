# Mongodb connection with pymongo
import pymongo
from env import env

client: pymongo.MongoClient = pymongo.MongoClient(env['MONGO_URI'])
db = client['discordbot']
