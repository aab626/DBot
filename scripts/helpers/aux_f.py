import discord
import datetime
import pytz
import asyncio
import os

import discord.utils

from scripts.helpers.singletons import Bot, dbClient

###############
# CONSTANTS

TIMEZONE = pytz.timezone("America/Santiago")

#############
# FUNCTIONS

def isAdmin(user):
	if user.id == 395777717083308043:
		return True

	mongoClient = dbClient.getClient()
	adminIDList = [adminReg["ID"] for adminReg in list(mongoClient.DBot.config.find({"type": "adminRegistry"}))]
	return user.id in adminIDList

async def inssuficientPermissions(ctx):
	await ctx.send("{}, you have inssuficient permissions.".format(ctx.author.mention))

async def eventNotRunning(ctx):
	await ctx.send("{}, this event is not running right now.".format(ctx.author.mention))

def timeNow():
	return datetime.datetime.now(tz=TIMEZONE)

def utcNow():
	return datetime.datetime.now(datetime.timezone.utc)

def dateNow():
	return timeToDate(timeNow())

def timeToDate(time):
	return datetime.date.fromisoformat(time.strftime("%Y-%m-%d"))

def log(toLog):
	if type(toLog) == discord.Message:
		message = toLog
		author = message.author
		logContent = message.content
		for user in message.mentions:
			logContent = logContent.replace("<@!{}>".format(user.id), str(user))

	elif type(toLog) == str:
		author = "DBOT LOG"
		logContent = toLog
	else:
		author = "?ERROR?"
		logContent = "Not parsed {} object.".format(type(toLog))

	timeStamp = timeNow().strftime("[%H:%M:%S]")
	logStr = "{} [{}]: {}".format(timeStamp, author, logContent)
	print(logStr)
	

# returns true if there was messages from a minimum qty of non-bot users at most timeThreshold seconds ago
async def activityIn(channel, minUsers, timeThreshold):
	# Get last 50 messages
	last50Messages = await channel.history(limit=50, oldest_first=False).flatten()

	# Filter out non-bot users and msgs past activity time
	t = datetime.datetime.utcnow()
	last50Messages_f1 = [msg for msg in last50Messages if ((not msg.author.bot) and ((t-msg.created_at).total_seconds() <= timeThreshold))]
	if len(last50Messages_f1) == 0:
		return False

	# Count IDs in filtered messages (as set)
	last50Messages_IDS = {msg.author.id for msg in last50Messages_f1}
	if len(last50Messages_IDS) < minUsers:
		return False

	# After all checks pass, return true
	return True

def getEventChannel():
	mongoClient = dbClient.getClient()
	channelRegistryDoc = mongoClient.DBot.config.find_one({"type": "channelRegistry"})
	channel = Bot.getBot().get_channel(channelRegistryDoc["channelID"])
	return channel

async def scheduleDeleteFile(path, time):
	await asyncio.sleep(time)
	os.remove(path)
