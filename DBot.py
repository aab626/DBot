# DBot.py
import discord
import discord.utils
from discord.ext import commands

# Dependencies
import io
import os
import json
import pymongo

# Change current working directory to this file's directory
os.chdir(os.path.split(os.path.abspath(__file__))[0])

# Commands
import scripts.helpers.aux_f as aux
from scripts.helpers.Bot import *

import scripts.random_commands as random_c
import scripts.google_commands as google_c
import scripts.basic_commands as basic_c
import scripts.economy_commands as economy_c
import scripts.waifu_commands as waifu_c
import scripts.admin_commands as admin_c
import scripts.autism_commands as autism_c
import scripts.autism_commands_bot as autism_cb
# import scripts.wargame_commands as wargame_c

# Set prefix and load token
COMMAND_PREFIX = ">"
with io.open("token", "r", encoding="utf-8") as f:
	TOKEN = f.read()

# Check and/or create folders
# c_aux.checkFolders()

# Init bot and cogs
bot = Bot.getBot(COMMAND_PREFIX)

# Bot events
# When ready, load cogs
@bot.event
async def on_ready():
	aux.log("Removing Help Command")
	bot.remove_command("help")

	aux.log("Loading Event Channel")
	eventChannel = aux.getEventChannel()

	aux.log("Loading cogs")
	bot.add_cog(random_c.Random(bot, eventChannel))
	bot.add_cog(google_c.Google(bot, eventChannel))
	bot.add_cog(basic_c.Basic(bot, eventChannel))
	bot.add_cog(economy_c.Economy(eventChannel))
	bot.add_cog(waifu_c.Waifu(bot, eventChannel))
	bot.add_cog(autism_c.Autism(eventChannel))
	bot.add_cog(admin_c.Admin(eventChannel))
	# bot.add_cog(wargame_c.Wargame(bot, eventChannel))
	aux.log("All cogs loaded")

	aux.log("DBot READY")

@bot.event
async def on_disconnect():
	aux.log("DBot Disconnected")

@bot.event
async def on_resumed():
	aux.log("DBot Resumed Session")

@bot.event
async def on_message(message):
	# DBot messages
	if message.author == bot.user:
		return 0

	# Other bots messages
	if message.author.bot:
		return 0

	# Only bot admins can get bot response with DMs
	if type(message.channel) == discord.channel.DMChannel:
		if aux.isAdmin(message.author) == False:
			return 0

	# Log and process
	# await log(message.author, message.content.strip("\n"))

	# Self-invoked commands kills the command execution
	selfInvokedCommand = False
	if await autism_c.on_message(message) == 0:
		selfInvokedCommand = True

	# Commands
	if not selfInvokedCommand:
		await bot.process_commands(message)

@bot.event
async def on_guild_join(guild):
	#print(guild.emojis)
	general = discord.utils.find(lambda x: x.name == "general", guild.text_channels)
	if general and general.permissions_for(guild.me).send_messages:
		greetingText = "Dbot is here! \*tips fedora*"
		try:
			emojiStr = [emoji for emoji in guild.emojis if emoji.name=="fedora"][0]
		except:
			emojiStr = "\U0001F3A9"

		await general.send("{} {}".format(greetingText, emojiStr))

# Run the bot
bot.run(TOKEN)
