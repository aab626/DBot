# import discord
# import discord.utils
# from discord.ext import commands

# from scripts._aux_f import *

# from scripts.wargame_f import *
# from scripts.wargame_events import *

# import scripts.waifu_f as waifu_f

# import random
# import datetime

##############
# CONSTANTS

####################################################
# WARGAME COG

class Wargame(commands.Cog):
	def __init__(self, bot, eventChannel, dbClient):
		self.bot = bot
		self.eventChannel = eventChannel
		self.dbClient = dbClient

		# Add the events to the bot's event loop
		#self.bot.loop.create_task(hourlyCommandPointsEvent(self.bot, eventChannel))
		#self.bot.loop.create_task(dailyReservesEvent(self.bot, eventChannel))

	###############
	# WARGAME COMMANDS

	@commands.group(aliases=["war"])
	async def wargame(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("{}, Invalid command\nuse `>help wargame` instead".format(ctx.message.author.mention))

	@wargame.command(aliases=["delete"])
	async def reset(self, ctx):
		if not isAdmin(ctx.message.author):
			await ctx.send("{}, you have insufficient permissions.".format(ctx.message.author.mention))
			return 0
		else:
			deletewarGame()
			await ctx.send("{}, wargame has been reset".format(ctx.message.author.mention))

	# Prematurely stops a ongoing wargame
	@wargame.command()
	async def stop(self, ctx):
		if not isAdmin(ctx.message.author):
			await ctx.send("{}, you have insufficient permissions.".format(ctx.message.author.mention))
			return 0

		if not getEventDoc("wargameEvent")["active"]:
			await ctx.send("{}, this event is not active now.".format(ctx.message.author.mention))
			return 0

		with dbClient() as client:
			t = timeNow()
			client.DBot.events.update_one({"name": "wargameEvent"}, {"$set": {"gameEndTime": t.isoformat()}})
		await ctx.send("{}, Wargame has been stopped".format(ctx.message.author.mention))
		return 0

	@wargame.command(aliases=["new", "newmap"])
	async def start(self, ctx):
		if not isAdmin(ctx.message.author):
			await ctx.send("{}, you have insufficient permissions.".format(ctx.message.author.mention))
			return 0
		else:
			startWargame()
			await ctx.send("{}, A new wargame map has just been created.".format(ctx.message.author.mention))
			return 0

	@wargame.command()
	async def map(self, ctx):
		fullMap_path = askForFullMap(ctx.message.author)
		await ctx.send("", file=discord.File(fullMap_path))
		deleteMap(fullMap_path)

	@wargame.command()
	async def colors(self, ctx):
		selectableColors = [color for color in colorData.keys() if colorData[color]["selectable"]]

		embed = discord.Embed(title="DBot Wargame", description="Player color keys:\n"+"\n".join(selectableColors))
		await ctx.send("", embed=embed)

	@wargame.command(aliases=["reg"])
	async def register(self, ctx, pTag: str, pColorName: str):
		if timeNow() > getWargameTimes()["registerEndTime"]:
			await ctx.send("{}, registration time is over.".format(ctx.message.author.mention))
			return 0

		pID = ctx.message.author.id
		pName = ctx.message.author.name
		code = registerPlayer(pID, pName, pTag, pColorName)
		if code == 0:
			msg = "{}, you have been succesfully registered.".format(ctx.message.author.mention)
		elif code == -1:
			msg = "{}, a player with this user ID is already registered.".format(ctx.message.author.mention)
		elif code == -2:
			msg = "{}, a player with this tag is already registered.".format(ctx.message.author.mention)
		elif code == -3:
			msg = "{}, there are no available positions to spawn your capital now.\nTry again in the next game!".format(ctx.message.author.mention)
		elif code == -4:
			msg = "{}, the tag must be an alphanumerical string of length 1-3 characters.".format(ctx.message.author.mention)
		elif code == -5:
			msg = "{}, the tag can only have alphanumerical characters.".format(ctx.message.author.mention)
		elif code == -6:
			msg = "{}, this color is not registered, check `>wargame colors`.".format(ctx.message.author.mention)

		await ctx.send(msg)

	@wargame.command(aliases=["summary"])
	async def info(self, ctx):
		gameInfo = queryGameInfo()

		playerFields = []
		for playerInfo in gameInfo["players"]:
			if playerInfo["name"] == "NPC":
				continue

			tagStr = " "*abs(3-len(playerInfo["tag"]))+playerInfo["tag"]
			nameStr = playerInfo["name"][:12]

			fieldName = "[{}] {}".format(tagStr, nameStr)
			fieldValue = "[{}] Territories: {} ({}%)".format(playerInfo["color"], playerInfo["territories"], playerInfo["territoryPercent"])
			playerFields.append((fieldName, fieldValue))

		embed = discord.Embed(title="DBot Wargame Summary", description=discord.Embed.Empty)
		for pField in playerFields:
			embed.add_field(name=pField[0], value=pField[1], inline=False)

		npcInfo = [pInfo for pInfo in gameInfo["players"] if pInfo["name"] == "NPC"][0]
		embed.add_field(name="Unclaimed Areas", value="{} ({}%)".format(npcInfo["territories"], npcInfo["territoryPercent"]), inline=False)

		await ctx.send("", embed=embed)

	@wargame.command(aliases=["atk"])
	async def attack(self, ctx, originPosIndex: str, attackForce: int, destinationPosIndex: str):
		# Check if user is playing
		if not isUserPlaying(ctx.message.author.id):
			await ctx.send("{}, you are not currently playing.".format(ctx.message.author.mention))
			return 0

		# Parse origin position
		originPos = posIndexToCoord(originPosIndex)
		if type(originPos) == int:
			if originPos == -1:
				msg = "{}, Origin Position can only be refered using letters and digits.".format(ctx.message.author.mention)
			elif originPos == -2:
				msg = "{}, The Origin Position can have at most 2 digits.".format(ctx.message.author.mention)
			elif originPos == -3:
				msg = "{}, The Origin Position can have at most 1 letter.".format(ctx.message.author.mention)
			elif originPos == -4:
				msg = "{}, The entered Origin Position its outside the map.".format(ctx.message.author.mention)

			await ctx.send(msg)
			return 0

		# Parse destination position
		destinationPos = posIndexToCoord(destinationPosIndex)
		if type(originPos) == int:
			if originPos == -1:
				msg = "{}, Destination Position can only be refered using letters and digits.".format(ctx.message.author.mention)
			elif originPos == -2:
				msg = "{}, The Destination Position can have at most 2 digits.".format(ctx.message.author.mention)
			elif originPos == -3:
				msg = "{}, The Destination Position can have at most 1 letter.".format(ctx.message.author.mention)
			elif originPos == -4:
				msg = "{}, The entered Destination Position its outside the map.".format(ctx.message.author.mention)

			await ctx.send(msg)
			return 0

		attackerID = ctx.message.author.id
		attackReportCode = resolveAttack(attackerID, originPos, destinationPos, attackForce)

		# Check if there was an error during attack
		if attackReportCode < 0:
			msg = "{}, There was an unknown error during the Attack Phase.\nPlease contact an Administrator".format(ctx.message.author.mention)
			if attackReportCode == -1:
				msg = "{}, There was an error during the Attack Phase on the Origin Position\nPlease contact an Administrator".format(ctx.message.author.mention)
			elif attackReportCode == -2:
				msg = "{}, There was an error during the Attack Phase on the Destination Position\nPlease contact an Administrator".format(ctx.message.author.mention)
			elif attackReportCode == -3:
				msg = "{}, You are not the owner of this position.".format(ctx.message.author.mention)
			elif attackReportCode == -4:
				msg = "{}, You do not have enough Force in this position make this attack.".format(ctx.message.author.mention)
			elif attackReportCode == -5:
				msg = "{}, The Destination Position is not valid for this attack".format(ctx.message.author.mention)
			elif attackReportCode == -6:
				msg = "{}, You do not have enough Command Points to make this attack.".format(ctx.message.author.mention)

			await ctx.send(msg)
			return 0

		# If there wasnt an error during attack phase, send a battle report
		with dbClient() as client:
			battleReport = client.DBot.wargameBattles.find_one({"battleID": attackReportCode})

		battleReportEmbed = battleReportSimple(attackReportCode)
		await ctx.send("{}".format(ctx.message.author.mention), embed=battleReportEmbed)
		return 0

	@wargame.command(aliases=["rep"])
	async def report(self, ctx, battleID: int):
		battleReportEmbed = battleReportExtended(battleID)
		await ctx.send("{}".format(ctx.message.author.mention), embed=battleReportEmbed)
		return 0

	@wargame.command(aliases=["playerstat"])
	async def me(self, ctx, mentionedUser: discord.User = None):
		if not isUserPlaying(ctx.message.author.id) and not isAdmin(ctx.message.author):
			await ctx.send("{}, you cant check your stats if you are not playing.".format(ctx.message.author.mention))
			return 0

		if mentionedUser != None:
			if not isAdmin(ctx.message.author):
				await ctx.send("{}, you aren't allowed to check other player stats.".format(ctx.message.author.mention))
				return 0
			else:
				targetID = mentionedUser.id
		else:
			targetID = ctx.message.author.id

		playerInfo = queryPlayerInfo(targetID)

		if playerInfo == -1:
			await ctx.send("{}, this player is not registered in the current Wargame".format(ctx.message.author.mention))
			return 0

		embedTitle = "{} Wargame Stats".format(playerInfo["name"])
		embedDescription = "With {} territories, has control of {}% of the map".format(playerInfo["territoryCount"], playerInfo["territoryPercent"])
		embed = discord.Embed(title=embedTitle, description=embedDescription)

		embed.add_field(name="Total Combined Force", value=playerInfo["totalForce"])

		resourcesValue_CP = "CP: {}/{}".format(playerInfo["commandPoints"], playerInfo["commandPointsCap"])
		resourcesValue_Reserves = "Reserves: {}".format(playerInfo["reserves"])
		embed.add_field(name="Resources", value=resourcesValue_CP+"\n"+resourcesValue_Reserves)

		await ctx.send("", embed=embed)
		return 0

	# Increases the force of an owned position
	@wargame.command(aliases=["def"])
	async def fortify(self, ctx, posIndex: str, reservesAmount: int):
		# Check if user is playing
		if not isUserPlaying(ctx.message.author.id) and not isAdmin(ctx.message.author):
			await ctx.send("{}, you cant check your stats if you are not playing.".format(ctx.message.author.mention))
			return 0

		# Parse origin position
		pos = posIndexToCoord(posIndex)
		if type(pos) == int:
			if pos == -1:
				msg = "{}, position can only be refered using letters and digits.".format(ctx.message.author.mention)
			elif pos == -2:
				msg = "{}, the Position can have at most 2 digits.".format(ctx.message.author.mention)
			elif pos == -3:
				msg = "{}, the Position can have at most 1 letter.".format(ctx.message.author.mention)
			elif pos == -4:
				msg = "{}, the entered Position its outside the map.".format(ctx.message.author.mention)
			return 0

		# Try to increment the force of the position
		code = increaseForce(playerID, posCoords, forceIncrement)
		if code == 0:
			msg = "{}, the position {} now has a Force of {} troops.".format(ctx.message.author.mention, posIndex, getPos(pos)["force"])
		elif code == -1:
			msg = "{}, the Position its outside the map".format(ctx.message.author.mention)
		elif code == -2:
			msg = "{}, this Position is not owned by you.".format(ctx.message.author.mention)
		elif code == -3:
			msg = "{}, this Position is not connected to your Capital.".format(ctx.message.author.mention)
		elif code == -4:
			msg = "{}, you don't have enough reserves to fortify this amount.".format(ctx.message.author.mention)

		await ctx.send(msg)
		return 0

	@wargame.command()
	async def sacrifice(self, ctx, waifuID: int):
		# Check if user is playing
		if not isUserPlaying(ctx.message.author.id) and not isAdmin(ctx.message.author):
			await ctx.send("{}, you cant check your stats if you are not playing.".format(ctx.message.author.mention))
			return 0

		# Tries to sacrifice a waifu
		code = sacrificeWaifu(ctx.message.author, waifuID)

		if code == -1:
			msg = "{}, this waifu is not on your list.".format(ctx.message.author.mention)
			await ctx.send(msg)
			return 0

		waifu = waifu_f.getWaifu(waifuID)
		embed = discord.Embed(title="Waifu Sacrifice", description="{} Sacrificed {} and got a Battle Blessing!".format(ctx.message.author.name, waifu["name"]))
		embed.add_field(name="Battle Blessing", value="You got a Battle Roll Bonus of {} for your next battle!".format(getPlayerDoc["battleRollBonus"]))
		embed.set_thumbnail(url=random.choice(waifu["pictures"]))
		await ctx.send("", embed=embed)
		return 0

	@wargame.command(aliases=["times", "timeleft"])
	async def time(self, ctx):
		eventDoc = getEventDoc(WARGAME_EVENT_NAME)
		if eventDoc is None or not eventDoc["active"]:
			await ctx.send("{}, this event is not active now.".format(ctx.message.author.mention))
			return 0

		t = timeNow()
		gameStartTime = datetime.datetime.fromisoformat(eventDoc["gameStartTime"])
		gameEndTime = datetime.datetime.fromisoformat(eventDoc["gameEndTime"])
		registerEndTime = datetime.datetime.fromisoformat(eventDoc["registerEndTime"])

		msg_gameStart = "Start: {}".format(gameStartTime.strftime("%H:%M:%S @ %d-%m-%Y"))
		msg_gameEnd = "End: {}".format(gameEndTime.strftime("%H:%M:%S @ %d-%m-%Y"))
		msg_registerEnd = "Accepting new players until: {}".format(gameEndTime.strftime("%H:%M:%S @ %d-%m-%Y") if registerEndTime > t else "TIME OVER")

		embedTitle = "Wargame Time Left \U000023F3"
		embedDescription = msg_gameStart+"\n"+msg_gameEnd+"\n"+msg_registerEnd
		embed = discord.Embed(title=embedTitle, descrition=embedDescription)
		await ctx.send("", embed=embed)
		return 0
