import random

import scripts.commands.waifu.waifu_const as waifu_const
from scripts.models.userprofile import UserProfile
from scripts.helpers.singletons import dbClient, Bot


# returns a waifu based on MAL character id
def getWaifu(MAL_charID):
	waifu = dbClient.getClient().DBot.waifus.find_one({"MAL_data.charID": MAL_charID})
	return waifu

# Returns the number of waifus in the DB
def waifuCount():
	return dbClient.getClient().DBot.waifus.count_documents({})

# Returns a list with the ranking list sorted by descending total waifu value
def getWaifuRankingList():
	userProfiles = UserProfile.getAllUsers()
	userProfiles.sort(key=lambda profile: len(profile.waifuList), reverse=True)
	userProfiles.sort(key=lambda profile: profile.waifuGetTotalValue(), reverse=True)
	return userProfiles

# Returns the position in the ranking of an user (indexing from 1)
def getWaifuRankingPosition(user):
	UserProfile.load(user)
	waifuRankingList = getWaifuRankingList()
	position = 1
	for waifuProfile in waifuRankingList:
		if waifuProfile.user == user:
			break

	return position

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
	# rank selection
	r = random.random()
	if   0    <= r < waifu_const.aSSS:
		rank = "SSS"
	elif waifu_const.aSSS <= r < waifu_const.aSS:
		rank = "SS"
	elif waifu_const.aSS  <= r < waifu_const.aS:
		rank ="S"
	elif waifu_const.aS   <= r < waifu_const.aA:
		rank = "A"
	elif waifu_const.aA   <= r < waifu_const.aB:
		rank = "B"
	elif waifu_const.aB   <= r < waifu_const.aC:
		rank = "C"
	elif waifu_const.aC   <= r < waifu_const.aD:
		rank = "D"
	else:
		rank = "E"

	mongoClient = dbClient.getClient()
	waifusInRank = mongoClient.DBot.waifus.count_documents({"rank": rank})
	waifuCursor = mongoClient.DBot.waifus.find({"rank": rank})

	waifu = waifuCursor[random.randint(0, waifusInRank-1)]
	return waifu
