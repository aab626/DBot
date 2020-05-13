import discord

import random
import os



async def letterMoment(message):
	letter = message.content.strip(">").lower()
	letterPath = os.path.join(os.getcwd(), "resources", "letters", "{}.gif".format(letter))

	try:
		emojiFedora = [emoji for emoji in message.guild.emojis if emoji.name=="fedora"][0]
		emojiStr = "{}".format(emojiFedora)
	except:
		emojiStr = "\U0001F3A9"

	msg = "{} moment {}".format(letter.upper(), emojiStr)
	await message.channel.send(msg, file=discord.File(letterPath))
