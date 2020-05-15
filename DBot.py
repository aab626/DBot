# Dependencies
import io
import json
import os

# DBot.py
import discord
import discord.utils
import pymongo
from discord.ext import commands

# Commands
import scripts.commands.admin.admin_commands as admin_commands
import scripts.commands.autism.autism_commands as autism_commands
import scripts.commands.basic.basic_commands as basic_commands
import scripts.commands.economy.economy_commands as economy_commands
import scripts.commands.google.google_commands as google_commands
import scripts.commands.random.random_commands as random_commands
import scripts.commands.waifu.waifu_commands as waifu_commands

from scripts.helpers.aux_f import getEventChannel, isAdmin, log
from scripts.helpers.singletons import Bot

# Check if this is not the main file
if __name__ != "__main__":
    raise Exception("DBot.py should be the main executable!")

# Change current working directory to this file's directory
os.chdir(os.path.split(os.path.abspath(__file__))[0])

# Set prefix and load token
COMMAND_PREFIX = ">"
with io.open(os.path.join(os.getcwd(), "keys", "token.secret"), "r", encoding="utf-8") as f:
    TOKEN = f.read()

# Init bot and cogs
bot = Bot.getBot(COMMAND_PREFIX)

# Bot events
# When ready, load cogs
@bot.event
async def on_ready():
    log("Removing Help Command")
    bot.remove_command("help")

    log("Loading Event Channel")
    eventChannel = getEventChannel()

    log("Loading cogs")
    bot.add_cog(random_commands.Random(eventChannel))
    bot.add_cog(google_commands.Google(eventChannel))
    bot.add_cog(basic_commands.Basic(eventChannel))
    bot.add_cog(economy_commands.Economy(eventChannel))
    bot.add_cog(waifu_commands.Waifu(eventChannel))
    bot.add_cog(admin_commands.Admin(eventChannel))
    bot.add_cog(autism_commands.Autism(eventChannel))
    # bot.add_cog(wargame_c.Wargame(bot, eventChannel))
    log("All cogs loaded")

    log("DBot READY")


@bot.event
async def on_disconnect():
    log("DBot Disconnected")


@bot.event
async def on_resumed():
    log("DBot Resumed Session")


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
        if isAdmin(message.author) == False:
            return 0

    # Self-invoked commands kills the command execution
    selfInvokedCommand = False
    if await autism_commands.on_message(message) == 0:
        selfInvokedCommand = True

    # Commands
    # Log and then process
    if not selfInvokedCommand:
        log(message)
        await bot.process_commands(message)


@bot.event
async def on_guild_join(guild):
    general = discord.utils.find(
        lambda x: x.name == "general", guild.text_channels)
    if general and general.permissions_for(guild.me).send_messages:
        greetingText = "Dbot is here! \*tips fedora*"
        try:
            emojiStr = [
                emoji for emoji in guild.emojis if emoji.name == "fedora"][0]
        except:
            emojiStr = "\U0001F3A9"

        await general.send("{} {}".format(greetingText, emojiStr))

# Run the bot
bot.run(TOKEN)
