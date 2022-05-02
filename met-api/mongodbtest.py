from pymongo import MongoClient
from random import randint
from dotenv import load_dotenv
from fetchEnv import MONGO_PORT
# pprint library is used to make the output look more pretty
# connect to MongoDB, change the << MONGODB URL >> to reflect your own connection string
client = MongoClient(port=MONGO_PORT)
# Database Name
db = client.formio
 
# Collection Name
col = db.forms
 
# Get the first item
x = col.find_one()

print(x)


  
