import os
import requests
import json
import random
import discord

googleFolder = os.path.join(os.getcwd(), "resources", "google")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"}

# returns a custom search google json
def googleSearch(query, Google_APIKey, CSE_ID):
	queryURL = "https://www.googleapis.com/customsearch/v1?key={}&cx={}&q={}&searchType=image".format(Google_APIKey, CSE_ID, query)
	queryResponse = requests.get(queryURL, headers=HEADERS)
	queryJson = json.loads(queryResponse.content)
	return queryJson

# Returns a dict of the path and title of the downloaded image
# mode = first | random
def getGoogleImage(googleJson, mode="first"):
	itemDicts = [item for item in googleJson["items"]]

	if mode == "random":
		item = random.choice(itemDicts)
	elif mode == "first":
		item = itemDicts[0]
	else:
		item = itemDicts[0]


	imgDict = {"title": item["title"], 
			   "url": item["link"], 
			   "queryURL": "https://www.google.com/search?q={}&tbm=isch&safe=images".format(googleJson["queries"]["request"][0]["searchTerms"].replace(" ", "+")),
			   "query": googleJson["queries"]["request"][0]["searchTerms"]}
	return imgDict

# make an embed for google img, google imgrandom commands
def googleEmbed(author, imgDict):
	title = "{}#{}".format(author.name, author.discriminator)
	embed = discord.Embed(title=title, description=imgDict["url"])
	embed.set_author(name="Google search: {}".format(imgDict["query"]),
					 url=imgDict["queryURL"],
					 icon_url="https://upload.wikimedia.org/wikipedia/commons/2/2d/Google-favicon-2015.png")
	embed.set_image(url=imgDict["url"])
	return embed
