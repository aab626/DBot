import discord
import discord.utils
from discord.ext import commands

from scripts.waifu_f import *
from scripts.economy_f import *

from scripts.events.ev_waifu_auctionhouse import *

from scripts.helpers.dbClient import *

import datetime
import math
import random

##############
# CONSTANTS

WAIFU_LIST_WAIFUS_PER_PAGE = 5

####################################################
# WAIFU COG

class Waifu(commands.Cog):
	def __init__(self, bot, eventChannel):
		self.bot = bot
		self.eventChannel = eventChannel

		# Add the events to the bot's event loop
		self.waifuAuctionHouseEvent = waifuAuctionHouseEvent(name="waifuAH", bot=self.bot, channel=self.eventChannel,
															 minWait=int(2*3600), maxWait=int(4.5*3600), duration=int(1.5*60),
															 checkWait=60, eventWait=0.1,
															 activityTimeThreshold=30*60, activityWaitMin=int(1*3600), activityWaitMax=int(1.75*3600),
															 timeThresholdToExtend=10, bidTimeExtension=10)

		self.waifuAuctionHouseEvent.startLoop()

	###############
	# WAIFU COMMANDS

	@commands.group()
	async def waifu(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("{}, Invalid command,use `>help`.".format(ctx.message.author.mention))

	# syntax:
	# >waifu list [page] [duplicates|-d|-D] [rank1 rank2...] [@user]
	# reqs: page:	only 1 int
	#		rank	various strs, only in allowed ranks
	#		@User	must be a mention, only for admins
	@waifu.command()
	async def list(self, ctx, *args):
		# parse args
		# parse page number
		numbers = [int(arg) for arg in args if arg.isdigit()]
		if len(numbers) > 1:
			await ctx.send("{}, you can enter at most one page number.".format(ctx.message.author.mention))
			return 0
		page = numbers[0] if len(numbers) == 1 else 1

		# parse ranks
		allRanks = ["SSS", "SS", "S", "A", "B", "C", "D", "E"]
		ranksInArgs = [arg for arg in args if (arg.upper() in allRanks)]
		ranksQuery = ranksInArgs if len(ranksInArgs) > 0 else allRanks

		# select user to use in waifu list command
		mentions = ctx.message.mentions
		if len(mentions) != 0:
			if not isAdmin(ctx.message.author):
				await ctx.send("{}, you have insufficient permissions.".format(ctx.message.author.mention))
				return 0

			if len(mentions) > 1:
				await ctx.send("{}, you can enter at most one mention.".format(ctx.message.author.mention))
				return 0

			targetUser = mentions[0]
		else:
			targetUser = ctx.message.author

		# Get waifu profile
		waifuProfile = getWaifuProfile(targetUser)

		# Determine if searching for duplicates
		duplicateMode = False
		if ("-d" in args) or ("-D" in args) or ("duplicates" in args):
			duplicateMode = True

		if len(waifuProfile["waifuList"]) == 0:
			await ctx.send("{}, this user has no waifus yet \U0001F494".format(ctx.message.author.mention))
			return 0

		# Query waifus from DB
		query = {"$and": [{"rank": {"$in": ranksQuery}}, {"MAL_data.charID": {"$in": waifuProfile["waifuList"]}}]}
		mongoClient = dbClient.getClient()
		waifuList = list(mongoClient.DBot.waifus.find(query).sort("value", pymongo.DESCENDING))

		if duplicateMode:
			duplicateDict = getDuplicateWaifus(ctx.message.author)
			waifuList = [waifu for waifu in waifuList if waifu["MAL_data"]["charID"] in duplicateDict.keys()]

		if len(waifuList) == 0:
			await ctx.send("{}, this search returned no waifus!".format(ctx.message.author.mention))
			return 0

		if waifuProfile["waifuFav"] != None:
			favWaifu = favWaifu = mongoClient.DBot.waifus.find_one({"MAL_data.charID": waifuProfile["waifuFav"]})

			embedDescription = "Favorite Waifu: {}{}\nFrom: {}".format(favWaifu["name"],
																	   "" if favWaifu["aliases"] == [] else ", alias {}".format(random.choice(favWaifu["aliases"])),
																	   favWaifu["animeName"])
			thumbnail_url = random.choice(favWaifu["pictures"])
		else:
			embedDescription = discord.Embed.Empty
			thumbnail_url = "https://raw.githubusercontent.com/drizak/DBot/master/resources/noFavWaifu.png"


		embed = discord.Embed(title="{}'s Harem".format(ctx.message.author.name), description=embedDescription)

		waifuStart = WAIFU_LIST_WAIFUS_PER_PAGE*(page-1)
		waifuEnd = waifuStart + WAIFU_LIST_WAIFUS_PER_PAGE
		for waifu in waifuList[waifuStart:waifuEnd]:
			fieldName = "{}/{} \U0000300C{}\U0000300D: {}".format(waifuList.index(waifu)+1,
																  len(waifuList),
																  waifu["rank"],
																  waifu["name"])
			fieldValue1 = "Source: {}".format(waifu["animeName"])
			fieldValue2 = "Ranking: {}/{}\nValue:{}".format(waifu["ranking"], waifuCount(), waifu["value"])
			fieldValue3 = "Waifu ID: {}".format(waifu["MAL_data"]["charID"])
			fieldValues = [fieldValue1, fieldValue2, fieldValue3]

			if duplicateMode:
				fieldValue4 = "Count: {}".format(duplicateDict[waifu["MAL_data"]["charID"]])
				fieldValues.append(fieldValue4)

			embed.add_field(name=fieldName, value="\n".join(fieldValues), inline=False)

		totalValue = sum([waifu["value"] for waifu in waifuList])
		embed.add_field(name="Total Waifu Value", value="{}".format(pMoney(totalValue)), inline=False)

		embed.set_thumbnail(url=thumbnail_url)
		footerText1 = "Waifu Harem page: {} of {}.".format(page, math.ceil(len(waifuList)/WAIFU_LIST_WAIFUS_PER_PAGE))
		footerText2 = "Search other pages using `>waifu list <page>`"
		embed.set_footer(text=footerText1 + "\n" + footerText2)

		await ctx.send("", embed=embed)

	@waifu.command()
	async def bid(self, ctx, bidAmount: int = 0):

		if not self.waifuAuctionHouseEvent.isRunning():
			await ctx.send("{}, this event is not active right now.".format(ctx.message.author.mention))
			return 0

		if checkBalance(ctx.message.author, bidAmount) == False:
			await ctx.send("{}, you have inssuficient funds to make this bid.".format(ctx.message.author.mention))
			return 0

		if bidAmount <= self.waifuAuctionHouseEvent.lastBid:
			await ctx.send("{}, the minimum bid must be higher than {}.".format(ctx.message.author.mention, pMoney(self.waifuAuctionHouseEvent.lastBid)))
			return 0

		if abs(bidAmount - self.waifuAuctionHouseEvent.lastBid) < self.waifuAuctionHouseEvent.bidStepUp:
			await ctx.send("{}, the minimum bid must be at least {} higher than the previous one.".format(ctx.message.author.mention, 
																										  pMoney(self.waifuAuctionHouseEvent.bidStepUp)))
			return 0

		# if there is an event, check preliminary bidding info
		t = timeNow()
		extendedTime = False
		if (self.waifuAuctionHouseEvent.timeEnd - t).total_seconds() < self.waifuAuctionHouseEvent.timeThresholdToExtend:
			extendedTime = True

		# Eco Unlock previous bidder and Eco lock current one
		if self.waifuAuctionHouseEvent.user != None:
			ecoUnlock(self.waifuAuctionHouseEvent.user)
		ecoLock(ctx.message.author)

		self.waifuAuctionHouseEvent.user = ctx.message.author
		self.waifuAuctionHouseEvent.lastBid = bidAmount
		self.waifuAuctionHouseEvent.lastBidTime = t

		# Report to channel
		embed = discord.Embed(title="Bid Registered", description="{} made the latest bid!".format(ctx.message.author.name))
		embed.add_field(name="Bid Amount", value="{}".format(pMoney(bidAmount)))

		if extendedTime:
			newEndTime = timeNow() + datetime.timedelta(seconds=self.waifuAuctionHouseEvent.bidTimeExtension)
			tStr = "Auction will stop at {}.".format(newEndTime.strftime("%H:%M:%S"))
			embed.add_field(name="Time Extended!", value=tStr)

		await ctx.send("", embed=embed)

	@waifu.command(aliases=["fav"])
	async def favorite(self, ctx, favArg):
		code = setFavoriteWaifu(ctx.message.author, favArg)
		if code == 0:
			if favArg == "clear":
				endMsg = "cleared"
			else:
				endMsg = "set"
			await ctx.send("{}, your favorite waifu has been {}!".format(ctx.message.author.mention, endMsg))
		elif code == -1:
			await ctx.send("{}, you do not have this waifu in your waifu list.".format(ctx.message.author.mention))
		elif code == -2:
			await ctx.send("{}, I didn't understand that, see `>help waifu fav`.".format(ctx.message.author.mention))

	@waifu.command(aliases=["top"])
	async def ranking(self, ctx, rankArg=None):
		if rankArg == "me":
			rankingPos = getWaifuRankingPosition(ctx.message.author)
			rankingLength = getWaifuProfileCount()
			embed = discord.Embed(title="Waifu Ranking", description="You are in position {}/{}.".format(rankingPos, rankingLength))
			
			await ctx.send("", embed=embed)
		else:
			embed = discord.Embed(title="Waifu Ranking", description="Top 5 based on Total Waifu Value.")
			i = 1
			for waifuProfile in getWaifuRankingList()[:5]:
				fieldName = "{}/5: {}".format(i, waifuProfile["name"])
				fieldValue = "Total Value: {}, with {} waifus".format(waifuProfile["totalWaifuValue"], len(waifuProfile["waifuList"]))
				embed.add_field(name=fieldName, value=fieldValue, inline=False)
				i += 1

			await ctx.send("", embed=embed)

	@waifu.command(aliases=["fusion"])
	async def fuse(self, ctx, waifuID1: int, waifuID2: int, waifuID3: int):
		code = fuseWaifus(ctx.message.author, waifuID1, waifuID2, waifuID3)
		if code < 0:
			if code == -1:
				msg = "{}, One of the Waifu IDs you entered is not in your list.".format(ctx.message.author.mention)
			elif code == -2:
				msg = "{}, The 3 Waifus must have same rank.".format(ctx.message.author.mention)
			elif code == -3:
				msg = "{}, You can't fuse a SSS-ranked Waifu.".format(ctx.message.author.mention)

			await ctx.send(msg)
			return 0

		waifu = getWaifu(code)
		embed = discord.Embed(title="\U0001F9EC {}'s Waifu Fusion! \U0001F9EC".format(ctx.message.author.name), description="You got a {}-tier Waifu!".format(waifu["rank"]))

		infoValue1 = "Name: {}".format(waifu["name"])
		infoValue2 = ", alias {}".format(random.choice(waifu["aliases"])) if len(waifu["aliases"]) > 0 else ""
		infoValue3 = "From: {}".format(waifu["animeName"])
		embed.add_field(name="Basic Information", value=infoValue1+infoValue2+"\n"+infoValue3)
		
		statsValue1 = "Value: {}".format(waifu["value"])
		statsValue2 = "Ranking: {}/{}".format(waifu["ranking"], waifuCount())
		embed.add_field(name="Stats", value=statsValue1+"\n"+statsValue2)

		thumbnail_url = random.choice(waifu["pictures"])
		embed.set_thumbnail(url=thumbnail_url)

		await ctx.send("", embed=embed)
		return 0

	@waifu.command()
	async def summon(self, ctx):
		profile = getWaifuProfile(ctx.message.author)
		if dateNow() <= datetime.date.fromisoformat(profile["lastSummonDate"]):
			await ctx.send("{}, you can summon only once per day.".format(ctx.message.author.mention))
			return 0
		
		# Update last summon date
		mongoClient = dbClient.getClient()
		mongoClient.DBot.waifu.update_one({"id": ctx.message.author.id}, {"$set": {"lastSummonDate": dateNow().isoformat()}})

		# Get a summonable waifu and add it to the profile
		rank = getSummonRank()
		waifu = getRandomWaifuByRank(rank)
		addWaifu(ctx.message.author, waifu)

		embed = discord.Embed(title="\U00002728 {}'s Waifu Summon \U00002728".format(ctx.message.author), description="You summoned a {}-tier Waifu!".format(waifu["rank"]))

		infoValue1 = "Name: {}".format(waifu["name"])
		infoValue2 = ", alias {}".format(random.choice(waifu["aliases"])) if len(waifu["aliases"]) > 0 else ""
		infoValue3 = "From: {}".format(waifu["animeName"])
		embed.add_field(name="Basic Information", value=infoValue1+infoValue2+"\n"+infoValue3)
		
		statsValue1 = "Value: {}".format(waifu["value"])
		statsValue2 = "Ranking: {}/{}".format(waifu["ranking"], waifuCount())
		embed.add_field(name="Stats", value=statsValue1+"\n"+statsValue2)

		thumbnail_url = random.choice(waifu["pictures"])
		embed.set_thumbnail(url=thumbnail_url)

		await ctx.send("", embed=embed)
		return 0
