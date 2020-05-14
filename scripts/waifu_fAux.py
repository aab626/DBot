from scripts.helpers.dbClient import *
from scripts.helpers.Bot import *
from scripts.models.waifu import *

import random

WAIFU_RANKS = ["E", "D", "C", "B", "A", "S","SS", "SSS"]
NO_FAV_WAIFU_URL = "https://raw.githubusercontent.com/drizak/DBot/master/static/noFavWaifu.png"
WAIFU_LIST_WAIFUS_PER_PAGE = 5

# returns a waifu based on MAL character id
def getWaifu(MAL_charID):
	waifu = dbClient.getClient().DBot.waifus.find_one({"MAL_data.charID": MAL_charID})
	return waifu

# Returns the number of waifus in the DB
def waifuCount():
	return dbClient.getClient().DBot.waifus.count_documents({})

# Returns a list with the ranking list sorted by descending total waifu value
def getWaifuRankingList():
	waifuDocs = list(dbClient.getClient().DBot.waifu.find({}))
	waifuProfiles = [WaifuProfile.load(Bot.getBot().get_user(waifuDoc["user"]["id"])) for waifuDoc in waifuDocs]

	waifuDictRankedList = [{"profile": waifuProfile, "totalValue": waifuProfile.getTotalValue()} for waifuProfile in waifuProfiles]
	waifuDictRankedList.sort(key=lambda waifuDict: len(waifuDict["profile"].waifuList))
	waifuDictRankedList.sort(key=lambda waifuDict: waifuDict["totalValue"], reverse=True)
	
	waifuRankedList = [waifuDict["profile"] for waifuDict in waifuDictRankedList]
	return waifuRankedList

# Returns the position in the ranking of an user (indexing from 1)
def getWaifuRankingPosition(user):
	WaifuProfile.load(user)
	waifuRankingList = getWaifuRankingList()
	position = 1
	for waifuProfile in waifuRankingList:
		if waifuProfile.user == user:
			break

	return position

# returns the number of waifu profiles in the database
def getWaifuProfileCount():
	profileCount = dbClient.getClient().DBot.waifu.count_documents({})
	return profileCount

# returns a random waifu of an specific rank
def getRandomWaifuByRank(rank):
	mongoClient = dbClient.getClient()
	waifusInRank = mongoClient.DBot.waifus.count_documents({"rank": rank})
	waifuCursor = mongoClient.DBot.waifus.find({"rank": rank})

	waifu = waifuCursor[random.randint(0, waifusInRank-1)]
	return waifu

def getSummonRank():
	r = random.random()
	if   0      <= r < 0.025:
		return "C"
	elif 0.025  <= r < 0.125:
		return "D"
	else:
		return "E"

# returns a random waifu based on rank weights
def getRandomWaifu():
	# Probability per rank
	pSSS = 0.0028
	pSS  = 0.0112
	pS   = 0.056
	pA   = 0.07998
	pB   = 0.11997
	pC   = 0.16926
	pD   = 0.25389
	pE   = 0.3069
	
	# Cumulative probability per rank
	aSSS = pSSS
	aSS  = aSSS + pSS
	aS   = aSS  + pS
	aA   = aS   + pA
	aB   = aA   + pB
	aC   = aB   + pC
	aD   = aC   + pD
	aE   = aD   + pE

	# rank selection
	r = random.random()
	if   0    <= r < aSSS:
		rank = "SSS"
	elif aSSS <= r < aSS:
		rank = "SS"
	elif aSS  <= r < aS:
		rank ="S"
	elif aS   <= r < aA:
		rank = "A"
	elif aA   <= r < aB:
		rank = "B"
	elif aB   <= r < aC:
		rank = "C"
	elif aC   <= r < aD:
		rank = "D"
	else:
		rank = "E"

	mongoClient = dbClient.getClient()
	waifusInRank = mongoClient.DBot.waifus.count_documents({"rank": rank})
	waifuCursor = mongoClient.DBot.waifus.find({"rank": rank})

	waifu = waifuCursor[random.randint(0, waifusInRank-1)]
	return waifu
