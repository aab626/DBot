import discord

from scripts.helpers.dbClient import *

import os
import random

def letterMoment(message):
	letter = message.content.strip(">").lower()
	letterPath = os.path.join(os.getcwd(), "resources", "letters", "{}.gif".format(letter))

	try:
		emojiFedora = [emoji for emoji in message.guild.emojis if emoji.name=="fedora"][0]
		emojiStr = "{}".format(emojiFedora)
	except:
		emojiStr = "\U0001F3A9"

	msg = "{} moment {}".format(letter.upper(), emojiStr)
	file = discord.File(letterPath)
	return {"msg": msg, "file": file}

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
