from scripts.helpers.dbClient import *
from scripts.helpers.aux_f import *

# from scripts.waifu_fAux import *

from bson.codec_options import CodecOptions
import datetime
import collections

# class nya !!!
class WaifuProfile:
	def __init__(self, user, waifuList, waifuFavorite, timeCreation, timeSummoning):
		self.user = user
		self.waifuList = waifuList
		self.waifuFavorite = waifuFavorite
		self.timeCreation = timeCreation
		self.timeSummoning = timeSummoning

	#################
	# STATIC METHODS

	@staticmethod
	def load(user):
		mongoClient = dbClient.getClient()
		timeAware_Collection = mongoClient.DBot.waifu.with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=TIMEZONE))
		profileDoc = timeAware_Collection.find_one({"user.id": user.id})

		if profileDoc is None:
			user = user
			waifuList = []
			waifuFavorite = None
			timeCreation = utcNow()
			timeSummoning = utcNow() - datetime.timedelta(days=1)
		else:
			user = Bot.getBot().get_user(profileDoc["user"]["id"])
			waifuList = profileDoc["waifuList"]
			waifuFavorite = profileDoc["waifuFavorite"]
			timeCreation = profileDoc["timeCreation"]
			timeSummoning = profileDoc["timeSummoning"]

		profile = WaifuProfile(user, waifuList, waifuFavorite, timeCreation, timeSummoning)
		if profileDoc is None:
			profile._save()

		return profile

	#################
	# PUBLIC METHODS

	def addWaifu(self, waifu):
		waifuID = waifu["MAL_data"]["charID"]
		self.waifuList.append(waifuID)
		dbClient.getClient().DBot.waifu.update_one({"user.id": self.user.id}, {"$set": {"waifuList": self.waifuList}})

	def removeWaifu(self, waifu):
		waifuID = waifu["MAL_data"]["charID"]
		self.waifuList.remove(waifuID)
		dbClient.getClient().DBot.waifu.update_one({"user.id": self.user.id}, {"$set": {"waifuList": self.waifuList}})

	def checkWaifu(self, waifu):
		return waifu["MAL_data"]["charID"] in self.waifuList

	def getTotalValue(self):
		waifus = list(dbClient.getClient().DBot.waifus.find({"MAL_data.charID": {"$in": self.waifuList}}))
		return sum([waifu["value"] for waifu in waifus])

	def setFavorite(self, waifuID):
		if not (waifuID in self.waifuList):
			return -1
		else:
			self.waifuFavorite = waifuID
			dbClient.getClient().DBot.waifu.update_one({"user.id": self.user.id}, {"$set": {"waifuFavorite": self.waifuFavorite}})
			return 0

	def clearFavorite(self):
		self.waifuFavorite = None

	def getDuplicateWaifuIDs(self):
		countDict = collections.Counter(self.waifuList)
		duplicateDict = {waifuID:countDict[waifuID] for waifuID in countDict.keys() if countDict[waifuID] > 1}
		return duplicateDict

	def summonWaifu(self):
		if self._ableToSummon():
			dbClient.getClient().DBot.waifu.update_one({"user.id": self.user.id}, {"$set": {"timeSummoning": utcNow()}})
			timeAware_Collection = dbClient.getClient().DBot.waifu.with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=TIMEZONE))
			self.timeSummoning = timeAware_Collection.find_one({"user.id": self.user.id})["timeSummoning"]
			return 0
		else:
			return -1

	#################
	# PRIVATE METHODS

	def _makeDoc(self):
		profileDoc = {"user": {"name": self.user.name, "id": self.user.id},
					  "waifuList": self.waifuList,
					  "waifuFavorite": self.waifuFavorite,
					  "timeCreation": self.timeCreation,
					  "timeSummoning": self.timeSummoning
					  }

		return profileDoc

	def _save(self):
		mongoClient = dbClient.getClient()
		profileDoc = self._makeDoc()
		if mongoClient.DBot.waifu.count_documents({"user.id": self.user.id}) == 0:
			mongoClient.DBot.waifu.insert_one(profileDoc)
		else:
			mongoClient.DBot.waifu.reaplace_one({"user.id": self.user.id}, profileDoc)

	def _ableToSummon(self):
		return dateNow() > timeToDate(self.timeSummoning)
