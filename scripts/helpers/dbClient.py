import io
import json
import pymongo
import os

class dbClient:
	__instance = None

	def __init__(self):
		if dbClient.__instance == None:
			with io.open(os.path.join(os.getcwd(), "keys", "mongo.secret"), "r", encoding="utf-8") as f:
				authDict = json.load(f)

			dbClient.__instance = pymongo.MongoClient(host=authDict["hostname"], port=int(authDict["port"]),
													  username=authDict["username"], password=authDict["password"])
		else:
			raise Exception("dbClient is meant to be a singleton.")

	@staticmethod
	def getClient():
		if dbClient.__instance == None:
			dbClient()
		return dbClient.__instance

	def close(self):
		dbClient.__instance.close()
