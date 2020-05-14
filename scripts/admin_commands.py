import discord
import discord.utils
from discord.ext import commands

from scripts.admin_f import *
from scripts.helpers.aux_f import *
from scripts.helpers.dbClient import *

####################################################
# ADMIN COG

class Admin(commands.Cog):
	def __init__(self, eventChannel):
		self.eventChannel = eventChannel

	@commands.group()
	async def admin(self, ctx):
		pass

	@admin.command(aliases=["oyasumi", "oyasuminasai"])
	async def shutdown(self, ctx):
		code = await shutdown_f(ctx)
		if code == -1:
			await inssuficientPermissions(ctx)			
		return 0

	@admin.command()
	async def addmoney(self, ctx, mentionedUser: discord.User, changeAmount: int):
		code = admin_addmoney(ctx, mentionedUser, changeAmount)
		if code == -1:
			await inssuficientPermissions(ctx)
		elif code == 0:
			await ctx.send("{}, {} balance was changed by {}.".format(ctx.message.author.mention,
																mentionedUser.mention,
																pMoney(changeAmount)))
		return 0

	@admin.group()
	async def event(self, ctx):
		pass

	@event.command()
	async def list(self, ctx):
		code = admin_event_list(ctx)
		if code == -1:
			await inssuficientPermissions(ctx)
		else:
			msg = code
			channel = await ctx.author.create_dm()
			await channel.send(msg)
		
		return 0

	@event.command()
	async def info(self, ctx, eventName: str):
		code = admin_event_info(ctx, eventName)
		if code == -1:
			await inssuficientPermissions(ctx)
		else:
			msg = code
			channel = await ctx.author.create_dm()
			await channel.send(msg)

		return 0

	@event.command()
	async def force(self, ctx, eventName: str, timeToExecution: int):
		code = admin_event_force(ctx, eventName, timeToExecution)
		if code == -1:
			await inssuficientPermissions(ctx)
		elif code == -2:
			await ctx.send("{}, This event is not registered.".format(ctx.author.mention))
		else:
			msg = code
			await ctx.send(msg)
			return 0

	@admin.group()
	async def channel(self, ctx):
		pass

	@channel.command()
	async def register(self, ctx):
		code = admin_channel_register(ctx)
		if code == -1:
			await inssuficientPermissions(ctx)
		elif code == 0:
			await ctx.send("{}, channel registered successfully.".format(ctx.message.author.mention))

		return 0

	@channel.command()
	async def unregister(self, ctx):
		code = admin_channel_unregister(ctx)
		if code == -1:
			await inssuficientPermissions(ctx)
		elif code == 0:
			await ctx.send("{}, channel unregistered successfully.".format(ctx.author.mention))

		return 0

	@admin.command()
	async def add(self, ctx, mentionedUser: discord.User):
		code = admin_add(ctx, mentionedUser)
		if code == -1:
			await inssuficientPermissions(ctx)
		elif code == -2:
			await ctx.send("{}, this user already has DBot Admin privileges".format(ctx.author.mention))
		elif code == 0:
			await ctx.send("{}, {} has been added as a DBot Administrator.".format(ctx.author.mention, mentionedUser.mention))

		return 0

	@admin.command()
	async def remove(self, ctx, mentionedUser: discord.User):
		code = admin_remove(ctx, mentionedUser)
		if code == -1:
			await inssuficientPermissions(ctx)
		elif code == -2:
			await ctx.send("{}, user was not found among DBot Administrators".format(ctx.author.mention))
		elif code == 0:
			await ctx.send("{}, {} DBot Admin privileges have been revoked.".format(ctx.author.mention, mentionedUser.mention))

		return 0
