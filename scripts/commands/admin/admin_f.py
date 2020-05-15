import datetime

from scripts.helpers.aux_f import isAdmin, timeNow
from scripts.helpers.singletons import dbClient, Bot, EventManager
from scripts.models.userprofile import UserProfile

async def shutdown_f(ctx):
	if not isAdmin(ctx.author):
		return -1

	await ctx.send("Oyasuminasai~")
	dbClient.getClient().close()
	await Bot.getBot().close()
	return 0

def addmoney_f(ctx, user, changeAmount):
	if not isAdmin(ctx.author):
		return -1
	else:
		UserProfile.load(user).ecoChangeBalance(changeAmount, forced=True)
		return 0

def event_list_f(ctx):
	if not isAdmin(ctx.author):
		return -1

	evManager = EventManager.getEventManager()
	eventList = evManager.getEventList()

	if len(eventList) == 0:
		msg = "{}, There are no registered Events.".format(ctx.author.mention)
	else:
		msg = "Registed Events:\n"+"\n".join(eventList)

	return msg

def event_info_f(ctx, eventName):
	if not isAdmin(ctx.author):
		return -1

	evManager = EventManager.getEventManager()
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

	return msg

def event_force_f(ctx, eventName, timeToExecution):
	if not isAdmin(ctx.author):
		return -1

	evManager = EventManager.getEventManager()
	event = evManager.getEvent(eventName)

	if event == -1:
		return -2
	else:
		timeStart = timeNow() + datetime.timedelta(seconds=timeToExecution)
		event.timeStart = timeStart
		msg = "{}, Event {} will start in {} seconds.".format(ctx.message.author.mention, event.name, timeToExecution)
		event.eventLog("Start Time: {}".format(event.timeStart))

	return msg

def channel_register_f(ctx):
	if not isAdmin(ctx.author):
		return -1

	mongoClient = dbClient.getClient()
	mongoClient.DBot.config.delete_many({"type": "channelRegistry"})
	channelRegDoc = {"type": "channelRegistry", "channelID": ctx.channel.id}
	mongoClient.DBot.config.insert_one(channelRegDoc)
	return 0

def channel_unregister_f(ctx):
	if not isAdmin(ctx.message.author):
		return -1

	mongoClient = dbClient.getClient()
	mongoClient.DBot.config.delete_one({"channelID": ctx.channel.id})
	return 0

def add_f(ctx, mentionedUser):
	if not isAdmin(ctx.author):
		return -1

	mongoClient = dbClient.getClient()
	adminDocCount = mongoClient.DBot.config.count_documents({"type": "adminRegistry", "ID": mentionedUser.id})
	if adminDocCount == 0:
		adminDoc = {"type": "adminRegistry", "ID": mentionedUser.id}
		mongoClient.DBot.config.insert_one(adminDoc)
		return 0
	else:
		return -2

def remove_f(ctx, mentionedUser):
	if not isAdmin(ctx.author):
		return -1

	mongoClient = dbClient.getClient()
	adminDocCount = mongoClient.DBot.config.count_documents({"type": "adminRegistry", "ID": mentionedUser.id})
	if adminDocCount > 0:
		mongoClient.DBot.config.delete_many({"type": "adminRegistry", "ID": mentionedUser.id})

	if adminDocCount > 0:
		return 0
	else:
		return -2
