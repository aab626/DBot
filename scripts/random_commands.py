import discord
from discord.ext import commands

from scripts.random_f import *

class Random(commands.Cog):
	def __init__(self, bot, eventChannel):
		self.bot = bot
		self.eventChannel = eventChannel

	@commands.group()
	async def random(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("{}, Invalid command use `>help random` instead".format(ctx.message.author.mention))

	# random dice
	# throws a dice with a passed string
	@random.command()
	async def dice(self, ctx, *args):
		if len(args) == 0:
			diceSource = ["1d6"]
		else:
			diceSource = args

		diceDict = dict()
		for dice in diceSource:
			throws, faces = [int(x) for x in dice.split("d")]

			for t in range(throws):
				value = throwDice(faces)

				if faces not in diceDict.keys():
					diceDict[faces] = []

				diceDict[faces].append(value)

		sumDict = dict()
		for faces in diceDict.keys():
			if faces not in sumDict.keys():
				sumDict[faces] = 0

			sumDict[faces] += sum(diceDict[faces])

		# Assemble output embed			
		keysSorted = list(diceDict.keys())
		keysSorted.sort()
		valueStrs = []
		for faces in keysSorted:
			valueStr_thisLine = "d{}: {} ({})".format(faces, ", ".join([str(t) for t in diceDict[faces]]), sumDict[faces])
			valueStrs.append(valueStr_thisLine)

		throwString = "\n".join(valueStrs)

		successEmbed = discord.Embed(title="Throwing dice \U0001F3B2...")
		successEmbed.add_field(name="Throws", value=throwString, inline=True)
		successEmbed.add_field(name="Total", value=str(sum(sumDict.values())), inline=True)

		await ctx.send("", embed=successEmbed)

	# random teams
	# prints the teams assembled with the makeGroup function
	@random.command()
	async def teams(self, ctx, *args):
		nGroups = int(args[0])
		nMembersPerGroup = int(args[1])
		playerList = args[2:]
		groupList = makeGroup(nGroups, nMembersPerGroup, playerList)

		membersInGroup = []
		for group in groupList:
			for member in group:
				membersInGroup.append(member)

		membersLeftOut = [player for player in playerList if ((player in membersInGroup) == False)]

		message_out = ""
		for group in groupList:
			message_out = message_out + "\nTeam {}: {}".format(groupList.index(group)+1, ", ".join(group))

		message_out = message_out.strip("\n")

		successEmbed = discord.Embed(title="Team Randomizer \U0001F38C")
		for group in groupList:
			fieldTitle = "Team {}".format(groupList.index(group)+1)
			fieldValue = ", ".join(group)
			successEmbed.add_field(name=fieldTitle, value=fieldValue, inline=False)

		if len(membersLeftOut) > 0:
			successEmbed.set_footer(text="Players left out: {}".format(", ".join(membersLeftOut)))

		await ctx.send("", embed=successEmbed)
