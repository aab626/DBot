import discord

import random
import os

async def callate(message):
	baseWords = ["callate", "matate"]
	extraWords = ["ahora", "imbecil"]

	totalWordN = random.randint(2, 6)
	baseWordN = max(2, totalWordN*2//3)
	extraWordN = (totalWordN - baseWordN)

	selectedWords = []
	for i in range(baseWordN):
		selectedWords.append(random.choice(baseWords))
	for i in range(extraWordN):
		selectedWords.append(random.choice(extraWords))

	wordList = []
	random.shuffle(selectedWords)
	for word in selectedWords:
		#word = random.choice(baseWords)

		while "c" in word and word != "imbecil":
			r = random.random()
			if r <= 0.2:
				break
			word = word.replace("c", "k")

		while "h" in word:
			r = random.random()
			if r <= 0.3:
				break
			word = word.replace("h", "")

		numberOfChanges = random.randint(2, 8)
		alteredChars = []
		for j in range(numberOfChanges):
			char = random.choice(word)
			if char in alteredChars:
				continue

			newChar = char*random.choice([1,2,2,2,2,2,3,3])
			word = word.replace(char, newChar)
			r = random.random()
			if r <= 0.1:
				word = word.replace(newChar, random.choice([" "+newChar, newChar+" "]))

			alteredChars.append(char)


		word = word.upper()
		wordList.append(word)

	finalCallate = " ".join(wordList).strip("Y")
	for i in range(3, 10):
		spacing = " "*i
		finalCallate = finalCallate.replace(spacing, " ")
	
	await message.channel.send("{} {}".format(message.author.mention, finalCallate))

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
