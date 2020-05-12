from scripts.helpers.aux_f import *
from scripts.helpers.dbClient import *

import datetime
import random

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

##################################
# GENERAL ECONOMY FUNCTIONS

# Returns a string, with the standard money format
# modes:
# simple	$12
# verbose	12 dollars | 1 dollar
def pMoney(amount, mode="simple"):
	# verbose
	if mode == "verbose":
		return "{} {}".format(amount, CURRENCY_NAME_PLURAL if amount > 1 else CURRENCY_NAME_SINGULAR)
	# simple (default)
	else:
		return "{} {}".format(amount, CURRENCY_SYMBOL)

####################################
# ECONOMY PROFILE RELATED FUNCTIONS

# creates an economy profile for an user
# return codes
# 0		ok
# -1	user already has profile
def createEconomyProfile(user):
	if checkEconomyProfile(user) == False:
		profile = {	"id": user.id,
					"name": user.name,
					"balance": STARTING_BALANCE,
					"createTime": timeNow().isoformat(),
					"collectTime": timeNow().isoformat(),
					"locked": False}

		mongoClient = dbClient.getClient()
		mongoClient.DBot.economy.insert_one(profile)
		return 0
	else:
		return -1

# returns true if the user has an economy profile, false otherwise
def checkEconomyProfile(user):
	mongoClient = dbClient.getClient()
	count = mongoClient.DBot.economy.count_documents({"id": user.id})

	if count == 0:
		return False
	else:
		return True

# returns the economy profile for an user
# if the user didnt had a profile, creates one before returning it
def getEconomyProfile(user):
	if checkEconomyProfile(user) == False:
		createEconomyProfile(user)

	mongoClient = dbClient.getClient()
	profile = mongoClient.DBot.economy.find_one({"id": user.id})

	return profile

# changes the balance of an user by an amount
# error codes
# 0		ok
# -1	user does not have a profile
def changeBalance(user, changeAmount):
	if checkEconomyProfile(user) == True:
		mongoClient = dbClient.getClient()
		mongoClient.DBot.economy.update_one({"id": user.id}, {"$inc": {"balance": changeAmount}})
		return 0
	else:
		return -1

# returns true if the user has enough funds in their economy profile, false otherwise
def checkBalance(user, amount):
	profile = getEconomyProfile(user)
	return profile["balance"] >= amount

####################################
# LOTTERY COMMAND RELATED FUNCTIONS

# Generates a ticket for the lottery
def generateTicket():
	ticket = []
	while len(ticket) < LOTTERY_NUMBERS_TO_DRAW:
		n = random.randint(1, LOTTERY_NUMBERS_IN_POOL)
		if n in ticket:
			continue
		else:
			ticket.append(n)
	
	ticket.sort()
	return ticket

# returns the quantity of number that are in both tickets (hits)
def checkTicket(ticket, winningTicket):
	hits = sum([1 if t in winningTicket else 0 for t in ticket])
	return hits

def gameLottery(gamesToPlay):
	winningTicket = generateTicket()

	lotteryReport = {"winningTicket": winningTicket, "games": []}
	for i in range(gamesToPlay):
		ticket = generateTicket()
		hits = checkTicket(ticket, winningTicket)
		prize = LOTTERY_PRIZE_DICTIONARY[hits] if hits in LOTTERY_PRIZE_DICTIONARY.keys() else 0

		lotteryDict = {"ticket": ticket, "hits": hits, "prize": prize}
		lotteryReport["games"].append(lotteryDict)

	return lotteryReport

#############################################
# COLLECT COMMAND RELATED FUNCTIONS

# Checks if an user is able to use the daily collect command
# error codes
# (True, 0)		ok
# (False, -1)	user has created profile in the same day
# (False, -2)	user has already collected today
def ableToCollect(user):
	profile = getEconomyProfile(user)
	tCreated = datetime.datetime.fromisoformat(profile["createTime"])
	dateCreated = datetime.date.fromtimestamp(tCreated.timestamp())

	if dateCreated == dateNow():
		return -1

	tCollected = datetime.datetime.fromisoformat(profile["collectTime"])
	dateCollected = datetime.date.fromtimestamp(tCollected.timestamp())
	if dateCollected == dateNow():
		return -2

	return 0

# adds a daily collection amount to an user balance
# error codes
# 0		ok
# -1	user has created profile in the same day
# -2	user has already collected today
def dailyCollect(user):
	code = ableToCollect(user)
	if code == 0:
		changeBalance(user, COLLECT_AMOUNT)
		mongoClient = dbClient.getClient()
		mongoClient.DBot.economy.update_one({"id": user.id}, {"$set": {"collectTime": timeNow().isoformat()}})
		return 0
	else:
		return code

def ecoLock(user):
	# Ensure eco profile is created
	getEconomyProfile(user)
	# Lock profile
	mongoClient = dbClient.getClient()
	mongoClient.DBot.economy.find({"id": user.id}, {"$set": {"locked": True}})

def ecoUnlock(user):
	# Ensure eco profile is created
	getEconomyProfile(user)
	# Unlock profile
	mongoClient = dbClient.getClient()
	mongoClient.DBot.economy.find({"id": user.id}, {"$set": {"locked": False}})

def isEcoLocked(user):
	ecoProfile = getEconomyProfile(user)
	return ecoProfile["locked"]

# Returns a list with the players sorted by descending total balance
def getEconomyRankingList():
	mongoClient = dbClient.getClient()
	ecoProfiles = list(mongoClient.DBot.economy.find({}).sort("balance", pymongo.DESCENDING))
	return ecoProfiles
