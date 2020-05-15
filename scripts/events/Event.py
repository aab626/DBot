import asyncio
import datetime
import random

from scripts.helpers.aux_f import TIMEZONE, activityIn, log, utcNow
from scripts.helpers.singletons import Bot, EventManager


class Event:
	def __init__(self, name, channel, 
				 minWait, maxWait, duration, 
				 checkWait, eventWait, 
				 activityTimeThreshold, activityWaitMin, activityWaitMax):
		
		self.name = name
		self.status = False
		self.bot = Bot.getBot()

		self.channel = channel

		self.minWait = minWait
		self.maxWait = maxWait
		self.duration = duration

		self.checkWait = checkWait
		self.eventWait = eventWait

		self.activityTimeThreshold = activityTimeThreshold
		self.activityWaitMin = activityWaitMin
		self.activityWaitMax = activityWaitMax

		self.timeStart = utcNow()
		self.timeEnd = utcNow()

		self.eventLog("Instantiated")

		evManager = EventManager.getEventManager()
		evManager.registerEvent(self)
		self.eventLog("Registered in EventManager")

	# Starts the event loop by creating a task in the bot event loop
	# Should not be overriden.
	def startLoop(self):
		self.eventLog("Creating loop task")
		self.bot.loop.create_task(self.loop())

	# Event loop
	# Should not be overriden.
	async def loop(self):
		# Pre-loop event init
		self.eventLog("LOAD Phase")
		self.eventLoad()
		self.eventLog("Start Time: {} [{}]".format(self.timeStart, self.timeStart.replace(tzinfo=TIMEZONE).strftime("%H:%M:%S")))
		# Wait-for-event loop
		while True:
			# If there is a condition valid for start, check activity
			if self.startCondition():
				self.eventLog("startCondition PASSED")
				# If there wasnt enough activity for start, delay event start
				if not await self.activityCondition():
					self.eventLog("activityCondition FAILED")
					self.setTimeStart(self.activityWaitMin, self.activityWaitMax)
					continue

				self.eventLog("activityCondition PASSED")
				# If there is sufficient activity for start, start event
				# Pre-event initialization and publish
				self.eventLog("INIT Phase")
				self.eventInit()
				self.eventLog("End Time: {} [{}]".format(self.timeEnd, self.timeEnd.replace(tzinfo=TIMEZONE).strftime("%H:%M:%S")))

				self.eventLog("Publishing START")
				await self.eventPublishStart()

				# Main Event loop
				self.eventLog("Entering Main event-loop")
				while not self.endCondition():
					# Event process during main event loop
					await self.eventProcess()

					# Event while sleeper
					await asyncio.sleep(self.eventWait)

				# Post-event status update and publish
				self.eventLog("PREPUBLISH Phase ")
				self.eventPrePublish()

				self.eventLog("Publishing END")
				await self.eventPublishEnd()

				self.eventLog("STOP Phase")
				self.eventStop()
				self.eventLog("Start Time: {} [{}]".format(self.timeStart, self.timeStart.replace(tzinfo=TIMEZONE).strftime("%H:%M:%S")))

			else:
				self.eventLog("startCondition FAILED")

			# Wait-for-event while sleeper
			self.eventLog("Sleep: checkWait ({})".format(self.checkWait))
			await asyncio.sleep(self.checkWait)

	#####################
	# MAIN LOOP METHODS

	# Sets the base variables for the event.
	# Variables should be instance variables.
	# Can be overriden
	def eventLoad(self):
		pass

	# Sets the main condition for the event to start
	# Defaults to t > start time
	# Can be overriden:
	#	true : start event
	#	false: dont start event, delay until checkWait seconds
	def startCondition(self):
		return utcNow() > self.timeStart

	# Sets the activity needed as a condition for the event to start
	# Defaults to check:
	#	in the last 50 messages, there was at least 2 users ta
	# Can (should) be overriden: (SHOULD BE AWAITED)
	#	true : start event
	#	false: dont start event, change start time with given parameters
	async def activityCondition(self):
		return await activityIn(self.channel, minUsers=1, timeThreshold=self.activityTimeThreshold)

	# Sets variables for the event when it started, such as prizes or conditions to win
	# Variables should be instance variables.
	# SHOULD be overriden.
	def eventInit(self):
		pass

	# Sends a message to the channel when the event starts
	# SHOULD be overriden. (SHOULD BE AWAITED)
	async def eventPublishStart(self):
		print("event started")

	# Sets the condition for the event to end, when it is started
	# Defaults to t > end time
	# Can be overriden:
	#	true : stop the event
	#	false: continue the event
	def endCondition(self):
		return utcNow() > self.timeEnd

	# Main process method when the event is running
	# Can be overriden.
	async def eventProcess(self):
		pass

	# Process method to calculate stuff after the event has ended
	# but before publishing the end.
	# Can be overriden.
	def eventPrePublish(self):
		pass

	# Sends a message to the channel when the event stops
	# SHOULD be overriden. (SHOULD BE AWAITED)
	async def eventPublishEnd(self):
		print("event ended")

	# Process method used when the event stops.
	# Defaults to update the start time and set status.
	# Should be overriden to clean event variables and assign prizes.
	def eventStop(self):
		self.setTimeStart(self.minWait, self.maxWait)
		self.status = False

	###########################
	# HELPER (AUX) FUNCTIONS

	# Helper functions to update the start time of the event
	# Should not be overriden.
	def setTimeStart(self, *args):
		if len(args) == 1:
			waitTime = args[0]
		elif len(args) > 1:
			waitTime = random.randint(args[0], args[1])
		else:
			waitTime = 0
			print("ERROR: call to setTimeStart with no arguments")

		self.timeStart = utcNow() + datetime.timedelta(seconds=waitTime)

	# Helper functions to update the end time of the event
	# Should not be overriden.
	def setTimeEnd(self, *args):
		if len(args) == 1:
			duration = args[0]
		elif len(args) > 1:
			duration = random.randint(args[0], args[1])
		else:
			duration = 0
			print("ERROR: call to setTimeEnd with no arguments.")

		self.timeEnd = utcNow() + datetime.timedelta(seconds=duration)

	# Getter for self.status
	# Returns true if the event is running, false otherwise
	def isRunning(self):
		return self.status

	# Event logger
	def eventLog(self, logMsg):
		log("Event {} | {}".format(self.name, logMsg))
