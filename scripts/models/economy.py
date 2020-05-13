from scripts.helpers.dbClient import *
from scripts.helpers.aux_f import *
from scripts.helpers.Bot import *

import datetime

#############
# CONSTANTS

STARTING_MONEY = 15
COLLECTION_MONEY = 5

# class nya?
class EcoProfile:
	def __init__(self, user, balance, timeCreation, timeCollection, lock):
		self.user = user
		self.balance = balance
		self.timeCreation = timeCreation
		self.timeCollection = timeCreation

		self._lock = lock

	#################
	# STATIC METHODS
	
	@staticmethod
	def load(user):
		mongoClient = dbClient.getClient()
		profileDoc = mongoClient.DBot.economy.find({"user.id": user.id})

		if profileDoc is None:
			user = user
			balance = STARTING_MONEY
			timeCreation = timeNow()
			timeCollection = timeNow()
			lock = False
		else:
			user = Bot.getBot().get_user(profileDoc["user"]["id"])
			balance = profileDoc["balance"]
			timeCreation = profileDoc["timeCreation"]
			timeCollection = profileDoc["timeCollection"]
			lock = profileDoc["lock"]

		profile = EcoProfile(user, balance, timeCreation, timeCollection)
		if profileDoc is None:
			profile._save()

		return profile

	####################
	# PUBLIC METHODS

	def changeBalance(changeAmount):
		if self.checkBalance(changeAmount):
			self.balance += changeAmount
			dbClient.getClient().DBot.economy.update_one({"user.id": self.user.id}, {"$set": {"balance": self.balance}})
			return 0
		else:
			return -1

	def checkBalance(self, amountToCheck):
		if amountToCheck < 0:
			return True
		else:
			return self.balance >= amountToCheck

	def collect(self):
		if self._ableToCollect():
			self.changeBalance(COLLECTION_MONEY)
			dbClient.getClient().DBot.economy.update_one({"user.id": self.user.id}, {"$set": {"timeCollection": timeNow().isoformat()}})
			return 0
		else:
			return -1

	def isLocked(self):
		return self._lock

	def lock(self):
		self._lock = True
		dbClient.getClient().DBot.economy.update_one({"user.id": self,user.id}, {"$set": {"lock": self._lock}})

	def unlock(self):
		self._lock = False
		dbClient.getClient().DBot.economy.update_one({"user.id": self,user.id}, {"$set": {"lock": self._lock}})

	##################
	# PRIVATE METHODS

	def _makeDoc(self):
		profileDoc = {"user": {"name": self.user.name, "id": self.user.id},
					  "balance": self.balance,
					  "timeCreation": self.timeCreation.isoformat(),
					  "timeCollection": self.timeCollection.isoformat(),
					  "lock": self._lock
					  }

		return profileDoc

	def _save(self):
		mongoClient = dbClient.getClient()
		if mongoClient.DBot.economy.count_documents({"user.id": self.user.id}) == 0:
			mongoClient.DBot.economy.insert_one(self._makeDoc())
		else:
			mongoClient.DBot.economy.replace_one({"user.id": self.user.id}, self._makeDoc())

	def _ableToCollect(self):
		dateCreated = datetime.date.fromtimestamp(timeCreation.timestamp())
		dateCollected = datetime.date.fromtimestamp(timeCollection.timestamp())
		date = dateNow()
		if date == dateCreated or date == dateCollected:
			return False
		else:
			return True
