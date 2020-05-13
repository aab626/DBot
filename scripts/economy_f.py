from scripts.models.economy import *
from scripts.economy_fAux import *

from scripts.helpers.aux_f import *
from scripts.helpers.dbClient import *
from scripts.helpers.eventManager import *

import datetime
import random
import pymongo

############
# CONSTANTS

STARTING_BALANCE = 15

CURRENCY_SYMBOL = "D\U000000A2"
CURRENCY_NAME_SINGULAR = "DCoin"
CURRENCY_NAME_PLURAL = "DCoins"

LOTTERY_NUMBERS_IN_POOL = 17
LOTTERY_NUMBERS_TO_DRAW = 10
LOTTERY_PRIZE_DICTIONARY = {10: 100, 9: 50, 8: 15, 7: 10}
LOTTERY_MAX_GAMES_ALLOWED = 15
LOTTERY_COST = 5

COLLECT_AMOUNT = 5

###########
# FUNCTIONS

def balance_f(ctx, targetUser):
	if userMentioned != None:
		if isAdmin(ctx.author):
			targetUser = userMentioned
		else:
			return -1
	else:
		targetUser = ctx.author

	profile = EcoProfile.load(targetUser)

	embedTitle = "{}'s Balance".format(profile.user.name)
	embedDescription = pMoney(profile.balance)
	embed = discord.Embed(title=embedTitle, description=embedDescription)
	return embed

def lottery_f(user, gamesToPlay):
	if gamesToPlay > LOTTERY_MAX_GAMES_ALLOWED:
		return -1

	profile = EcoProfile.load(user)
	if profile.isLocked():
		return -2

	totalCost = LOTTERY_COST * gamesToPlay
	if not profile.checkBalance(totalCost):
		return -3

	# When all checks pass, lock the profile
	profile.lock()

	# Play lottery and assemble report embed
	lotteryReport = gameLottery(gamesToPlay)
	ticketStrings = []
	for game in lotteryReport["games"]:
		ticketStr = "{}: `[{}] ({})` | Prize: {}".format(str(lotteryReport["games"].index(game)+1).zfill(2),
														 "-".join([str(t).zfill(2) for t in game["ticket"]]),
														 str(game["hits"]).zfill(2),
														 game["prize"])
		ticketStrings.append(ticketStr)

	totalPrize = sum([game["prize"] for game in lotteryReport["games"]])
	totalChange = totalPrize - totalCost
	if totalChange > 0:
		resultStr = "You won {}!".format(pMoney(totalChange))
	elif totalChange < 0:
		resultStr = "You just lost {} haha".format(pMoney(abs(totalChange)))
	else:
		resultStr = "You didn't win or lose anything"

	embed = discord.Embed(title="Lottery", description="Winning ticket: `[{}]`".format("-".join([str(t).zfill(2) for t in lotteryReport["winningTicket"]])))
	embed.add_field(name="Tickets", value="\n".join(ticketStrings), inline=False)
	embed.add_field(name="Results", value="Total Prize: {}\n".format(totalPrize)+resultStr, inline=False)
	if totalChange == 0:
		embed.set_footer(text="Booooooooooring")

	# Make balance changes and unlock profile
	profile.changeBalance(-totalCost)
	if totalPrize > 0:
		profile.changeBalance(totalPrize)
	profile.unlock()

	return embed

def collect_f(user):
	profile = EcoProfile.load(user)
	code = profile.collect()
	if code == -1:
		return -1
	elif code == 0:
		embedTitle = "Welfare Collected!"
		embedDescription = "You just collected your daily {}".format(pmoney(COLLECTION_MONEY))
		embed = discord.Embed(title=embedTitle, description=embedDescription)
		return embed

def claim_f(user):
	evManager = eventManager.getEventManager()
	claimEvent = evManager.getEvent("claim")

	if not claimEvent.isRunning():
		return -1
	elif user in claimEvent.users:
		return -2
	else:
		claimEvent.users.append(user)
		return 0

def pay_f(originUser, destinationUser, amount):
	if amount <= 0:
		return -1

	originProfile = EcoProfile.load(originUser)
	if originProfile.isLocked():
		return -2

	destinationProfile = EcoProfile.load(destinationUser)
	if destinationProfile.isLocked():
		return -3

	if not originProfile.checkBalance(amount):
		return -4

	originProfile.lock()
	originProfile.changeBalance(-amount)
	originProfile.unlock()

	destinationProfile.lock()
	destinationProfile.changeBalance(amount)
	destinationProfile.unlock()

	embedTitle = "Successful transaction"
	embedDescription = "{} just sent {} to {}.".format(originUser.name, pMoney(amount), destinationUser.name)
	embed = discord.Embed(title=embedTitle, description=embedDescription)
	return embed

def ranking_f():
	embed = discord.Embed(title="Economy Ranking", description="Top 5 based on total Balance.") 
	
	mongoClient = dbClient.getClient()
	ecoDocs = list(mongoClient.DBot.economy.find({}).sort("balance", pymongo.DESCENDING))

	selectedDocs = ecoDocs[:5]
	for ecoDoc in selectedDocs:
		profile = EcoProfile.load(ecoDoc["user"]["id"])
		fieldName = "{}/{}: {}".format(selectedDocs.index(ecoDoc)+1, len(selectedDocs), profile.user.name)
		fieldValue = "Balance: {}".format(pMoney(profile.balance))
		embed.add_field(name=fieldName, value=fieldValue)
	
	return embed