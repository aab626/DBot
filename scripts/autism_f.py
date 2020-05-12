from scripts.helpers.aux_f import *
from scripts.helpers.dbClient import *

import random
from PIL import Image, GifImagePlugin
import string
import os
import time

def getIsakPhrase(ctx):
	phase1List = ["pucha no puedo", 
				  "justo ahora estoy ocupado", 
				  "ahora lo veo dificil", 
				  "lo siento ahora no", 
				  "pucha no creo que pueda", 
				  "aaahhh no no puedo"]

	mongoClient = dbClient.getClient()
	r = random.randint(0, mongoClient.DBot.isak.count_documents({"accepted": True})-1)
	isakDoc = mongoClient.DBot.isak.find({"accepted": True})[r]

	try:
		emojiIsak = [emoji for emoji in ctx.guild.emojis if emoji.name=="isak"][0]
		emojiStr = "{}".format(emojiIsak)
	except:
		emojiStr = ""

	return "{} porque {} {}".format(random.choice(phase1List), isakDoc["phrase"], emojiStr).strip(" ")

def addIsakPhrase(user, phrase):
	isakDoc = {"phrase": phrase,
			   "user": { "ID": user.id,
			   			 "name": user.name},
			   "accepted": False}

	mongoClient = dbClient.getClient()
	result = mongoClient.DBot.isak.insert_one(isakDoc)
	return result

def getChochePhrase():
	mongoClient = dbClient.getClient()
	r = random.randint(0, mongoClient.DBot.choche.count_documents({"accepted": True})-1)
	chocheDoc = mongoClient.DBot.choche.find({"accepted": True})[r]

	return chocheDoc["phrase"]

def getHiddenChochePhrase(chochePhrase):
	chocheSplit = chochePhrase.split(" ")
	wordsNumber = len(chocheSplit)

	if wordsNumber//3 < 1:
		wordsToHideN = 1
	else:
		wordsToHideN = random.randint(1, wordsNumber//3)

	wordsToHide = []
	while len(wordsToHide) < wordsToHideN:
		randomWord = random.choice(chocheSplit)
		if randomWord in wordsToHide:
			continue
		else:
			wordsToHide.append(randomWord)

	finalSplit = []
	for word in chocheSplit:
		if word in wordsToHide:
			hiddenWord = "`{}`".format("\U00002588"*len(word))
			finalSplit.append(hiddenWord)
		else:
			finalSplit.append(word)

	hiddenChochePhrase = " ".join(finalSplit)
	return hiddenChochePhrase

def checkChochePhrase(chocheGuess, chochePhrase):
	wordsToReplace = [["yutub", "youtube", "yutu", "youtub"],
					  ["todo", "too"],
					  ["todos", "toos"],
					  ["facebook", "feisbuk"],
					  ["face", "feis"],
					  ["misterion", "mysterion"],
					  ["youtubero", "yutubero"],
					  ["youtuberos", "yutuberos"],
					  ["youtuber", "yutuber"],
					  ["youtubers", "yutubers"],
					  ["de", "del"],
					  ["le", "les"]]

	chocheGuess = chocheGuess.lower()
	
	chocheGuessSplitFix = []
	for word in chocheGuess.split(" "):
		i = 0
		foundReplacement = False
		for replaceList in wordsToReplace:
			if word in replaceList:
				replacement = "%REP_{}%".format(i)
				chocheGuessSplitFix.append(replacement)
				foundReplacement = True
				break
			i += 1

		if foundReplacement:
			continue
		else:
			chocheGuessSplitFix.append(word)

	chochePhraseSplitFix = []
	for word in chochePhrase.split(" "):
		i = 0
		foundReplacement = False
		for replaceList in wordsToReplace:
			if word in replaceList:
				replacement = "%REP_{}%".format(i)
				chochePhraseSplitFix.append(replacement)
				foundReplacement = True
				break
			i += 1

		if foundReplacement:
			continue
		else:
			chochePhraseSplitFix.append(word)

	return chocheGuessSplitFix == chochePhraseSplitFix

def addChochePhrase(user, phrase):
	chocheDoc = {"phrase": phrase,
			     "user": { "ID": user.id,
			   			   "name": user.name},
			   	 "accepted": False}

	mongoClient = dbClient.getClient()
	result = mongoClient.DBot.choche.insert_one(chocheDoc)
	return result

# Assembles a phrase with dancing letters (gifs)
# error codes
# type(path)	ok
# -1			phrase too short (min 1 character)
# -2			phrase too long (max 20 characters)
# -3			character not valid (only ascii letters and spaces are allowed)
def makeAutismGif(phrase, user):
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
	imageFileName = "{}_{}.gif".format(time.time(), user.id)
	imageFinalPath = os.path.join(autismFolder, imageFileName)
	
	frames[0].save(imageFinalPath, format="GIF", append_images=frames[1:], save_all=True, duration=170, loop=0, version="GIF89a", background=0, transparency=7, disposal=2)
	return imageFinalPath

def deleteAutism(autismPath):
	try:
		os.remove(autismPath)
		return 0
	except:
		return -1
