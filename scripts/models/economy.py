from scripts.helpers.dbClient import *
from scripts.helpers.aux_f import *
from scripts.helpers.Bot import *

import datetime
from bson.codec_options import CodecOptions

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
		self.timeCollection = timeCollection

		self._lock = lock

	#################
	# STATIC METHODS
	
	@staticmethod
	def load(user):
		mongoClient = dbClient.getClient()
		timeAware_Collection = mongoClient.DBot.economy.with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=TIMEZONE))
		profileDoc = timeAware_Collection.find_one({"user.id": user.id})

		if profileDoc is None:
			user = user
			balance = STARTING_MONEY
			timeCreation = utcNow()
			timeCollection = utcNow()
			lock = False
		else:
			user = Bot.getBot().get_user(profileDoc["user"]["id"])
			balance = profileDoc["balance"]
			timeCreation = profileDoc["timeCreation"]
			timeCollection = profileDoc["timeCollection"]
			lock = profileDoc["lock"]

		profile = EcoProfile(user, balance, timeCreation, timeCollection, lock)
		if profileDoc is None:
			profile._save()

		return profile

	####################
	# PUBLIC METHODS

	def changeBalance(self, changeAmount, forced=False):
		if forced or self.checkBalance(changeAmount):
			self.lock()
			self.balance += changeAmount
			dbClient.getClient().DBot.economy.update_one({"user.id": self.user.id}, {"$set": {"balance": self.balance}})
			self.unlock()
			return 0
		else:
			return -1

	# amountToCheck > 0
	# returns true if the balance is higher or equal than the amount
	def checkBalance(self, amountToCheck):
		amountToCheck = abs(amountToCheck)
		if amountToCheck < 0 or self.balance >= amountToCheck:
			return True
		else:
			return False

	def collect(self):
		if self._ableToCollect():
			self.changeBalance(COLLECTION_MONEY)
			dbClient.getClient().DBot.economy.update_one({"user.id": self.user.id}, {"$set": {"timeCollection": utcNow()}})
			
			timeAware_Collection = dbClient.getClient().DBot.economy.with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=TIMEZONE))
			self.timeCollection = timeAware_Collection.find_one({"user.id": self.user.id})["timeCollection"]
			return 0
		else:
			return -1

	def isLocked(self):
		return self._lock

	def lock(self):
		self._lock = True
		dbClient.getClient().DBot.economy.update_one({"user.id": self.user.id}, {"$set": {"lock": self._lock}})

	def unlock(self):
		self._lock = False
		dbClient.getClient().DBot.economy.update_one({"user.id": self.user.id}, {"$set": {"lock": self._lock}})

	##################
	# PRIVATE METHODS

	def _makeDoc(self):
		profileDoc = {"user": {"name": self.user.name, "id": self.user.id},
					  "balance": self.balance,
					  "timeCreation": self.timeCreation,
					  "timeCollection": self.timeCollection,
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
		dateCreated = timeToDate(self.timeCreation)
		dateCollected = timeToDate(self.timeCollection)
		date = dateNow()
		if date > dateCollected and date > dateCreated:
			return True
		else:
			return False
