from scripts.events.Event import Event

from scripts.wargame_f import *
from scripts.economy_f import *
from scripts._aux_f import *

WARGAME_EVENTDOC_NAME = "wargameEvent"

class wargameReservesEvent(Event):
	def __init__(self, name, bot, channel,
				 minWait, maxWait, duration, 
				 checkWait, eventWait, 
				 activityTimeThreshold, activityWaitMin, activityWaitMax):

		super().__init__(name, bot, channel,
						 minWait, maxWait, duration, 
						 checkWait, eventWait, 
						 activityTimeThreshold, activityWaitMin, activityWaitMax)

	def eventLoad(self):
		self.status = False
		self.stopEvent = True
		self.continueWargame = True
		self.setTimeStart(self.minWait)

	def startCondition(self):
		return wargameIsRunning() and (timeNow() > self.timeStart)

	async def activityCondition(self):
		return True

	def eventInit(self):
		self.continueWargame = True
		self.stopEvent = False

	async def eventPublishStart(self):
		pass

	def endCondition(self):
		return self.stopEvent

	async def eventProcess(self):
		# Wargame can keep running as long while any of the conditions below are met:
		# 1) There is more than 1 player alive, and the game end time hasnt been reached
		# 2) There is time for a player to register, and the game end time hasnt been reached
		eventDoc = getEventDoc(WARGAME_EVENTDOC_NAME)
		registerEndTime = datetime.datetime.fromtimestamp(eventDoc["registerEndTime"])
		gameEndTime = datetime.datetime.fromtimestamp(eventDoc["gameEndTime"])

		with dbClient() as client:
			playersLeft = client.DBot.wargamePlayers.count_documents({"isAlive": True})
		
		condition1 = (playersLeft > 1) and (t < gameEndTime)
		condition2 = (t < registerEndTime) and (t < gameEndTime)
		self.continueWargame = condition1 or condition2

		# Send signal to terminate event
		self.stopEvent = True

	def eventPrePublish(self):
		# Change active status
		if not self.continueWargame:
			with dbClient() as client:
				client.DBot.events.update_one({"name": WARGAME_EVENTDOC_NAME}, {"$set": {"active": False}})

	async def eventPublishEnd(self):
		if not self.continueWargame:
			# report end to the channel and announce winners
			with dbClient() as client:
				humanPlayerList = list(client.DBot.wargamePlayers.find({"ID": {"$ne": -1}}))

			for playerDoc in humanPlayerList:
				with dbClient() as client:
					finalTerritories = list(client.DBot.wargameMap.find({"ownerID": playerDoc["ID"]}))
					finalTerritoryCount = len(finalTerritories)
					finalForceCombined = sum(territory["force"] for territory in finalTerritories)

					attacksWon = client.DBot.wargameBattles.count_documents({"$and": {"attackerID": playerDoc["ID"], "aftermath.attackWon": True}})
					defensesWon = client.DBot.wargameBattles.count_documents({"$and": {"defenderID": playerDoc["ID"], "aftermath.attackWon": True}})
					totalAttacks = client.DBot.wargameBattles.count_documents({"attackerID": playerDoc["ID"]})
					totalDefenses = client.DBot.wargameBattles.count_documents({"defenserID": playerDoc["ID"]})
					playersDefeated = client.DBot.wargameBattles.count_documents({"$and": {"attackerID": playerDoc["ID"], "aftermath.resultedInCapitulation": True}})

				finalScore = 1*attacksWon + 0.5*defensesWon + 10*playersDefeated

				playerDoc["finalTerritoryCount"] = finalTerritoryCount
				playerDoc["finalForceCombined"] = finalForceCombined
				playerDoc["attacksWon"] = attacksWon
				playerDoc["defensesWon"] = defensesWon
				playerDoc["playersDefeated"] = playersDefeated
				playerDoc["totalAttacks"] = totalAttacks
				playerDoc["totalDefenses"] = totalDefenses
				playerDoc["finalScore"] = round(finalScore, 1)

			# Sort order : finalScore > registerTime
			humanPlayerList.sort(key=lambda playerDoc: playerDoc["registerTime"])
			humanPlayerList.sort(key=lambda playerDoc: playerDoc["finalScore"], reverse=True)

			embedTitle = "The war has come to an end..."
			embedDescription = "Congratulations to {}! Winner of the war!".format(humanPlayerList[0]["name"])
			embed = discord.Embed(title=embedTitle, description=embedDescription)

			# For every player, report in embed
			for playerDoc in humanPlayerList:
				position = humanPlayerList.index(playerDoc)+1
				aliveRewardFactor = 1 if playerDoc["isAlive"] else 0.5
				positionRewardFactor = 1 if position in [1,2,3] else 0.5
				positionReward = 30 if position == 1 else 20 if position == 2 else 10 if position == 3 else 0
				reward = positionReward + int(playerDoc["finalScore"]*aliveRewardFactor*positionRewardFactor)

				aliveEmojiStr = "\U00002705" if playerDoc["isAlive"] else "\U0000274C"
				winnerEmojiStr = "\U0001F3C6" if position == 1 else "\U0001F948" if position == 2 else "\U0001F949" if position == 3 else ""
				fieldName = "{}/{}: {} {}{}".format(position, len(humanPlayerList), playerDoc["name"], winnerEmojiStr, aliveEmojiStr)

				fieldValue1 = "Final Territories: {}\nFinal Total Force: {}".format(playerDoc["finalTerritoryCount"],
																					playerDoc["finalForceCombined"])
				fieldValue2 = "Attacks Won: {}/{}\nDefenses Won: {}/{}\nPlayers Defeated: {}".format(playerDoc["attacksWon"], playerDoc["totalAttacks"],
																									 playerDoc["defensesWon"], playerDoc["totalDefenses"],
																									 playerDoc["playersDefeated"])
				fieldValue3 = "War Spoils : {}".format(pMoney(reward))
				fieldValue = fieldValue1+"\n"+fieldValue2+"\n"+fieldValue3

				# Add rewards
				if reward > 0:
					changeBalance(bot.get_user(playerDoc["ID"]), reward)

				embed.add_field(fieldName, fieldValue, inline=False)

			# Send final embed
			await self.channel.send("@here", embed=embed)

	def eventStop(self):
		self.eventDoc = None
		self.stopEvent = True
		self.continueWargame = True
		self.setTimeStart(self.minWait)
