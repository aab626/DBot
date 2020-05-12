import discord
import discord.utils
from discord.ext import commands

from scripts.autism_commands_bot import *
from scripts.autism_f import *

from scripts.events.ev_autism_choche import *

import string
import os

##########################
# BOT-EVENT DECLARATIONS

# Autism On event message
async def on_message(bot, message):
	if len(message.content) == 2:
		if message.content[0] == bot.command_prefix and message.content[1] in string.ascii_uppercase:
			await letterMoment(message)
			return 0

	callateChance = random.random()
	if callateChance < 0.0078125:
		await callate(message)
		return 0

####################################################
# AUTISM COG

class Autism(commands.Cog):
	def __init__(self, bot, eventChannel):
		self.bot = bot
		self.eventChannel = eventChannel

		# Add the events to the bot's event loop
		self.chocheEvent = chocheEvent(name="choche", bot=self.bot, channel=self.eventChannel,
									   minWait=1*3600, maxWait=3*3600, duration=60,
									   checkWait=60, eventWait=0.1,
									   activityTimeThreshold=30*60, activityWaitMin=int(0.5*1*3600), activityWaitMax=int(0.5*3*3600),
									   minPrize=2, maxPrize=5)
		self.chocheEvent.startLoop()

	@commands.command()
	async def doviarab(self, ctx):
		await ctx.send("22")

	@commands.group()
	async def isak(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send(getIsakPhrase(ctx))
		return 0

	@isak.command(aliases=["add"])
	async def isak_add(self, ctx, *, phraseToAdd: str):
		result = addIsakPhrase(ctx.message.author, phraseToAdd)

		if result.acknowledged:
			await ctx.send("{}, the phrase has been added to isak succesfully.".format(ctx.message.author.mention))
		else:
			await ctx.send("{}, there was an error adding the phrase to isak.".format(ctx.message.author.mention))
		return 0

	@commands.group()
	async def choche(self, ctx):
		if ctx.invoked_subcommand is None:
			if not self.chocheEvent.isRunning():
				await ctx.send("{}, this event is not active.".format(ctx.message.author.mention))
				return 0
			
			chocheGuess = " ".join(ctx.message.content.split(" ")[1:])
			if checkChochePhrase(chocheGuess, self.chocheEvent.chochePhrase):
				self.chocheEvent.winnerUser = ctx.message.author
			else:
				await ctx.message.add_reaction("\U0000274C")
			return 0

	@choche.command(aliases=["add"])
	async def choche_add(self, ctx, *, phraseToAdd):
		result = addChochePhrase(ctx.message.author, phraseToAdd)

		if result.acknowledged:
			await ctx.send("{}, the phrase has been added to choche succesfully.".format(ctx.message.author.mention))
		else:
			await ctx.send("{}, there was an error adding the phrase to choche.".format(ctx.message.author.mention))
		return 0

	@commands.command()
	async def autism(self, ctx, *, phrase):
		code = makeAutismGif(phrase, ctx.message.author)

		if type(code) == int:
			msg = "{}, undocumented error code: {}".format(ctx.message.author.mention, code)
			if code == -1:
				msg = "{}, the phrase needs to have a minimum of 1 character".format(ctx.message.author.mention)
			elif code == -2:
				msg = "{}, the phrase can have at most 20 characters".format(ctx.message.author.mention)
			elif code == -3:
				msg = "{}, the phrase can only have letters and spaces".format(ctx.message.author.mention)

			await ctx.send(msg)
			return 0

		autismGifPath = code
		await ctx.send("", file=discord.File(autismGifPath))
		deleteAutism(autismGifPath)
		return 0
