from scripts.helpers.aux_f import *
from scripts.helpers.dbClient import *
from scripts.helpers.EventManager import *
from scripts.models.waifu import *
from scripts.models.economy import *

from scripts.waifu_fAux import *
from scripts.economy_fAux import *

import pymongo
import random
import datetime
import collections
import math

###########
# FUNCTIONS

def waifu_list_f(ctx, args):
	# parse args
	# parse page number
	numbers = [int(arg) for arg in args if arg.isdigit()]
	if len(numbers) > 1:
		return -1
	page = numbers[0] if len(numbers) == 1 else 1

	# parse ranks
	ranksInArgs = [arg for arg in args if (arg.upper() in WAIFU_RANKS)]
	ranksQuery = ranksInArgs if len(ranksInArgs) > 0 else WAIFU_RANKS

	# parse target user
	mentions = ctx.message.mentions
	if len(mentions) != 0:
		if not isAdmin(ctx.author):
			return -2
		if len(mentions) > 1:
			return -3

		targetUser = mentions[0]
	else:
		targetUser = ctx.author

	# Parse duplicate mode
	duplicateMode = False
	if ("-d" in args) or ("-D" in args) or ("duplicates" in args):
		duplicateMode = True

	# Get waifu profile
	waifuProfile = WaifuProfile.load(ctx.author)

	if len(waifuProfile.waifuList) == 0:
		if targetUser == ctx.author:
			return -4
		else:
			return -5

	# Query waifus from DB
	waifuList = []
	for waifuID in waifuProfile.waifuList:
		waifu = dbClient.getClient().DBot.waifus.find_one({"MAL_data.charID": waifuID})
		waifuList.append(waifu)
	waifuList.sort(key=lambda waifu: waifu["value"], reverse=True)

	if duplicateMode:
		duplicateDict = waifuProfile.getDuplicateWaifuIDs()
		waifuList = [waifu for waifu in waifuList if waifu["MAL_data"]["charID"] in duplicateDict.keys()]

	if len(waifuList) == 0:
		return -6

	if waifuProfile.waifuFavorite is not None:
		waifuFav = getWaifu(waifuProfile.waifuFavorite)
		embedDescription = "Favorite Waifu: {}{}\nFrom: {}".format(
			waifuFav["name"],
			"" if waifuFav["aliases"] == [] else ", alias {}".format(random.choice(waifuFav["aliases"])),
			waifuFav["animeName"])
		thumbnail_url = random.choice(waifuFav["pictures"])
	else:
		embedDescription = discord.Embed.Empty
		thumbnail_url = NO_FAV_WAIFU_URL

	embed = discord.Embed(title="{}'s Harem".format(waifuProfile.user.name), description=embedDescription)
	waifuStart = WAIFU_LIST_WAIFUS_PER_PAGE*(page-1)
	waifuEnd = waifuStart + WAIFU_LIST_WAIFUS_PER_PAGE
	for waifu in waifuList[waifuStart:waifuEnd]:
		fieldName = "{}/{} \U0000300C{}\U0000300D: {}".format(
			waifuList.index(waifu)+1,
			len(waifuList),
			waifu["rank"],
			waifu["name"])

		fieldValue1 = "Source: {}".format(waifu["animeName"])
		fieldValue2 = "Ranking: {}/{}\nValue: {}".format(waifu["ranking"], waifuCount(), waifu["value"])
		fieldValue3 = "Waifu ID: {}".format(waifu["MAL_data"]["charID"])
		fieldValues = [fieldValue1, fieldValue2, fieldValue3]

		if duplicateMode:
			fieldValue4 = "Count: {}".format(duplicateDict[waifu["MAL_data"]["charID"]])
			fieldValues.append(fieldValue4)

		embed.add_field(name=fieldName, value="\n".join(fieldValues), inline=False)

	embed.add_field(name="Total Waifu Value", value="{}".format(pMoney(waifuProfile.getTotalValue())), inline=False)

	embed.set_thumbnail(url=thumbnail_url)
	footerText1 = "Waifu Harem page: {} of {}.".format(page, math.ceil(len(waifuList)/WAIFU_LIST_WAIFUS_PER_PAGE))
	footerText2 = "Search other pages using `>waifu list <page>`"
	embed.set_footer(text=footerText1 + "\n" + footerText2)

	return embed

def waifu_bid_f(user, bidAmount):
	eventManager = EventManager.getEventManager()
	waifuAHEvent = eventManager.getEvent("waifuAH")

	if not waifuAHEvent.isRunning():
		return -1

	ecoProfile = EcoProfile.load(user)
	if not ecoProfile.checkBalance(bidAmount):
		return -2

	if bidAmount <= waifuAHEvent.lastBid:
		return -3

	if abs(bidAmount - waifuAHEvent.lastBid) < waifuAHEvent.bidStepUp:
		return -4

	# If there is an event, check preliminary bidding info
	t = timeNow()
	extendedTime = False
	if (waifuAHEvent.timeEnd - t).total_seconds() < waifuAHEvent.timeThresholdToExtend:
		extendedTime = True

	# Eco unlock previous bidder and eco lock current one
	if waifuAHEvent.user is not None:
		EcoProfile.load(waifuAHEvent.user).unlock()
	ecoProfile.lock()

	# Set this user as current bidder in event
	waifuAHEvent.user = user
	waifuAHEvent.lastBid = bidAmount
	waifuAHEvent.lastBidTime = t

	# Assemble embed and return
	embed = discord.Embed(title="Bid Registered", description="{} made the latest bid!".format(user.name))
	embed.add_field(name="Bid Amount", value="{}".format(pMoney(bidAmount)))

	if extendedTime:
		newEndTime = timeNow() + datetime.timedelta(seconds=self.waifuAuctionHouseEvent.bidTimeExtension)
		tStr = "Auction will stop at {}.".format(newEndTime.strftime("%H:%M:%S"))
		embed.add_field(name="Time Extended!", value=tStr)

	return embed

def waifu_favorite_f(user, favArg):
	if not (favArg.lower() == "clear" or favArg.isdigit()):
		return -2

	waifuProfile = WaifuProfile.load(user)
	if favArg.lower() == "clear":
		waifuProfile.clearFavorite()
		return 1
	if favArg.isdigit():
		newFavWaifuID = int(favArg)
		code = waifuProfile.setFavorite(newFavWaifuID)
		return code

def waifu_ranking_f(user, rankArg):
	if rankArg == "me":
		rankingPos = getWaifuRankingPosition(user)
		rankingLength = getWaifuProfileCount()
		embed = discord.Embed(title="Waifu Ranking", description="You are in position {}/{}.".format(rankingPos, rankingLength))
	else:
		embed = discord.Embed(title="Waifu Ranking", description="Top 5 based on Total Waifu Value.")
		i = 1
		for waifuProfile in getWaifuRankingList()[:5]:
			fieldName = "{}/5: {}".format(i, waifuProfile.user.name)
			fieldValue = "Total Value: {}, with {} waifus".format(waifuProfile.getTotalValue(), len(waifuProfile.waifuList))
			embed.add_field(name=fieldName, value=fieldValue, inline=False)
			i += 1

	return embed

# Fuses 3 lower-rank waifus to get 1 next-rank waifu
# error codes
# >0 (waifuID)	ok
# -1			one of the waifus is not owned by the user
# -2			waifus with different rank
# -3			a SSS waifu was entered
def waifu_fuse_f(user, waifuID1, waifuID2, waifuID3):
	waifuProfile = WaifuProfile.load(user)

	# check if all of the 3 waifus are owned by the user
	waifuListCopy = waifuProfile.waifuList[:]
	try:
		waifuListCopy.remove(waifuID1)
		waifuListCopy.remove(waifuID2)
		waifuListCopy.remove(waifuID3)
	except:
		return -1

	# check if all of the 3 waifus are of the same rank
	waifu1 = getWaifu(waifuID1)
	waifu2 = getWaifu(waifuID2)
	waifu3 = getWaifu(waifuID3)
	if not (waifu1["rank"] == waifu2["rank"] == waifu3["rank"]):
		return -2

	# check if at least one is SSS
	if waifu1["rank"] == "SSS" or waifu2["rank"] == "SSS" or waifu3["rank"] == "SSS":
		return -3

	# if all checks passed, get the a next-rank waifu
	nextRank = WAIFU_RANKS[WAIFU_RANKS.index(waifu1["rank"])+1]

	# Remove waifus from user profile
	waifuProfile.removeWaifu(waifu1)
	waifuProfile.removeWaifu(waifu2)
	waifuProfile.removeWaifu(waifu3)

	# Get random fused waifu
	fusedWaifu = getRandomWaifuByRank(nextRank)
	waifuProfile.addWaifu(fusedWaifu)

	# Assemble embed
	embedTitle = "\U0001F9EC {}'s Waifu Fusion! \U0001F9EC".format(user)
	embedDescription = "You got a {}-tier Waifu!".format(fusedWaifu["rank"])
	embed = discord.Embed(title=embedTitle, description=embedDescription)	

	infoValue1 = "Name: {}".format(fusedWaifu["name"])
	infoValue2 = ", alias {}".format(random.choice(fusedWaifu["aliases"])) if len(fusedWaifu["aliases"]) > 0 else ""
	infoValue3 = "From: {}".format(fusedWaifu["animeName"])
	embed.add_field(name="Basic Information", value=infoValue1+infoValue2+"\n"+infoValue3)

	statsValue1 = "Value: {}".format(fusedWaifu["value"])
	statsValue2 = "Ranking: {}/{}".format(fusedWaifu["ranking"], waifuCount())
	embed.add_field(name="Stats", value=statsValue1+"\n"+statsValue2)

	thumbnail_url = random.choice(fusedWaifu["pictures"])
	embed.set_thumbnail(url=thumbnail_url)

	return embed

def waifu_summon_f(user):
	waifuProfile = WaifuProfile.load(user)
	code = waifuProfile.summonWaifu()

	if code == -1:
		return -1

	waifu = getRandomWaifuByRank(getSummonRank())
	waifuProfile.addWaifu(waifu)

	embedTitle = "\U00002728 {}'s Waifu Summon \U00002728".format(user)
	embedDescription = "You summoned a {}-tier Waifu!".format(waifu["rank"])
	embed = discord.Embed(title=embedTitle, description=embedDescription)

	infoValue1 = "Name: {}".format(waifu["name"])
	infoValue2 = ", alias {}".format(random.choice(waifu["aliases"])) if len(waifu["aliases"]) > 0 else ""
	infoValue3 = "From: {}".format(waifu["animeName"])
	embed.add_field(name="Basic Information", value=infoValue1+infoValue2+"\n"+infoValue3)
	
	statsValue1 = "Value: {}".format(waifu["value"])
	statsValue2 = "Ranking: {}/{}".format(waifu["ranking"], waifuCount())
	embed.add_field(name="Stats", value=statsValue1+"\n"+statsValue2)

	thumbnail_url = random.choice(waifu["pictures"])
	embed.set_thumbnail(url=thumbnail_url)

	return embed
