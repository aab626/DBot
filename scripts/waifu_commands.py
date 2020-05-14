import discord
import discord.utils
from discord.ext import commands

from scripts.waifu_f import *
from scripts.economy_f import *

from scripts.events.ev_waifu_auctionhouse import *

from scripts.helpers.dbClient import *
from scripts.helpers.aux_f import *

import datetime
import math
import random

##############
# CONSTANTS

WAIFU_LIST_WAIFUS_PER_PAGE = 5

####################################################
# WAIFU COG

class Waifu(commands.Cog):
	def __init__(self, bot, eventChannel):
		self.bot = bot
		self.eventChannel = eventChannel

		# Add the events to the bot's event loop
		self.waifuAuctionHouseEvent = waifuAuctionHouseEvent(name="waifuAH", channel=self.eventChannel,
															 minWait=int(2*3600), maxWait=int(3.5*3600), duration=90,
															 checkWait=60, eventWait=0.1,
															 activityTimeThreshold=1*3600, activityWaitMin=int(0.5*3600), activityWaitMax=int(1.5*3600),
															 timeThresholdToExtend=15, bidTimeExtension=15)

		self.waifuAuctionHouseEvent.startLoop()

	###############
	# WAIFU COMMANDS

	@commands.group()
	async def waifu(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("{}, Invalid command,use `>help`.".format(ctx.message.author.mention))

	# syntax:
	# >waifu list [page] [duplicates|-d|-D] [rank1 rank2...] [@user]
	# reqs: page:	only 1 int
	#		rank	various strs, only in allowed ranks
	#		@User	must be a mention, only for admins
	@waifu.command()
	async def list(self, ctx, *args):
		code = waifu_list_f(ctx, args)
		if code == -1:
			await ctx.send("{}, you can enter at most one page number.".format(ctx.author.mention))
		elif code == -2:
			await inssuficientPermissions(ctx)
		elif code == -3:
			await ctx.send("{}, you can enter at most one mention.".format(ctx.author.mention))
		elif code == -4:
			await ctx.send("{}, you don't have any waifus yet.".format(ctx.author.mention))
		elif code == -5:
			await ctx.send("{}, {} do not have any waifus yet.".format(ctx.author.mention, ctx.mentions[0]))
		elif code == -6:
			await ctx.send("{}, this search returned no waifus!".format(ctx.author.mention))
		else:
			embed = code
			await ctx.send("", embed=embed)

	@waifu.command()
	async def bid(self, ctx, bidAmount: int = 0):
		code = waifu_bid_f(ctx.author, bidAmount)
		if code == -1:
			await ctx.send("{}, this event is not active right now.".format(ctx.author.mention))
		elif code == -2:
			await ctx.send("{}, you have inssuficient funds to make this bid.".format(ctx.author.mention))
		elif code == -3:
			await ctx.send("{}, the minimum bid must be higher than {}.".format(ctx.author.mention, pMoney(self.waifuAuctionHouseEvent.lastBid)))
		elif code == -4:
			await ctx.send("{}, the minimum bid must be at least {} higher than the previous one.".format(
				ctx.message.author.mention,
				pMoney(self.waifuAuctionHouseEvent.bidStepUp)))
		else:
			embed = code
			await ctx.send("", embed=embed)

	@waifu.command(aliases=["fav"])
	async def favorite(self, ctx, favArg):
		code = waifu_favorite_f(ctx.author, favArg)
		print(code)
		if code == -1:
			await ctx.send("{}, you do not have this waifu in your waifu list.".format(ctx.author.mention))
		elif code == -2:
			await ctx.send("{}, the argument must be `clear` or a `Waifu ID`.".format(ctx.author.mention))
		elif code == 0:
			await ctx.send("{}, your new Favorite Waifu has been set!".format(ctx.author.mention))
		elif code == 1:
			await ctx.send("{}, your new Favorite Waifu has been cleared!".format(ctx.author.mention))

	@waifu.command(aliases=["top"])
	async def ranking(self, ctx, rankArg=None):
		embed = waifu_ranking_f(ctx.author, rankArg)
		await ctx.send("", embed=embed)

	@waifu.command(aliases=["fusion"])
	async def fuse(self, ctx, waifuID1: int, waifuID2: int, waifuID3: int):
		code = waifu_fuse_f(ctx.author, waifuID1, waifuID2, waifuID3)
		if code == -1:
			await ctx.send("{}, One of the Waifu IDs you entered is not in your list.".format(ctx.author.mention))
		elif code == -2:
			await ctx.send("{}, The 3 Waifus must have same rank.".format(ctx.author.mention))
		elif code == -3:
			await ctx.send("{}, You can't fuse a SSS-ranked Waifu.".format(ctx.author.mention))
		else:
			embed = code
			await ctx.send("", embed=embed)

	@waifu.command()
	async def summon(self, ctx):
		code = waifu_summon_f(ctx.author)
		if code == -1:
			await ctx.send("{}, you can summon only once per day.".format(ctx.message.author.mention))
		else:
			embed = code
			await ctx.send("", embed=embed)
