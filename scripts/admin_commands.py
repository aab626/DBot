import discord
import discord.utils
from discord.ext import commands

from scripts.economy_f import *
from scripts.helpers.aux_f import *
from scripts.helpers.dbClient import *
from scripts.helpers.eventManager import *

import datetime
import pprint

####################################################
# ADMIN COG

class Admin(commands.Cog):
	def __init__(self, bot, eventChannel):
		self.bot = bot
		self.eventChannel = eventChannel

	@commands.group()
	async def admin(self, ctx):
		pass

	@admin.command(aliases=["oyasumi", "oyasuminasai"])
	async def shutdown(self, ctx):
		if not isAdmin(ctx.message.author):
			await ctx.send("{}, you have inssuficient permissions.".format(ctx.message.author.mention))
			return 0

		await ctx.send("Oyasuminasai~")
		dbClient.getClient().close()
		await self.bot.close()

	@admin.command()
	async def addmoney(self, ctx, mentionedUser: discord.User, changeAmount: int):
		if not isAdmin(ctx.message.author):
			await ctx.send("{}, you have inssuficient permissions.".format(ctx.message.author.mention))
			return 0

		changeBalance(mentionedUser, changeAmount)
		await ctx.send("{}, {} balance was changed by {}.".format(ctx.message.author.mention,
																	mentionedUser.mention,
																	pMoney(changeAmount)))

	@admin.group()
	async def event(self, ctx):
		pass

	@event.command()
	async def list(self, ctx):
		if not isAdmin(ctx.message.author):
			await ctx.send("{}, you have inssuficient permissions.".format(ctx.message.author.mention))
			return 0

		evManager = eventManager.getEventManager()
		eventList = evManager.getEventList()

		if len(eventList) == 0:
			msg = "{}, There are no registered Events.".format(ctx.message.author.mention)
		else:
			msg = "Registed Events:\n"+"\n".join(eventList)

		channel = await ctx.author.create_dm()
		await channel.send(msg)
		return 0

	@event.command()
	async def info(self, ctx, eventName: str):
		if not isAdmin(ctx.message.author):
			await ctx.send("{}, you have inssuficient permissions.".format(ctx.message.author.mention))
			return 0

		evManager = eventManager.getEventManager()
		event = evManager.getEvent(eventName)

		if event == -1:
			msg = "{}, This event is not registered.".format(ctx.message.author.mention)
		else:
			evLine1 = "Event Information"
			evLine2 = "Name: {}".format(event.name)
			evLine3 = "Status: {}".format(event.status)
			evLine4 = "Start: {}".format(event.timeStart)
			evLine5 = "Duration: {}".format(event.duration)
			evLine6 = "Min. Wait: {}".format(event.minWait)
			evLine7 = "Max. Wait: {}".format(event.maxWait)
			evLines = [evLine1, evLine2, evLine3, evLine4, evLine5, evLine6, evLine7]
			msg = "\n".join(evLines)

		channel = await ctx.author.create_dm()
		await channel.send(msg)
		return 0

	@event.command()
	async def force(self, ctx, eventName: str, timeToExecution: int):
		if not isAdmin(ctx.message.author):
			await ctx.send("{}, you have inssuficient permissions.".format(ctx.message.author.mention))
			return 0

		evManager = eventManager.getEventManager()
		event = evManager.getEvent(eventName)

		if event == -1:
			msg = "{}, This event is not registered.".format(ctx.message.author.mention)
		else:
			timeStart = timeNow() + datetime.timedelta(seconds=timeToExecution)
			event.timeStart = timeStart
			msg = "{}, Event {} will start in {} seconds.".format(ctx.message.author.mention, event.name, timeToExecution)
			event.eventLog("Start Time: {}".format(event.timeStart))

		await ctx.send(msg)
		return 0

	@admin.group()
	async def channel(self, ctx):
		pass

	@channel.command()
	async def register(self, ctx):
		if not isAdmin(ctx.message.author):
			await ctx.send("{}, you have inssuficient permissions.".format(ctx.message.author.mention))
			return 0

		mongoClient = dbClient.getClient()
		mongoClient.DBot.config.delete_many({"type": "channelRegistry"})
		channelRegDoc = {"type": "channelRegistry", "channelID": ctx.channel.id}
		mongoClient.DBot.config.insert_one(channelRegDoc)

		await ctx.send("{}, channel registered successfully.".format(ctx.message.author.mention))
		return 0

	@channel.command()
	async def unregister(self, ctx):
		if not isAdmin(ctx.message.author):
			await ctx.send("{}, you have inssuficient permissions.".format(ctx.message.author.mention))
			return 0

		mongoClient = dbClient.getClient()
		mongoClient.DBot.config.delete_one({"channelID": ctx.channel.id})

		await ctx.send("{}, channel unregistered successfully.".format(ctx.message.author.mention))
		return 0

	@admin.command()
	async def add(self, ctx, userMentioned: discord.User):
		if not isAdmin(ctx.message.author):
			await ctx.send("{}, you have inssuficient permissions.".format(ctx.message.author.mention))
			return 0

		mongoClient = dbClient.getClient()
		adminDocCount = mongoClient.DBot.config.count_documents({"type": "adminRegistry", "ID": userMentioned.id})
		if adminDocCount == 0:
			adminDoc = {"type": "adminRegistry", "ID": userMentioned.id}
			mongoClient.DBot.config.insert_one(adminDoc)
			msg = "{}, {} has been added as a DBot Administrator.".format(ctx.message.author.mention, userMentioned.mention)
		else:
			msg = "{}, this user already has DBot Admin privileges".format(ctx.message.author.mention)

		await ctx.send(msg)
		return 0

	@admin.command()
	async def remove(self, ctx, userMentioned: discord.User):
		if not isAdmin(ctx.message.author):
			await ctx.send("{}, you have inssuficient permissions.".format(ctx.message.author.mention))
			return 0

		mongoClient = dbClient.getClient()
		adminDocCount = mongoClient.DBot.config.count_documents({"type": "adminRegistry", "ID": userMentioned.id})
		if adminDocCount > 0:
			mongoClient.DBot.config.delete_many({"type": "adminRegistry", "ID": userMentioned.id})

		if adminDocCount > 0:
			msg = "{}, {} DBot Admin privileges have been revoked.".format(ctx.message.author.mention, userMentioned.mention)
		else:
			msg = "{}, user was not found amont DBot Administrators".format(ctx.message.author.mention)

		await ctx.send(msg)
		return 0
