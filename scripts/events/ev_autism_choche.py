from scripts.events.Event import Event

from scripts.economy_f import *
from scripts.autism_f import *

import discord

class chocheEvent(Event):
	def __init__(self, name, bot, channel,
				 minWait, maxWait, duration, 
				 checkWait, eventWait, 
				 activityTimeThreshold, activityWaitMin, activityWaitMax,
				 minPrize, maxPrize):

		super().__init__(name, bot, channel, 
						 minWait, maxWait, duration, 
						 checkWait, eventWait, 
						 activityTimeThreshold, activityWaitMin, activityWaitMax)

		self.minPrize = minPrize
		self.maxPrize = maxPrize

	def eventLoad(self):
		self.status = False
		self.setTimeStart(self.minWait, self.maxWait)

		self.winnerUser = None
		self.chochePhrase = None
		self.prize = 0

	def eventInit(self):
		self.status = True
		self.chochePhrase = getChochePhrase()
		self.prize = random.randint(self.minPrize, self.maxPrize)
		self.setTimeEnd(self.duration)

	async def eventPublishStart(self):
		embed = discord.Embed(title="Hola yutuberos como tan toos..", description="Guess what choche is trying to say with `>choche <phrase>`!")
		embed.add_field(name="Choche says...", value=getHiddenChochePhrase(self.chochePhrase))
		embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/481269182378409985.png")
		await self.channel.send("Hola yutuberos... @here", embed=embed)

	def endCondition(self):
		return ((timeNow() > self.timeEnd) or (self.winnerUser != None))

	async def eventPublishEnd(self):
		if self.winnerUser != None:
			embedDescription = "Congrats to {}! You won {}!".format(self.winnerUser.name, pMoney(self.prize))
			embed = discord.Embed(title="Hola yutuberos como tan toos..", description=embedDescription)
		else:
			embed = discord.Embed(title="Hola yutuberos como tan toos..", description="No one guessed it.")

		await self.channel.send("", embed=embed)

	def eventStop(self):
		if self.winnerUser != None:
			getEconomyProfile(self.winnerUser)
			changeBalance(self.winnerUser, self.prize)

		self.status = False
		self.setTimeStart(self.minWait, self.maxWait)
		
		self.winnerUser = None
		self.chochePhrase = None
		self.prize = 0
