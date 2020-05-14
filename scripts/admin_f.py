from scripts.economy_f import *
from scripts.helpers.aux_f import *
from scripts.helpers.dbClient import *
from scripts.helpers.EventManager import *
from scripts.helpers.Bot import *
from scripts.models.economy import *

async def shutdown_f(ctx):
	if not isAdmin(ctx.author):
		return -1

	await ctx.send("Oyasuminasai~")
	dbClient.getClient().close()
	await Bot.getBot().close()
	return 0

def admin_addmoney(ctx, user, changeAmount):
	if not isAdmin(ctx.author):
		return -1
	else:
		EcoProfile.load(user).changeBalance(changeAmount, forced=True)
		return 0

def admin_event_list(ctx):
	if not isAdmin(ctx.author):
		return -1

	evManager = EventManager.getEventManager()
	eventList = evManager.getEventList()

	if len(eventList) == 0:
		msg = "{}, There are no registered Events.".format(ctx.author.mention)
	else:
		msg = "Registed Events:\n"+"\n".join(eventList)

	return msg

def admin_event_info(ctx, eventName):
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

def admin_event_force(ctx, eventName, timeToExecution):
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

def admin_channel_register(ctx):
	if not isAdmin(ctx.author):
		return -1

	mongoClient = dbClient.getClient()
	mongoClient.DBot.config.delete_many({"type": "channelRegistry"})
	channelRegDoc = {"type": "channelRegistry", "channelID": ctx.channel.id}
	mongoClient.DBot.config.insert_one(channelRegDoc)
	return 0

def admin_channel_unregister(ctx):
	if not isAdmin(ctx.message.author):
		return -1

	mongoClient = dbClient.getClient()
	mongoClient.DBot.config.delete_one({"channelID": ctx.channel.id})
	return 0

def admin_add(ctx, mentionedUser):
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

def admin_remove(ctx, mentionedUser):
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
