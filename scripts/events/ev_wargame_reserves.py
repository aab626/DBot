from scripts.events.Event import Event

from scripts.wargame_f import *
from scripts._aux_f import *

# DAILY_RESERVE_GAIN_PER_CAPITAL = 10
# DAILY_RESERVE_GAIN_PER_NON_CAPITAL= 1

class wargameReservesEvent(Event):
	def __init__(self, name, bot, channel,
				 minWait, maxWait, duration, 
				 checkWait, eventWait, 
				 activityTimeThreshold, activityWaitMin, activityWaitMax,
				 waitDays,
				 reservesPerCapital, reservesPerNonCapital):

		self.waitDays = waitDays
		self.reservesPerCapital = reservesPerCapital
		self.reservesPerNonCapital = reservesPerNonCapital

		super().__init__(name, bot, channel,
						 minWait, maxWait, duration, 
						 checkWait, eventWait, 
						 activityTimeThreshold, activityWaitMin, activityWaitMax)

	def eventLoad(self):
		self.timeStart = dateNow() + datetime.timedelta(days=self.waitDays)
		self.status = False
		self.stopEvent = True

	def startCondition(self):
		return wargameIsRunning() and (dateNow() > self.timeStart)

	def eventInit(self):
		self.status = True
		self.stopEvent = False

	async def eventPublishStart(self):
		pass

	def endCondition(self):
		return self.stopEvent

	async def eventProcess(self):
		# Get alive player list
		playerDocList = list(client.DBot.wargamePlayers.find({"isAlive": True}))

		# For each alive player, update Reserves
		for playerDoc in playerDocList:
			# Get number of owned positions connected to the playercapital
			connectedPositions = scanFillOwner(tuple(playerDoc["capital"]), playerDoc["ID"], [])
			if playerDoc["capital"] in connectedPositions:
				connectedPositions.remove(playerDoc["capital"])
			if tuple(playerDoc["capital"]) in connectedPositions:
				connectedPositions.remove(tuple(playerDoc["capital"]))

			# Update the reserves (daily)
			# where the gain is 10 per capital, and 1 per connected position 
			reserveGain = self.reservesPerCapital + len(connectedPositions)*self.reservesPerNonCapital
			addReserves(playerDoc["ID"], reserveGain)

		# Send signal to terminate event
		self.stopEvent = True

	async def eventPublishEnd(self):
		pass

	def eventStop(self):
		self.status = False
		self.stopEvent = True
		self.timeStart = dateNow() + datetime.timedelta(days=self.waitDays)
