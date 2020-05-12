from scripts.helpers.aux_f import *
from scripts.helpers.dbClient import *

import pymongo
import random
import datetime
import collections

###########
# FUNCTIONS

###################################
# WAIFU PROFILE RELATED FUNCTIONS

# creates a waifu profile for an user
# return codes
# 0		ok
# -1	user already has profile
def createWaifuProfile(user):
	if checkWaifuProfile(user) == False:
		profile = {"id": user.id,
				   "name": user.name,
				   "waifuList": [],
				   "totalWaifuValue": 0,
				   "waifuFav": None,
				   "lastSummonDate": (dateNow() - datetime.timedelta(days=1)).isoformat()}

		mongoClient = dbClient.getClient()
		mongoClient.DBot.waifu.insert_one(profile)

		return 0
	else:
		return -1

# returns true if the user has a waifu profile, false otherwise
def checkWaifuProfile(user):
	mongoClient = dbClient.getClient()
	count = mongoClient.DBot.waifu.count_documents({"id": user.id})

	if count == 0:
		return False
	else:
		return True

# returns the waifu profile for an user
# ifthe user didnt had a profile, creates one before returning it
def getWaifuProfile(user):
	if checkWaifuProfile(user) == False:
		createWaifuProfile(user)

	mongoClient = dbClient.getClient()
	profile = mongoClient.DBot.waifu.find_one({"id": user.id})

	return profile

# adds a waifu to an user waifu profile
def addWaifu(user, waifu):
	profile = getWaifuProfile(user)
	profile["waifuList"].append(waifu["MAL_data"]["charID"])
	profile["totalWaifuValue"] += waifu["value"]

	mongoClient = dbClient.getClient()
	mongoClient.DBot.waifu.replace_one({"id": user.id}, profile)

# returns true if an user has a waifu, false otherwise
def checkWaifu(user, waifu):
	profile = getWaifuProfile(user)
	waifuID = waifu["MAL_data"]["charID"]
	return (waifuID in profile["waifuList"])

# removes a waifu from an user profile
# return codes
# 0 	ok
# -1	user does not have this waifu
def removeWaifu(user, waifu):
	if checkWaifu(user, waifu):
		profile = getWaifuProfile(user)
		waifuID = waifu["MAL_data"]["charID"]
		profile["waifuList"].remove(waifuID)
		profile["totalWaifuValue"] -= waifu["value"]

		mongoClient = dbClient.getClient()
		mongoClient.DBot.waifu.replace_one({"id": user.id}, profile)
		return 0
	else:
		return -1		

# returns a waifu based on MAL character id
def getWaifu(MAL_charID):
	mongoClient = dbClient.getClient()
	waifu = mongoClient.DBot.waifus.find_one({"MAL_data.charID": MAL_charID})
	return waifu

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

def getRandomWaifuByRank(rank):
	mongoClient = dbClient.getClient()
	waifusInRank = mongoClient.DBot.waifus.count_documents({"rank": rank})
	waifuCursor = mongoClient.DBot.waifus.find({"rank": rank})

	waifu = waifuCursor[random.randint(0, waifusInRank-1)]
	return waifu

def waifuCount():
	mongoClient = dbClient.getClient()
	n = mongoClient.DBot.waifus.count_documents({})
	return n

# changes the waifu ID of the favorite waifu in an users profile
# return codes
# 0		ok
# -1	user does not have this waifu id in their list
# -2	bad argument
def setFavoriteWaifu(user, favArg):
	if favArg == "clear":
		newFavWaifu = None
	elif favArg.isdigit():
		profile = getWaifuProfile(user)
		waifuID = int(favArg)
		if not (waifuID in profile["waifuList"]):
			return -1
		else:
			newFavWaifu = waifuID
	else:
		return -2

	mongoClient = dbClient.getClient()
	mongoClient.DBot.waifu.find_one_and_update({"id": user.id}, {"$set": {"waifuFav": newFavWaifu}})
	return 0

# returns the number of waifu profiles in the database
def getWaifuProfileCount():
	mongoClient = dbClient.getClient()
	profileCount = mongoClient.DBot.waifu.count_documents({})
	return profileCount

# Returns a cursor with the ranking list sorted by descending total waifu value
def getWaifuRankingList():
	aggregateQuery = [
					    {
					        '$match': {}
					    }, {
					        '$addFields': {
					            'waifuCount': {
					                '$size': '$waifuList'
					            }
					        }
					    }, {
					        '$sort': {
					            'waifuCount': -1
					        }
					    }, {
					        '$sort': {
					            'totalWaifuValue': -1
					        }
					    }
					]

	mongoClient = dbClient.getClient()
	waifuProfiles = mongoClient.DBot.waifu.aggregate(aggregateQuery)
	return list(waifuProfiles)

# Returns the position in the ranking of an user
def getWaifuRankingPosition(user):
	waifuProfile = getWaifuProfile(user)
	mongoClient = dbClient.getClient()
	countUsersOnTop = mongoClient.DBot.waifu.count_documents({"totalWaifuValue": {"gte": waifuProfile["totalWaifuValue"]}})
	
	positionInRanking = countUsersOnTop + 1
	return positionInRanking

# Fuses 3 lower-rank waifus to get 1 next-rank waifu
# error codes
# >0 (waifuID)	ok
# -1			one of the waifus is not owned by the user
# -2			waifus with different rank
# -3			a SSS waifu was entered
def fuseWaifus(user, waifuID1, waifuID2, waifuID3):
	profile = getWaifuProfile(user)

	# check if all of the 3 waifus are owned by the user
	waifuListCopy = profile["waifuList"][:]
	try:
		waifuListCopy.remove(waifuID1)
		waifuListCopy.remove(waifuID2)
		waifuListCopy.remove(waifuID3)
	except:
		return -1

	# Check if all of the 3 waifus are of the same rank
	waifu1 = getWaifu(waifuID1)
	waifu2 = getWaifu(waifuID2)
	waifu3 = getWaifu(waifuID3)
	if not (waifu1["rank"] == waifu2["rank"] == waifu3["rank"]):
		return -2

	# check if at least one is SSS
	if waifu1["rank"] == "SSS" or waifu2["rank"] == "SSS" or waifu3["rank"] == "SSS":
		return -3

	# If all checks passed, get the a next-rank waifu
	ranks = ["E", "D", "C", "B", "A", "S", "SS", "SSS"]
	nextRank = ranks[ranks.index(waifu1["rank"])+1]

	# Remove waifus from user profile
	removeWaifu(user, waifu1)
	removeWaifu(user, waifu2)
	removeWaifu(user, waifu3)

	# Get random fused waifu
	fusedWaifu = getRandomWaifuByRank(nextRank)
	addWaifu(user, fusedWaifu)

	return fusedWaifu["MAL_data"]["charID"]

def getSummonRank():
	r = random.random()
	if   0      <= r < 0.025:
		return "C"
	elif 0.025  <= r < 0.125:
		return "D"
	else:
		return "E"

def getDuplicateWaifus(user):
	waifuProfile = getWaifuProfile(user)
	countDict = collections.Counter(waifuProfile["waifuList"])
	duplicateDict = {waifuID:countDict[waifuID] for waifuID in countDict.keys() if countDict[waifuID] > 1}
	return duplicateDict
