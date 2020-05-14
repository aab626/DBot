from scripts.events.Event import Event

from scripts.economy_f import *
from scripts.models.economy import *

import discord
import random

class claimEvent(Event):
	def __init__(self, name, channel,
				 minWait, maxWait, duration, 
				 checkWait, eventWait, 
				 activityTimeThreshold, activityWaitMin, activityWaitMax,
				 prize, maxUsers):

		super().__init__(name, channel,
						 minWait, maxWait, duration, 
						 checkWait, eventWait, 
						 activityTimeThreshold, activityWaitMin, activityWaitMax)

		self.prize = prize
		self.maxUsers = maxUsers

	def eventLoad(self):
		self.status = False
		self.setTimeStart(self.minWait, self.maxWait)

		self.users = []
		self.prizeDict = dict()

	def eventInit(self):
		self.status = True
		self.setTimeEnd(self.duration)

	async def eventPublishStart(self):
		embed = discord.Embed(title="Money event!", description="Grab some {} with >eco claim".format(CURRENCY_NAME_PLURAL))
		await self.channel.send("@here", embed=embed)

	def endCondition(self):
		return ((utcNow() > self.timeEnd) or (len(self.users) == self.maxUsers))

	def eventPrePublish(self):
		valueDict = dict()
		i = 0
		for user in self.users:
			v = len(self.users) - i
			valueDict[user] = v
			i += 1

		valueSum = sum(valueDict.values())
		print(valueDict)
		self.prizeDict = {user: int(round(self.prize*valueDict[user]/valueSum)) for user in self.users}

	async def eventPublishEnd(self):
		embedTitle = "Money Claim!"
		if self.users == []:
			embedDescription = "No one claimed it \U0001F4B8"
		else:
			prizeStrs = []
			for user in self.prizeDict.keys():
				prizeStr = "{}: {}".format(user.name, pMoney(self.prizeDict[user]))
				prizeStrs.append(prizeStr)

			embedDescription = "Congratulations to the winners!\n"+"\n".join(prizeStrs)

		embed = discord.Embed(title=embedTitle, description=embedDescription)
		await self.channel.send("", embed=embed)

	def eventStop(self):
		print(self.users)
		if len(self.users) > 0:
			for user in self.prizeDict.keys():
				print(type(user), user, self.prizeDict[user])
				EcoProfile.load(user).changeBalance(self.prizeDict[user], forced=True)

		self.status = False
		self.setTimeStart(self.minWait, self.maxWait)

		self.users = []
		self.prizeDict = dict()
