import discord
import discord.utils
from discord.ext import commands

from scripts.economy_f import *

from scripts.events.ev_economy_claim import *


####################################################
# ECONOMY COG

class Economy(commands.Cog):
	def __init__(self, eventChannel):
		self.eventChannel = eventChannel

		# Add the events to the bot's event loop
		self.claimEvent = claimEvent(name="claim", channel=self.eventChannel,
									 minWait=int(2.5*3600), maxWait=5*3600, duration=90,
									 checkWait=60, eventWait=0.1,
									 activityTimeThreshold=60*60, activityWaitMin=int(0.75*3600), activityWaitMax=int(1.5*3600),
									 prize=15, maxUsers=5)

		self.claimEvent.startLoop()

	###############
	# ECO COMMANDS

	@commands.group()
	async def eco(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("{}, Invalid command, use `>help`".format(ctx.message.author.mention))

	@eco.command()
	async def balance(self, ctx, userMentioned: discord.User = None):
		code = balance_f(ctx, userMentioned)
		if code == -1:
			await ctx.send("{}, you have insufficient permissions.".format(ctx.author.mention))
		else:
			embed = code
			await ctx.send("", embed=embed)
		return 0

	@eco.command()
	async def lottery(self, ctx, gamesToPlay: int):
		code = lottery_f(ctx.author, gamesToPlay)
		if code == -1:
			await ctx.send("{}, you can play at most {} lotteries at the same time.".format(ctx.author.mention, LOTTERY_MAX_GAMES_ALLOWED))
		elif code == -2:
			await ctx.send("{}, your economy profile is currently locked.".format(ctx.author.mention))
		elif code == -3:
			await ctx.send("{}, you have insufficient funds for this transaction".format(ctx.author.mention))
		else:
			embed = code
			await ctx.send("", embed=embed)
		return 0

	@eco.command(aliases=["welfare"])
	async def collect(self, ctx):
		code = collect_f(ctx.author)
		if code == -1:
			await ctx.send("{}, you can collect only once every day.".format(ctx.author.mention))
		else:
			embed = code
			await ctx.send("", embed=embed)
		return 0

	@eco.command()
	async def claim(self, ctx):
		code = claim_f(ctx.author)
		if code == -1:
			await ctx.send("{}, this event is not active.".format(ctx.author.mention))
		elif code == -2:
			await ctx.message.add_reaction("\U0000274C")
		elif code == 0:
			await ctx.message.add_reaction("\U0001F4B0")
		return 0

	@eco.command()
	async def pay(self, ctx, userMentioned: discord.User, amount: int):
		code = pay_f(ctx.author, userMentioned, amount)
		if code == -1:
			await ctx.send("{}, the amount to pay must be a positive integer".format(ctx.author.mention))
		elif code == -2:
			await ctx.send("{}, your economy profile is currently locked.".format(ctx.author.mention))
		elif code == -3:
			await ctx.send("{}, the economy profile of {} is currently locked.".format(ctx.author.mention, userMentioned.mention))
		elif code == -4:
			await ctx.send("{}, you have insufficient funds for this transaction".format(ctx.author.mention))
		else:
			embed = code
			await ctx.send("", embed=embed)
		return 0

	@eco.command(aliases=["top"])
	async def ranking(self, ctx):
		embed = ranking_f()
		await ctx.send("", embed=embed)
