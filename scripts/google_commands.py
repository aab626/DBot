from discord.ext import commands

from scripts.google_f import *

# Google cog
class Google(commands.Cog):
	def __init__(self, bot, eventChannel):
		self.bot = bot
		self.eventChannel = eventChannel

	# google group
	@commands.group()
	async def google(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("{}, Invalid command\nuse `>help google` instead".format(ctx.message.author.mention))

	# sends first image
	@google.command()
	async def img(self, ctx, *, query):
		googleJson = googleSearch(query)
		imgDict = getGoogleImage(googleJson, mode="first")
		await ctx.send("", embed=googleEmbed(ctx.message.author, imgDict))


	@google.command(aliases=["imgr"])
	async def imgrandom(self, ctx, *, query):
		googleJson = googleSearch(query)
		imgDict = getGoogleImage(googleJson, mode="random")
		await ctx.send("", embed=googleEmbed(ctx.message.author, imgDict))
