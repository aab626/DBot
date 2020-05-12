import discord
import discord.utils
from discord.ext import commands

from scripts.economy_f import *

from scripts.events.ev_economy_claim import *


####################################################
# ECONOMY COG

class Economy(commands.Cog):
	def __init__(self, bot, eventChannel):
		self.bot = bot
		self.eventChannel = eventChannel

		# Add the events to the bot's event loop
		self.claimEvent = claimEvent(name="claim", bot=self.bot, channel=self.eventChannel,
									 minWait=int(2.5*3600), maxWait=5*3600, duration=120,
									 checkWait=60, eventWait=0.1,
									 activityTimeThreshold=30*60, activityWaitMin=int(1*3600), activityWaitMax=int(1.75*3600),
									 prize=12, maxUsers=5)

		self.claimEvent.startLoop()

	###############
	# ECO COMMANDS

	@commands.group()
	async def eco(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("{}, Invalid command, use `>help`".format(ctx.message.author.mention))

	@eco.command()
	async def balance(self, ctx, userMentioned: discord.User = None):
		if userMentioned != None:
			if isAdmin(ctx.message.author):
				targetUser = userMentioned
			else:
				await ctx.send("{}, you have insufficient permissions.".format(ctx.message.author.mention))
				return 0
		else:
			targetUser = ctx.message.author

		hadProfile = checkEconomyProfile(targetUser)
		profile = getEconomyProfile(targetUser)

		embedTitle = "{}'s Balance".format(profile["name"])
		embedDescription = pMoney(profile["balance"])
		embed = discord.Embed(title=embedTitle, description=embedDescription)

		if hadProfile == False:
				embed.set_footer(text="This economy profile has just been created, you have been gifted {}.".format(pMoney(profile["balance"])))

		await ctx.send("", embed=embed)

	@eco.command()
	async def lottery(self, ctx, gamesToPlay: int):
		if gamesToPlay > LOTTERY_MAX_GAMES_ALLOWED:
			await ctx.send("{}, you can play at most {} games per command.".format(ctx.message.author.mention, LOTTERY_MAX_GAMES_ALLOWED))
			return 0

		profile = getEconomyProfile(ctx.message.author)
		# Check if eco locked
		if profile["locked"]:
			await ctx.send("{}, your economy profile is currently locked.".format(ctx.message.author.mention))
			return 0

		# check for funds
		if profile["balance"] < LOTTERY_COST*gamesToPlay:
			await ctx.send("{}, you have inssuficient funds.".format(ctx.message.author.mention))
			return 0

		# play lottery
		lotteryReport = gameLottery(gamesToPlay)

		# format report
		ticketStrings = []
		for game in lotteryReport["games"]:
			ticketStr = "{}: `[{}] ({})` | Prize: {}".format(str(lotteryReport["games"].index(game)+1).zfill(2),
															 "-".join([str(t).zfill(2) for t in game["ticket"]]),
															 str(game["hits"]).zfill(2),
															 game["prize"])
			ticketStrings.append(ticketStr)

		totalPrize = sum([game["prize"] for game in lotteryReport["games"]])
		totalChange = totalPrize - LOTTERY_COST*gamesToPlay
		if totalChange > 0:
			resultStr = "You won {}!".format(pMoney(totalChange))
		elif totalChange < 0:
			resultStr = "You just lost {} haha".format(pMoney(abs(totalChange)))
		else:
			resultStr = "You didn't win or lose anything"

		# substract balance and add if won a prize
		changeBalance(ctx.message.author, -LOTTERY_COST*gamesToPlay)
		if totalPrize > 0:
			changeBalance(ctx.message.author, totalPrize)

		embed = discord.Embed(title="Lottery", description="Winning ticket: `[{}]`".format("-".join([str(t).zfill(2) for t in lotteryReport["winningTicket"]])))
		embed.add_field(name="Tickets", value="\n".join(ticketStrings), inline=False)
		embed.add_field(name="Results", value="Total Prize: {}\n".format(totalPrize)+resultStr, inline=False)
		if totalChange == 0:
			embed.set_footer(text="Booooooooooring")

		await ctx.send("", embed=embed)

	@eco.command(aliases=["welfare"])
	async def collect(self, ctx):
		code = dailyCollect(ctx.message.author)

		if code == -1:
			await ctx.send("{}, you can't collect welfare the same day your economy profile was created.".format(ctx.message.author.mention))
		elif code == -2:
			await ctx.send("{}, you can collect only once every day.".format(ctx.message.author.mention))
		elif code == 0:
			embedTitle = "Welfare collected!"
			embedDescription = "You just collected your daily {}.".format(pMoney(COLLECT_AMOUNT))
			embed = discord.Embed(title=embedTitle, description=embedDescription)
			await ctx.send("", embed=embed)

	@eco.command()
	async def claim(self, ctx):
		if not self.claimEvent.isRunning():
			await ctx.send("{}, this event is not active.".format(ctx.message.author.mention))
			return 0

		if ctx.message.author in self.claimEvent.users:
			await ctx.message.add_reaction("\U0000274C")
		else:
			self.claimEvent.users.append(ctx.message.author)
			await ctx.message.add_reaction("\U0001F4B0")
			
		return 0

	@eco.command()
	async def pay(self, ctx, userMentioned: discord.User, amount: int):
		# Check for correct amount
		if amount <= 0:
			await ctx.send("{}, the amount to pay must be a positive integer".format(ctx.message.author.mention))
			return 0

		profile = getEconomyProfile(ctx.message.author)
		# Check if eco locked
		if profile["locked"]:
			await ctx.send("{}, your economy profile is currently locked.".format(ctx.message.author.mention))
			return 0

		# Check for sufficient funds
		if profile["balance"] < amount:
			await ctx.send("{}, you have inssuficient funds.".format(ctx.message.author.mention))
			return 0

		# Ensure mentioned user has profile
		mentionedProfile = getEconomyProfile(userMentioned)

		# Make balance changes
		changeBalance(ctx.message.author, -amount)
		changeBalance(userMentioned, +amount)

		# Report success
		embed = discord.Embed(title="Successful transaction", description="{} just sent {} to {}.".format(ctx.author.name,
																										  pMoney(amount),
																										  userMentioned.name))
		await ctx.send("", embed=embed)
		return 0

	@eco.command(aliases=["top"])
	async def ranking(self, ctx):
		embed = discord.Embed(title="Economy Ranking", description="Top 5 based on total Balance.") 
		i = 1
		for ecoProfile in getEconomyRankingList()[:5]:
			fieldName = "{}/5: {}".format(i, ecoProfile["name"])
			fieldValue = "Balance: {}".format(pMoney(ecoProfile["balance"]))
			embed.add_field(name=fieldName, value=fieldValue, inline=False)
			i += 1

		await ctx.send("", embed=embed)
