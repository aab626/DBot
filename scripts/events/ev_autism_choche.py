# from scripts.events.Event import Event

# from scripts.autism_f import *
# from scripts.autism_fAux import *
# from scripts.economy_f import *

# from scripts.models.economy import *

import discord
import random

from scripts.events.Event import Event
from scripts.helpers.aux_f import utcNow
from scripts.models.userprofile import UserProfile
import scripts.autism_fAux as autism_fAux
import scripts.economy_fAux as economy_fAux

class chocheEvent(Event):
	def __init__(self, name, channel,
				 minWait, maxWait, duration, 
				 checkWait, eventWait, 
				 activityTimeThreshold, activityWaitMin, activityWaitMax,
				 minPrize, maxPrize):

		super().__init__(name, channel, 
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
		self.chochePhrase = autism_fAux.getChochePhrase()
		self.prize = random.randint(self.minPrize, self.maxPrize)
		self.setTimeEnd(self.duration)

	async def eventPublishStart(self):
		embed = discord.Embed(title="Hola yutuberos como tan toos..", description="Guess what choche is trying to say with `>choche <phrase>`!")
		embed.add_field(name="Choche says...", value=autism_fAux.getHiddenChochePhrase(self.chochePhrase))
		embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/481269182378409985.png")
		await self.channel.send("Hola yutuberos... @here", embed=embed)

	def endCondition(self):
		return ((utcNow() > self.timeEnd) or (self.winnerUser != None))

	async def eventPublishEnd(self):
		if self.winnerUser != None:
			embedDescription = "Congrats to {}! You won {}!".format(self.winnerUser.name, economy_fAux.pMoney(self.prize))
			embed = discord.Embed(title="Hola yutuberos como tan toos..", description=embedDescription)
		else:
			embed = discord.Embed(title="Hola yutuberos como tan toos..", description="No one guessed it.")

		await self.channel.send("", embed=embed)

	def eventStop(self):
		if self.winnerUser != None:
			UserProfile.load(self.winnerUser).ecoChangeBalance(self.prize, forced=True)

		self.status = False
		self.setTimeStart(self.minWait, self.maxWait)
		
		self.winnerUser = None
		self.chochePhrase = None
		self.prize = 0
