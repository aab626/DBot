import discord

from scripts._aux_f import *

from scripts.wargame_f import *

from scripts.economy_f import *

import asyncio
import datetime

##############
# CONSTANTS

# Wargame watcher event
WARGAME_EVENT_NAME = "wargameEvent"

# Daily Reserves Event
RESERVE_EVENT_NAME = "dailyReservesEvent"
DAILY_RESERVE_GAIN_PER_CAPITAL = 10
DAILY_RESERVE_GAIN_PER_NON_CAPITAL = 1

# Hourly CP Gain event
CP_EVENT_NAME = "hourlyCommandPointsEvent"
HOURLY_CP_GAIN_PER_CAPITAL = 1
HOURLY_CP_GAIN_PER_PRODUCER_POS = 1
MIN_FORCE_REQUIRED_TO_PRODUCE_HOURLY_CP = 5
NONPRODUCER_POS_NUMBER_TO_GAIN_CP = 3
CP_CAP_MULTIPLIER = 5
CP_CAP_POS_COUNT_TO_ADD = 2



####################
# EVENT FUNCTIONS

async def wargameEvent(bot, channel):
	log("EVENT LOAD: {} @ {}.".format(WARGAME_EVENT_NAME, channel))
	eventRunning = getEventDoc(WARGAME_EVENT_NAME)["active"]
	while eventRunning:
		# Wargame can keep running as long while any of the conditions below are met:
		# 1) There is more than 1 player alive, and the game end time hasnt been reached
		# 2) There is time for a player to register, and the game end time hasnt been reached
		t = timeNow()
		eventDoc = getEventDoc(WARGAME_EVENT_NAME)
		registerEndTime = datetime.datetime.fromtimestamp(eventDoc["registerEndTime"])
		gameEndTime = datetime.datetime.fromtimestamp(eventDoc["gameEndTime"])
		with dbClient() as client:
			playersLeft = client.DBot.wargamePlayers.count_documents({"isAlive": True})
		
		condition1 = (playersLeft > 1) and (t < gameEndTime)
		condition2 = (t < registerEndTime) and (t < gameEndTime)
		eventRunning = condition1 or condition2

		# Wait a minute between every event call
		asyncio.sleep(60)

	# When out-of-the-while loop, it means the wargame has ended
	# Change active status
	with dbClient() as client:
		client.DBot.events.update_one({"name": WARGAME_EVENT_NAME}, {"$set": {"active": False}})

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

	embedTitle = "The war has come to an end.."
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
	await channel.send("@here", embed=embed)

async def dailyReservesEvent(bot, channel):
	log("EVENT LOAD: {} @ {}.".format(RESERVE_EVENT_NAME, channel))
	eventDoc = {"name": RESERVE_EVENT_NAME,
				"category": "wargame",
				"lastDate": dateNow().isoformat()}

	with dbClient() as client:
		client.DBot.events.delete_many({"name": RESERVE_EVENT_NAME})
		client.DBot.events.insert_one(eventDoc)

	while True:
		# If the main wargame event is not active, reset and keep going
		wgEventDoc = getEventDoc(WARGAME_EVENT_NAME)
		if wgEventDoc is None:
			await asyncio.sleep(60)
			continue
		if not wgEventDoc["active"]:
			await asyncio.sleep(60)
			continue

		eventDoc = getEventDoc(RESERVE_EVENT_NAME)
		tDate = dateNow()
		tEvent = datetime.date.fromisoformat(eventDoc["lastDate"])
		# If it is a new day
		if tDate > tEvent:
			#Log
			log("EVENT START: {}".format(RESERVE_EVENT_NAME))

			# Get alive player list
			with dbClient() as client:
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
				reserveGain = DAILY_RESERVE_GAIN_PER_CAPITAL + len(connectedPositions)*DAILY_RESERVE_GAIN_PER_NON_CAPITAL
				addReserves(playerDoc["ID"], reserveGain)

			# When event finalices, replace event doc
			eventDoc["lastDate"] = dateNow().isoformat()
			replaceEventDoc(RESERVE_EVENT_NAME, eventDoc)

		# Check if a day has passed every 60 seconds
		await asyncio.sleep(60)

async def hourlyCommandPointsEvent(bot, channel):
	log("EVENT LOAD: {} @ {}.".format(CP_EVENT_NAME, channel))
	# Set up 1st start parameters
	eventDocument = {"name": CP_EVENT_NAME,
					 "category": "wargame",
					 "lastTime": timeNow().isoformat()}

	with dbClient() as client:
		client.DBot.events.delete_many({"name": CP_EVENT_NAME})
		client.DBot.events.insert_one(eventDocument)

	while True:
		# If the main wargame event is not active, reset and keep going
		wgEventDoc = getEventDoc(WARGAME_EVENT_NAME)
		if wgEventDoc is None:
			await asyncio.sleep(60)
			continue
		if not wgEventDoc["active"]:
			await asyncio.sleep(60)
			continue
		
		eventDoc = getEventDoc(CP_EVENT_NAME)
		t = timeNow()
		tEvent = datetime.datetime.fromisoformat(eventDoc["lastTime"])
		# If an hour has passed since last call
		if t.hour > tEvent.hour:
			# Log
			log("EVENT START: {}".format(CP_EVENT_NAME))

			# Get alive player list
			with dbClient() as client:
				playerDocList = list(client.DBot.wargamePlayers.find({"isAlive": True}))
			
			# For each alive player, update Command Point cap and add Command Points
			for playerDoc in playerDocList:
				with dbClient() as client:
					posList = list(client.DBot.wargameMap.find({"ownerID": playerDoc["ID"]}))

				# Update command points cap:
				# CP_CAP = BASE (50) + 5 for each 2 owned positions (capital does not count towards this)
				CP_cap = COMMAND_POINT_CAP_BASE + CP_CAP_MULTIPLIER*(len(posList)-1)//CP_CAP_POS_COUNT_TO_ADD
				with dbClient() as client:
					client.DBot.wargamePlayers.update_one({"ID": playerDoc["ID"]}, {"$set": {"commandPointsCap": CP_cap}})

				# Add command points
				# CP_GAIN: BASE (1) + 1 for each connected position to capital that has force >= 5
				#					+ 1 for every 3 connected positions that have force < 5
				connectedPositions = scanFillOwner(tuple(playerDoc["capital"]), playerDoc["ID"], [])
				if playerDoc["capital"] in connectedPositions:
					connectedPositions.remove(playerDoc["capital"])
				if tuple(playerDoc["capital"]) in connectedPositions:
					connectedPositions.remove(tuple(playerDoc["capital"]))
				
				CP_ProducerPositions = []
				CP_nonProducerPositions = []
				for pos in connectedPositions:
					if getPos(pos)["force"] >= MIN_FORCE_REQUIRED_TO_PRODUCE_HOURLY_CP:
						CP_ProducerPositions.append(pos)
					else:
						CP_nonProducerPositions.append(pos)

				CP_capitalGain = HOURLY_CP_GAIN_PER_CAPITAL
				CP_producerGain = HOURLY_CP_GAIN_PER_PRODUCER_POS*len(CP_ProducerPositions)
				CP_nonProducerGain = HOURLY_CP_GAIN_PER_PRODUCER_POS*len(CP_nonProducerPositions)//NONPRODUCER_POS_NUMBER_TO_GAIN_CP
				CPgain = CP_capitalGain + CP_producerGain + CP_nonProducerGain

				changeCommandPoints(playerDoc["ID"], CPgain)

			# When event finalices, replace the eventDoc
			eventDoc["lastTime"] = timeNow().isoformat()
			replaceEventDoc(CP_EVENT_NAME, eventDoc)

		# Check if an hour has passed every minute
		await asyncio.sleep(60)
