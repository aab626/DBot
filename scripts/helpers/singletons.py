import io
import json
import pymongo
import os

from discord.ext import commands


# Singleton for easy access to the main bot
# Always call with getBot() static method
class Bot:
	__instance = None

	def __init__(self, command_prefix):
		if Bot.__instance == None:
			Bot.__instance = commands.Bot(command_prefix)
		else:
			raise Exception("Bot class is meant to be a singleton.")

	@staticmethod
	def getBot(*args):
		if Bot.__instance == None:
			if len(args) != 1 or type(args[0]) != str:
				raise Exception("For the first initialization of Bot, a command_prefix argument must be passed.")
			else:
				command_prefix = args[0]
				Bot(command_prefix)
		
		return Bot.__instance

# Singleton for easy access to the DB connection
# Always call with getClient() static method
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

# Singleton for storing the events
# Always call with getEventManager() static method
class EventManager:
	__instance = None

	def __init__(self):
		if EventManager.__instance == None:
			EventManager.__instance = self
		else:
			raise Exception("EventManager is meant to be a singleton.")

		self._eventDict = dict()

	@staticmethod
	def getEventManager():
		if EventManager.__instance == None:
			EventManager()
		return EventManager.__instance

	def registerEvent(self, event):
		if not (event.name in self._eventDict):
			self._eventDict[event.name] = event
			return 0
		else:
			return -1

	def getEvent(self, eventName):
		if eventName in self._eventDict:
			return self._eventDict[eventName]
		else:
			return -1

	def getEventList(self):
		return self._eventDict.keys()
