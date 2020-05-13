from discord.ext import commands

from scripts.google_f import *

import io
import json
import os

# Google cog
class Google(commands.Cog):
	def __init__(self, bot, eventChannel):
		self.bot = bot
		self.eventChannel = eventChannel

		with io.open(os.path.join(os.getcwd(), "keys", "google.secret"), "r", encoding="utf-8") as f:
			keyDict = json.load(f)

		self.google_APIKey = keyDict["GoogleAPIKey"]
		self.google_CSEID = keyDict["CustomSearchEngineID"]

	# google group
	@commands.group()
	async def google(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("{}, Invalid command, use `>help` instead.".format(ctx.message.author.mention))

	# sends first image
	@google.command()
	async def img(self, ctx, *, query):
		embed = google_img_f(ctx.author, query, self.google_APIKey, self.CSE_ID)
		await ctx.send("", embed=embed)


	@google.command(aliases=["imgr"])
	async def imgrandom(self, ctx, *, query):
		embed = google_imgrandom_f(ctx.author, query, self.google_APIKey, self.CSE_ID)
		await ctx.send("", embed=embed)
