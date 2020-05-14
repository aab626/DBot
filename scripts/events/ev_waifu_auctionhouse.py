from scripts.events.Event import Event

from scripts.models.economy import *
from scripts.models.waifu import *

from scripts.waifu_fAux import *
from scripts.economy_fAux import *

import discord
import random

class waifuAuctionHouseEvent(Event):
	def __init__(self, name, channel,
				 minWait, maxWait, duration, 
				 checkWait, eventWait, 
				 activityTimeThreshold, activityWaitMin, activityWaitMax,
				 timeThresholdToExtend, bidTimeExtension):

		super().__init__(name, channel, 
						 minWait, maxWait, duration, 
						 checkWait, eventWait, 
						 activityTimeThreshold, activityWaitMin, activityWaitMax)

		self.timeThresholdToExtend = timeThresholdToExtend
		self.bidTimeExtension = bidTimeExtension

	def eventLoad(self):
		self.status = False
		self.setTimeStart(self.minWait, self.maxWait)

		self.waifu = None
		self.startingBid = 0
		self.buyoutPrize = 0
		self.bidStepUp = 1

		self.user = None
		self.lastBid = 0
		self.lastBidTime = None
		self.lastBidTimeChecked = None

	def eventInit(self):
		self.status = True
		self.setTimeEnd(self.duration)

		self.waifu = getRandomWaifu()
		self.startingBid = max(1, int(self.waifu["value"]*random.uniform(0.65, 0.95)))
		self.buyoutPrize = random.randint(int(3.5*self.waifu["value"]), int(5*self.waifu["value"]))
		self.bidStepUp = max(1, int((self.lastBid/self.waifu["value"]))**2)

		self.user = None
		self.lastBid = self.startingBid
		self.lastBidTime = utcNow()
		self.lastBidTimeChecked = self.lastBidTime

	async def eventPublishStart(self):
		embedDescription = "A {}-tiered waifu is being auctioned!".format("special" if self.waifu["rank"] in ["S", "SS", "SSS"] else "regular")
		embed = discord.Embed(title=self.waifu["name"], description=embedDescription, url=self.waifu["MAL_data"]["charURL"])
		embed.set_author(name="Waifu AuctionHouse Event!")
		embed.set_thumbnail(url=random.choice(self.waifu["pictures"]))

		if len(self.waifu["aliases"]) > 0:
			nameValueStr = "{}, alias {}".format(self.waifu["name"], random.choice(self.waifu["aliases"]))
		else:
			nameValueStr = self.waifu["name"]

		embed.add_field(name="Basic Information", value="{}\nFrom: {}".format(nameValueStr, self.waifu["animeName"]), inline=True)
		embed.add_field(name="Stats", value="Rank: {}\nRanking: {}/{}".format(self.waifu["rank"], self.waifu["ranking"], waifuCount(), inline=True))

		auctionStr1 = "Value: {}".format(self.waifu["value"])
		auctionStr2 = "Min. Bid: {}".format(self.startingBid+1)
		auctionStr3 = "Buyout Prize: {}".format(self.buyoutPrize)
		auctionStr4 = "Auction End: {}".format(self.timeEnd.replace(tzinfo=TIMEZONE).strftime("%H:%M:%S"))
		auctionLines = [auctionStr1, auctionStr2, auctionStr3, auctionStr4]
		embed.add_field(name="Auction", value="\n".join(auctionLines), inline=False)

		embed.set_footer(text="You can bid using >waifu bid <N>")
		await self.channel.send("@here", embed=embed)

	def endCondition(self):
		return ((utcNow() > self.timeEnd) or (self.lastBid >= self.buyoutPrize))

	async def eventProcess(self):
		if self.lastBidTime != self.lastBidTimeChecked:
			if (self.timeEnd - utcNow()).total_seconds() < self.timeThresholdToExtend:
				self.setTimeEnd(self.bidTimeExtension)
				self.lastBidTimeChecked = self.lastBidTime

		if self.lastBid > 0:
			newStepUp = max(1, int((self.lastBid/self.waifu["value"]))**2)
			if newStepUp > self.bidStepUp:
				self.bidStepUp = newStepUp
				embed = discord.Embed(title="Waifu AH Bid STEP UP!", description="New minimum bid Step-Up: {}".format(pMoney(self.bidStepUp)))
				await self.channel.send("", embed=embed)

	async def eventPublishEnd(self):
		embedTitle = "Waifu AuctionHouse Event!"
		if self.user == None:
			embed = discord.Embed(title=embedTitle, description="No one bidded for her \U0001F494")
		else:
			embed = discord.Embed(title=embedTitle, description="{} got {}! Congrats \U0001F496".format(self.user.name, self.waifu["name"]))
			embed.add_field(name="Bidding", value="{} ({}% of Waifu Value)".format(pMoney(self.lastBid), int(round(self.lastBid/self.waifu["value"]*100, 1))))
		
		embed.set_thumbnail(url=random.choice(self.waifu["pictures"]))
		await self.channel.send("", embed=embed)

	def eventStop(self):
		if self.user != None:
			EcoProfile.load(self.user).changeBalance(-self.lastBid)
			WaifuProfile.load(self.user).addWaifu(self.waifu)

		self.status = False
		self.setTimeStart(self.minWait, self.maxWait)

		self.waifu = None
		self.startingBid = 0
		self.buyoutPrize = 0
		self.bidStepUp = 1

		self.user = None
		self.lastBid = 0
		self.lastBidTime = None
		self.lastBidTimeChecked = None
