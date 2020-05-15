import random
import string
import os
import time

import discord
from PIL import Image, GifImagePlugin

from scripts.helpers.singletons import Bot, dbClient, EventManager
from scripts.helpers.aux_f import scheduleDeleteFile
import scripts.autism_fAux as autism_fAux

def letter_moment(message):
	if len(message.content) == 2:
		if message.content[0] == Bot.getBot().command_prefix and message.content[1] in string.ascii_uppercase:
			msgDict = autism_fAux.letterMoment(message)
			return msgDict
	else:
		return -1

def callate_f(message):
	if message.content.startswith(">"):
		return -1

	# 1 in 128 = 0.0078125
	r = random.random()
	if r < 0.0078125:
		wordList = ["KALALATEEEEE", 
					"AKALALTE KALALTE KALLATE", 
					"AKALTE KALATE", 
					"KALALTE KALLALTEEEE", 
					"KALLATEEEE", 
					"KALALTE KALALTE KALLATE", 
					"CLAKLAATTEEEEEE", 
					"CAALLATE", 
					"CALALLLATE AORA", 
					"KALLATTETEEEEEE", 
					"CALLLATTE KALLATE KALALATEE", 
					"KALALT EKALALTE KALLATE KALLATE KALLALTTEEE","KKLALTE Y MATATEEEE", 
					"KALATLE MATATE KALLTE MATATATEE", 
					"MATAT ET MATATE MATATEMATATE"]

		word = random.choice(wordList)
		msg = "{} {}".format(message.author.mention, word)
		return msg
	else:
		return -1

def doviafact_f():
	# Random chance for doviafact type
	r = random.random()
	if 0 < r <= 0.3:
		doviafact_type = "communism"
	else:
		doviafact_type = "country"

	# Get doviafact
	i = random.randint(0, dbClient.getClient().DBot.doviafacts.count_documents({"type": doviafact_type}))
	doviafact = dbClient.getClient().DBot.doviafacts.find({"type": doviafact_type})[i]

	# Assemble embed
	embedTitle = "A wonderful Doviafact you didn't know \U0001F4D2"
	embedDescription = doviafact["fact"]
	embed = discord.Embed(title=embedTitle, description=embedDescription)
	embed.set_thumbnail(url="https://raw.githubusercontent.com/drizak/DBot/master/static/doviafact_redditor.png")
	return embed

def isak_f(ctx):
	phase1List = ["Pucha no puedo", 
				  "Justo ahora estoy ocupado", 
				  "Ahora lo veo dificil", 
				  "Ahora no", 
				  "No creo que pueda", 
				  "Aaahhh no no puedo"]

	mongoClient = dbClient.getClient()
	r = random.randint(0, mongoClient.DBot.isak.count_documents({"accepted": True})-1)
	isakDoc = mongoClient.DBot.isak.find({"accepted": True})[r]

	try:
		emojiIsak = [emoji for emoji in ctx.guild.emojis if emoji.name=="isak"][0]
		emojiStr = "{}".format(emojiIsak)
	except:
		emojiStr = ""

	return "{} porque {} {}".format(random.choice(phase1List), isakDoc["phrase"], emojiStr).strip(" ")

def isak_add_f(author, phrase):
	mongoClient = dbClient.getClient()
	isakDocs = list(mongoClient.DBot.isak.find({}))
	if phrase in [isakDoc["phrase"] for isakDoc in isakDocs]:
		return -1
	else:
		isakDoc = {"phrase": phrase,
				   "user": { "ID": author.id,
				   			 "name": author.name},
				   "accepted": False}

		mongoClient.DBot.isak.insert_one(isakDoc)
		return 0

def choche_f(ctx):
	evManager = EventManager.getEventManager()
	chocheEvent = evManager.getEvent("choche")

	if not chocheEvent.isRunning():
		return -1
	else:
		chocheGuess = " ".join(ctx.message.content.split(" ")[1:])
		if autism_fAux.checkChochePhrase(chocheGuess, chocheEvent.chochePhrase):
			chocheEvent.winnerUser = ctx.author
			return 0
		else:
			return -2

def choche_add_f(author, phrase):
	mongoClient = dbClient.getClient()
	chocheDocs = list(mongoClient.DBot.choche.find({}))
	if phrase in [chocheDoc["phrase"] for chocheDoc in chocheDocs]:
		return -1
	else:
		chocheDoc = {"phrase": phrase,
			     "user": { "ID": author.id,
			   			   "name": author.name},
			   	 "accepted": False}

		mongoClient = dbClient.getClient()
		mongoClient.DBot.choche.insert_one(chocheDoc)
		return 0

# Assembles a phrase with dancing letters (gifs)
# error codes
# type(path)	ok
# -1			phrase too short (min 1 character)
# -2			phrase too long (max 20 characters)
# -3			character not valid (only ascii letters and spaces are allowed)
def autism_f(author, phrase):
	allowedCharacters = string.ascii_lowercase + " "
	phrase = phrase.lower()

	# Check length
	if len(phrase) < 1:
		return -1
	if len(phrase) > 20:
		return -2

	# Check for invalid characters
	for c in phrase:
		if not (c in allowedCharacters):
			return -3

	# Collect source letters
	letterDict = dict()
	for char in set(phrase):
		if char != " ":
			letterDict[char] = Image.open(os.path.join(os.getcwd(), "resources", "letters", "{}.gif".format(char)))

	# Calculate size of resulting image
	sizeX = letterDict[phrase[0]].size[0]*len(phrase)
	sizeY = letterDict[phrase[0]].size[1]
	imgSize = (sizeX, sizeY)

	# Start making frames
	frames = []
	frameCount = letterDict[phrase[0]].n_frames
	for frameIndex in range(frameCount):
		imgWordFrame = Image.new("P", imgSize, color=7)
		imgWordFrame.putpalette(letterDict[phrase[0]].getpalette())

		xIndex = 0
		for char in phrase:
			if char == " ":
				xIndex += 1
				continue
			else:
				letterImg = letterDict[char]
				letterImg.seek(frameIndex)

			imgWordFrame.paste(letterImg.copy(), box=(letterDict[phrase[0]].size[0]*xIndex, 0))
			xIndex += 1

		frames.append(imgWordFrame.copy())

	autismFolder = os.path.join(os.getcwd(), "resources", "autism")
	imageFileName = "{}_{}.gif".format(time.time(), author.id)
	imageFinalPath = os.path.join(autismFolder, imageFileName)
	
	frames[0].save(imageFinalPath, format="GIF", append_images=frames[1:], save_all=True, duration=170, loop=0, version="GIF89a", background=0, transparency=7, disposal=2)

	# Schedule for deletion in the minute and return path
	Bot.getBot().loop.create_task(scheduleDeleteFile(imageFinalPath, 15))
	return discord.File(imageFinalPath)
