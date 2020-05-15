import discord
from discord.ext import commands

import scripts.commands.random.random_f as random_f

class Random(commands.Cog):
	def __init__(self, eventChannel):
		self.eventChannel = eventChannel

	@commands.group()
	async def random(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("{}, Invalid command use `>help random` instead".format(ctx.author.mention))

	# random dice
	# throws a dice with a passed string
	@random.command()
	async def dice(self, ctx, *diceArgs):
		embed = random_f.dice_f(diceArgs)
		await ctx.send("", embed=embed)

	# random teams
	# prints the teams assembled with the makeGroup functions
	@random.command()
	async def teams(self, ctx, *args):
		embed = random_f.teams_f(args)
		await ctx.send("", embed=embed)
