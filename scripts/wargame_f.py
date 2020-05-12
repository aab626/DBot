import discord

from scripts._aux_f import *
import scripts.waifu_f as waifu_f

from PIL import Image, ImageDraw, ImageFont
import os
import random
import time
import opensimplex
import string
import datetime

#################################
# CONSTANTS AND STATIC FUNCTIONS

SQ_SIZE = 35
LINE_WIDTH = 3

STRIPE_SEMIDIST = int(SQ_SIZE/(1.618**3))

X_SIZE = 30
Y_SIZE = 15

MAP_NOISE_FREQUENCY = 0.325
FORCE_NOISE_FREQUENCY = 0.2
FORCE_NPC_MIN = 5
FORCE_NPC_MAX = 10

MOUNTAIN_LEVEL = 0.7

WARGAME_PATH = os.path.join(os.getcwd(), "resources", "wargame")

font_tile_size = int((0.3*SQ_SIZE - 0.3999)/0.8236)*2
FONT_TILE = ImageFont.truetype(font=os.path.join(WARGAME_PATH, "FreeMonoBold.ttf"), size=font_tile_size)

font_index_size = int((0.95*SQ_SIZE - 0.3999)/0.8236)*2
FONT_INDEX = ImageFont.truetype(font=os.path.join(WARGAME_PATH, "FreeMonoBold.ttf"), size=font_index_size)

START_RESERVES = 0
START_FORCE_BASE = 20

COMMAND_POINTS_BASE = 50
COMMAND_POINT_CAP_BASE = 50

WARGAME_GAME_DURATION_DAYS = 7
WARGAME_REGISTER_DURATION_DAYS = 2

colorData = {
	"red":				{"selectable": True,	"color": (255, 0, 0),		"capitalColor": (255, 127, 0)},
	"orange":			{"selectable": True,	"color": (255, 127, 0),		"capitalColor": (127, 255, 0)},
	"yellow":			{"selectable": True,	"color": (255, 255, 0),		"capitalColor": (0, 255, 0)},
	"chartreuse":		{"selectable": True,	"color": (127, 255, 0),		"capitalColor": (0, 255, 127)},
	"lime":				{"selectable": True,	"color": (0, 255, 0),		"capitalColor": (0, 255, 255)},
	"spring":			{"selectable": True,	"color": (0, 255, 127),		"capitalColor": (0, 127, 255)},
	"cyan":				{"selectable": True,	"color": (0, 255, 255),		"capitalColor": (0, 0, 255)},
	"azure":			{"selectable": True,	"color": (0, 127, 255),		"capitalColor": (127, 0, 255)},
	"blue":				{"selectable": True,	"color": (0, 0, 255),		"capitalColor": (255, 255, 0)},
	"violet":			{"selectable": True,	"color": (127, 0, 255),		"capitalColor": (255, 0, 127)},
	"magenta":			{"selectable": True,	"color": (255, 0, 255),		"capitalColor": (255, 0, 0)},
	"pink":				{"selectable": True,	"color": (255, 0, 127),		"capitalColor": (255, 127, 0)},
	"base_gray":		{"selectable": False,	"color": (200, 200, 200),	"capitalColor": (0, 0, 0)},
	"white":			{"selectable": False,	"color": (255, 255, 255),	"capitalColor": (0, 0, 0)},
	"black":			{"selectable": False,	"color": (0, 0, 0),			"capitalColor": (255, 255, 255)},
	"mountain_tile":	{"selectable": False,	"color": (185, 185, 185),	"capitalColor": (0, 0, 0)},
	"mountain":			{"selectable": False,	"color": (55, 55, 55),		"capitalColor": (0, 0, 0)},
	"mountain_outline": {"selectable": False, 	"color": (20, 20, 20),		"capitalColor": (0, 0, 0)}
	}

########################
# AUXILIARY FUNCTIONS

# error codes
# (posDoc)	ok
# -1		pos outside map
def getPos(pos):
	if not insideMap(pos):
		return -1

	with dbClient() as client:
		posDoc = client.DBot.wargameMap.find_one({"pos": pos})
	return posDoc

def registerPos(pos, ownerID):
	with dbClient() as client:
		client.DBot.wargameMap.update_one({"pos": pos}, {"$set": {"ownerID": ownerID}})

def setPos(pos, posDoc):
	with dbClient() as client:
		client.DBot.wargameMap.replace_one({"pos": pos}, posDoc)

def insideMap(pos):
	x, y = pos
	return (0 <= x <= X_SIZE - 1) and (0 <= y <= Y_SIZE - 1)

def linearTransform(value, minTuple, maxTuple):
	x, y = minTuple
	m, M = maxTuple
	return ((M-m)/2)*value + ((M+m)/2)

# Makes a scan fill from the (pos) position, and returns a list of
# all connected coords with positions matching the (targetTerrainType)
def scanFillTerrain(pos, targetTerrainType, scannedPos=[]):
	if pos in scannedPos:
		return []

	if not insideMap(pos):
		return []

	if getPos(pos)["terrain"] == targetTerrainType:
		L = [pos]
		scannedPos.append(pos)
	else:
		return []

	x, y = pos
	L = L + scanFillTerrain((x+1, y), targetTerrainType, scannedPos)
	L = L + scanFillTerrain((x-1, y), targetTerrainType, scannedPos)
	L = L + scanFillTerrain((x, y+1), targetTerrainType, scannedPos)
	L = L + scanFillTerrain((x, y-1), targetTerrainType, scannedPos)
	return L

# Makes a scan fill from the (pos) position, and returns a list of 
# all connected coords with positions matching the (ownerID)
def scanFillOwner(pos, ownerID, scannedPos=[]):
	if pos in scannedPos:
		print(pos, "scanned")
		return []

	if not insideMap(pos):
		print(pos, "outside")
		return []

	if getPos(pos)["ownerID"] == ownerID:
		print(pos, "added ok")
		L = [tuple(pos)]
		scannedPos.append(pos)
	else:
		print(pos, "not added")
		return []

	x, y = pos
	L = L + scanFillOwner((x+1, y), ownerID, scannedPos)
	L = L + scanFillOwner((x-1, y), ownerID, scannedPos)
	L = L + scanFillOwner((x, y+1), ownerID, scannedPos)
	L = L + scanFillOwner((x, y-1), ownerID, scannedPos)
	return L

def assemblePlayerDoc(pID, pName, pTag, pColor, capitalPos, isAlive=True, 
					  commandPoints=COMMAND_POINTS_BASE, commandPointsCap=COMMAND_POINT_CAP_BASE,
					  startReserves=START_RESERVES):
	playerDoc = dict()
	playerDoc["ID"] = pID
	playerDoc["name"] = pName
	playerDoc["tag"]  = pTag
	playerDoc["color"] = pColor
	playerDoc["capital"] = capitalPos
	playerDoc["isAlive"] = isAlive
	playerDoc["commandPoints"] = commandPoints
	playerDoc["commandPointsCap"] = commandPointsCap
	playerDoc["reserves"] = startReserves
	playerDoc["battleRollBonus"] = 1
	playerDoc["registerDate"] = timeNow().isofomat()
	return playerDoc

def checkOwnership(posCoords, pID):
	posDoc = getPos(posCoords)
	return posDoc["ownerID"] == pID

def getPlayerDoc(playerID):
	with dbClient() as client:
		playerDoc = client.DBot.wargamePlayers.find_one({"ID": playerID})
	return playerDoc

####################
# DRAWING FUNCTIONS

def getColor(colorName):
	return colorData[colorName]["color"]

def getCapitalColor(colorName):
	return colorData[colorName]["capitalColor"]

def getPosBox(pos):
	x,y = pos

	offsetX = LINE_WIDTH
	offsetY = LINE_WIDTH

	x0 = offsetX + x*(SQ_SIZE + LINE_WIDTH)
	y0 = offsetY + y*(SQ_SIZE + LINE_WIDTH)

	x1 = x0 + SQ_SIZE - 1
	y1 = y0 + SQ_SIZE - 1

	posBox = ((x0, y0), (x1, y1))
	return posBox

# returns an image of the map
def drawMap():
	imageSize_X = SQ_SIZE*X_SIZE + LINE_WIDTH*(X_SIZE+1)
	imageSize_Y = SQ_SIZE*Y_SIZE + LINE_WIDTH*(Y_SIZE+1)
	imageSize   = (imageSize_X, imageSize_Y)
	
	mapImg = Image.new("RGBA", imageSize, color=getColor("white"))
	mapDraw = ImageDraw.Draw(mapImg)

	# Draw Lines
	# Vertical lines
	for xi in range(X_SIZE+1):
		x0 = xi*(LINE_WIDTH+SQ_SIZE)
		y0 = 0
		x1 = x0 + LINE_WIDTH - 1
		y1 = mapImg.size[1]

		posBox = ((x0, y0), (x1, y1))
		mapDraw.rectangle(posBox, fill=getColor("black"), outline=None, width=1)

	# Horizontal lines
	for yi in range(Y_SIZE+1):
		x0 = 0
		y0 = yi*(LINE_WIDTH+SQ_SIZE)
		x1 = mapImg.size[0]
		y1 = y0 + LINE_WIDTH - 1

		posBox = ((x0, y0), (x1, y1))
		mapDraw.rectangle(posBox, fill=getColor("black"), outline=None, width=1)

	# Place mountains
	with dbClient() as client:
		mountainPosList = [pos["pos"] for pos in list(client.DBot.wargameMap.find({"terrain": "mountain"}))]

	for pos in mountainPosList:
		posBox = getPosBox(pos)
		mapDraw.rectangle(posBox, fill=getColor("mountain_tile"), outline=None, width=1)

		tri0 = (posBox[0][0]+1, posBox[1][1]-1)
		tri1 = (posBox[1][0]-1, posBox[1][1]-1)
		tri2 = ((posBox[0][0]+posBox[1][0])//2, posBox[0][1]+1)
		trianglePoints = (tri0, tri1, tri2)
		mapDraw.polygon(trianglePoints, fill=getColor("mountain"), outline=getColor("mountain_outline"))

	# Place player areas
	with dbClient() as client:
		playerList = list(client.DBot.wargamePlayers.find({}))

	for player in playerList:
		with dbClient() as client:
			playerPositions = list(client.DBot.wargameMap.find({"ownerID": player["ID"]}))

		for posDoc in playerPositions:
			# Paint tile
			posBox = getPosBox(posDoc["pos"])
			mapDraw.rectangle(posBox, fill=getColor(player["color"]), outline=None, width=1)

			# If its a capital area, draw stripes
			# Skip if NPC
			if posDoc["pos"] == player["capital"] and player["ID"] != -1:
				capitalColor = getCapitalColor(player["color"])

				# stripe \, top-left -> bottom-right
				# right-side of the top-left corner
				x1 = posBox[1][0]
				y0 = posBox[0][1]
				for delta in range(STRIPE_SEMIDIST+1):
					x0 = posBox[0][0] + delta
					y1 = posBox[1][1] - delta
					linePosBox = ((x0, y0), (x1, y1))
					mapDraw.line(linePosBox, fill=capitalColor, width=0)

				# bottom-side of the top-left corner
				x0 = posBox[0][0]
				y1 = posBox[1][1]
				for delta in range(STRIPE_SEMIDIST+1):
					y0 = posBox[0][1] + delta
					x1 = posBox[1][0] - delta
					linePosBox = ((x0, y0), (x1, y1))
					mapDraw.line(linePosBox, fill=capitalColor, width=0)

				# stripe /, bottom-left -> top-right
				# left-side of the bottom-left corner
				x1 = posBox[1][0]
				y0 = posBox[1][1]
				for delta in range(STRIPE_SEMIDIST+1):
					x0 = posBox[0][0] + delta
					y1 = posBox[0][1] + delta
					linePosBox = ((x0, y0), (x1, y1))
					mapDraw.line(linePosBox, fill=capitalColor, width=0)

				# top-side of the bottom-left corner
				x0 = posBox[0][0]
				y1 = posBox[0][1]
				for delta in range(STRIPE_SEMIDIST+1):
					x1 = posBox[1][0] - delta
					y0 = posBox[1][1] - delta
					linePosBox = ((x0, y0), (x1, y1))
					mapDraw.line(linePosBox, fill=capitalColor, width=0)

			# Draw player tag, skip if npc
			if player["ID"] != -1:
				tagPosBox_0 = (posBox[0][0] + 1      , posBox[0][1]+1)
				tagPosBox_1 = (posBox[1][0] - 1 , tagPosBox_0[1] + int(SQ_SIZE*0.5))
				tagPosBox = (tagPosBox_0, tagPosBox_1)

				tagTextSize = mapDraw.textsize(player["tag"], font=FONT_TILE)
				tagImg = Image.new("RGBA", [2*x for x in tagTextSize], color=(0,0,0,0))
				tagDrw = ImageDraw.Draw(tagImg)
				tagDrw.text((int(tagTextSize[0]*0.1),int(tagTextSize[1]*0.1)), player["tag"], font=FONT_TILE, fill=getColor("white"), stroke_width=3, stroke_fill=getColor("black"))
				tagImg = tagImg.crop(box=tagImg.getbbox())

				tagImgSize = (abs(tagPosBox[0][0]-tagPosBox[1][0]+1), abs(tagPosBox[0][1]-tagPosBox[1][1]+1))
				mapImg.alpha_composite(tagImg.resize(tagImgSize), dest=tagPosBox[0])

			# Draw force
			forcePosBox_0 = (posBox[0][0] + 1, posBox[0][1] + 2 + int(SQ_SIZE*0.4))
			forcePosBox_1 = (posBox[1][0] - 1, forcePosBox_0[1] + int(SQ_SIZE*0.35))
			forcePosBox = (forcePosBox_0, forcePosBox_1)

			forceTextSize = mapDraw.textsize(str(posDoc["force"]), font=FONT_TILE)
			forceImg = Image.new("RGBA", [2*x for x in forceTextSize], color=(0,0,0,0))
			forceDrw = ImageDraw.Draw(forceImg)
			forceDrw.text((int(forceTextSize[0]*0.1),int(forceTextSize[1]*0.1)), str(posDoc["force"]), font=FONT_TILE, fill=getColor("white"), stroke_width=4, stroke_fill=getColor("black"))
			forceImg = forceImg.crop(box=forceImg.getbbox())

			forceImgSize_Y = abs(forcePosBox[0][1]-forcePosBox[1][1]+1)
			scaleFactor = forceImgSize_Y/forceImg.size[1]
			forceImgSize_X = int(round(forceImg.size[0]*scaleFactor))
			forceImgSize = (forceImgSize_X, forceImgSize_Y)

			leftover_x = abs(abs(forcePosBox[1][0]-forcePosBox[0][0]+1) - forceImgSize_X)
			forceDestPos = (forcePosBox[0][0] + leftover_x, posBox[1][1] - forceImgSize_Y - 1)

			mapImg.alpha_composite(forceImg.resize(forceImgSize), dest=forceDestPos)

	return mapImg

def drawFrame(imgMap):
	frameSize_X = imgMap.size[0] + SQ_SIZE
	frameSize_Y = imgMap.size[1] + SQ_SIZE
	frameSize = (frameSize_X, frameSize_Y)
	frameImg = Image.new("RGBA", frameSize, color=(255, 255, 255, 255))
	frameDrw = ImageDraw.Draw(frameImg)

	# horizontal indexes (digits)
	for i in range(X_SIZE):
		posBox = getPosBox((i+1, 0))
		
		indexTextSize = frameDrw.textsize(str(i).zfill(2), font=FONT_INDEX)
		indexImg = Image.new("RGBA", indexTextSize, color=(0,0,0,0))
		indexDrw = ImageDraw.Draw(indexImg)
		indexDrw.text((0,0), str(i), font=FONT_INDEX, fill=getColor("black"))

		indexImgSize_X = abs(posBox[1][0]-posBox[0][0]+1) - 10
		if indexImg.size[0] > indexImgSize_X:
			indexImgSize_Y = int((indexImgSize_X*indexTextSize[1])/indexTextSize[0])
			indexImg = indexImg.resize((indexImgSize_X, indexImgSize_Y))

		indexPos_X = posBox[0][0] + (abs(posBox[1][0]-posBox[0][0]+1) - indexImg.size[0])//2
		indexPos_Y = posBox[0][1] + (abs(posBox[1][1]-posBox[0][1]+1) - indexImg.size[1])//2

		frameImg.alpha_composite(indexImg, dest=(indexPos_X, indexPos_Y))

	# vertical indexes (letters)
	for j in range(Y_SIZE):
		posBox = getPosBox((0, j+1))

		indexText = string.ascii_uppercase[j]
		indexTextSize = frameDrw.textsize(indexText, font=FONT_INDEX)
		indexImg = Image.new("RGBA", indexTextSize, color=(0,0,0,0))
		indexDrw = ImageDraw.Draw(indexImg)
		indexDrw.text((0,0), indexText, font=FONT_INDEX, fill=getColor("black"))
		indexImg = indexImg.crop(box=indexImg.getbbox())

		indexImgSize_Y = abs(posBox[1][1]-posBox[0][1]+1)-5
		if indexImg.size[1] > indexImgSize_Y:
			indexImgSize_X = int((indexImgSize_Y*indexTextSize[0])/indexTextSize[1])
			indexImg = indexImg.resize((indexImgSize_X, indexImgSize_Y))
			indexImg = indexImg.resize([int(0.6*c) for c in indexImg.size])

		indexPos_X = posBox[0][0] + (abs(posBox[1][0]-posBox[0][0]+1) - indexImg.size[0])//2
		indexPos_Y = posBox[0][1] + (abs(posBox[1][1]-posBox[0][1]+1) - indexImg.size[1])//2

		frameImg.alpha_composite(indexImg, dest=(indexPos_X, indexPos_Y))

	frameImg.paste(imgMap, box=(SQ_SIZE, SQ_SIZE))
	return frameImg

#################
# MAIN FUNCTIONS

def generateNewMap():
	# Create map seeds and generators
	mapSeed   = random.randint(0, int(time.time()))
	forceSeed = random.randint(0, int(time.time()))

	noiseMap = opensimplex.OpenSimplex(mapSeed)
	noiseForce = opensimplex.OpenSimplex(forceSeed)

	# Start creating each map tile
	for x in range(X_SIZE):
		for y in range(Y_SIZE):
			pos = (x, y)
			elevation = linearTransform(noiseMap.noise2d(x*MAP_NOISE_FREQUENCY,y*MAP_NOISE_FREQUENCY), (-1, 1), (0, 1))

			terrain = "mountain" if elevation >= MOUNTAIN_LEVEL else "valley"
			claimable = True if terrain == "valley" else False
			force = int(linearTransform(noiseMap.noise2d(x*FORCE_NOISE_FREQUENCY, y*FORCE_NOISE_FREQUENCY), (-1,1), (FORCE_NPC_MIN, FORCE_NPC_MAX)))
			ownerID = None

			posDocument = dict()
			posDocument["pos"] = (x,y)
			posDocument["x"] = x
			posDocument["y"] = y
			posDocument["terrain"] = terrain
			posDocument["claimable"] = claimable
			posDocument["force"] = force
			posDocument["ownerID"] = ownerID

			with dbClient() as client:
				client.DBot.wargameMap.insert_one(posDocument)

	# Search for valley pockets
	scannedPos = []
	posGroups = []
	for x in range(X_SIZE):
		for y in range(Y_SIZE):
			pos = (x,y)

			if pos in scannedPos:
				continue

			if getPos(pos)["terrain"] == "mountain":
				continue

			posGroup = scanFillTerrain(pos, "valley")
			scannedPos = scannedPos + posGroup

			if posGroup != []:
				posGroups.append(posGroup)

	# If there are valley pockets:
	# Start removing mountains from each pocket until its connected
	if len(posGroups) > 1:
		posGroups.sort(key=lambda pG: len(pG), reverse=True)
		for pocketGroup in posGroups[1:]:
			positionsInGroup = len(pocketGroup)

			closestPocketPos = None
			closestBigPos = None
			distance = (X_SIZE*Y_SIZE)**2
			for pocketPos in pocketGroup:
				for bigPos in posGroups[0]:
					taxiDist = abs(pocketPos[0]-bigPos[0])+abs(pocketPos[1]-bigPos[1])
					if taxiDist < distance:
						distance = taxiDist
						closestPocketPos = pocketPos
						closestBigPos = bigPos

			# When closest points found, start deleting mountains (from POCKET to BIG)
			xDist = abs(closestPocketPos[0]-closestBigPos[0])
			yDist = abs(closestPocketPos[1]-closestBigPos[1])

			xDir = "right" if closestBigPos[0] > closestPocketPos[0] else "left"
			yDir = "down" if closestBigPos[1] > closestPocketPos[1] else "up"

			currentPos = closestPocketPos
			while xDist > 0 or yDist > 0:
				if xDist > 0 and yDist == 0:
					nextMove = "x"
				elif xDist == 0 and yDist > 0:
					nextMove = "y"
				else:
					nextMove = random.choice(["x", "y"])

				modX, modY = 0, 0
				if nextMove == "x":
					xDist -= 1
					if xDir == "right":
						modX = 1
					else:
						modX = -1
				else:
					yDist -= 1
					if yDir == "down":
						modY = 1
					else:
						modY = -1

				currentPos = (currentPos[0]+modX, currentPos[1]+modY)

				posDoc = getPos(currentPos)
				posDoc["terrain"] = "valley"
				posDoc["claimable"] = True
				setPos(currentPos, posDoc)

	# Set force=0 in all non claimable positions
	with dbClient() as client:
		client.DBot.wargameMap.update_many({"claimable": False}, {"$set": {"force": 0}})

# Register a NPC player, should be used after creating a map
def registerNPC():
	playerDoc = assemblePlayerDoc(-1, "NPC", "NPC", "base_gray", capitalPos=None, isAlive=False, commandPoints=0)

	with dbClient() as client:
		client.DBot.wargamePlayers.insert_one(playerDoc)
		client.DBot.wargameMap.update_many({"claimable": True}, {"$set": {"ownerID": -1}})

def isUserPlaying(userID):
	playerDoc = getPlayerDoc(userID)
	if playerDoc is None:
		return False

	if not playerDoc["isAlive"]:
		return False

	return True

# register a player in the wargame player db
# error codes
# 0		ok
# -1	id already registered
# -2	tag already registered
# -3	no free positions
# -4	bad tag length (hardcoded to [1,2,3])
# -5	bad tag characters (only alphanumeric allowed)
# -6	bad color name (not found)
def registerPlayer(pID, pName, pTag, pColorName):
	# Check if tag is OK (only alphanumeric characters and len 1-3)
	if len(pTag) not in [1,2,3]:
		return -4

	if not pTag.isalnum():
		return -5

	if not (pColorName.lower() in [color for color in colorData.keys() if colorData[color]["selectable"]]):
		return -6
	else:
		pColorName = pColorName.lower()

	# Check for existance of id/name/tag
	with dbClient() as client:
		if client.DBot.wargamePlayers.count_documents({"ID": pID}) > 0:
			return -1
		elif client.DBot.wargamePlayers.count_documents({"tag": pTag}) > 0:
			return -2

	# Search for the best free position
	with dbClient() as client:
		freePositions = [pos["pos"] for pos in list(client.DBot.wargameMap.find({"claimable": True}))]
		humanPositions = client.DBot.wargameMap.find({"$and": [{"claimable": False},{"ownerID": {"$ne":-1}}, {"ownerID": {"$ne": None}}]})

	# If there are no free positions, return error -3:
	if len(freePositions) == 0:
		return -3

	# Get a position which is more than 10 spaces away using taxicab distance
	# if there is no such position, use a random free position
	posList_nearHumanPlayers = []
	scanRadius = 10
	for pos in humanPositions:
		r = scanRadius
		x, y = pos["pos"]
		with dbClient() as client:
			aggregateResults = client.DBot.wargameMap.aggregate([
			{"$match": {"x" : {"$gte": x-r, "$lte": x+r}, "y" : {"$gte": y-r, "$lte": y+r}}},
			{"$set": {"taxicabDistance": {"$add": [{"$abs": {"$subtract": ["$x",x]}}, {"$abs": {"$subtract": ["$y",y]}}]}}},
			{"$match": {"taxicabDistance": {"$lte": r}}},
			{"$group": {"_id": "$taxicabDistance", "set": {"$addToSet": "$pos"}}},
			{"$sort": {"_id": -1}},
			])

		# Adds all found pos to the scanned list
		for distanceSet in aggregateResults:
			posList_nearHumanPlayers = posList_nearHumanPlayers + distanceSet["set"]

	# Filter the free positions that are not near human players
	farPosList = []
	for freePos in freePositions:
		if not (freePos in posList_nearHumanPlayers):
			farPosList.append(freePos)

	# If there is are positions far from players, select a random position from that list, otherwise select a random position from the free list
	if len(farPosList) > 0:
		playerPos = random.choice(farPosList)
	else:
		playerPos = random.choice(freePositions)

	# Register player in the DB
	playerDoc = assemblePlayerDoc(pID, pName, pTag, pColorName, playerPos)
	with dbClient()	as client:
		client.DBot.wargamePlayers.insert_one(playerDoc)
	registerPos(playerPos, pID)

	# Change the force of the position
	adjCoords = [[playerPos[0]+vector[0], playerPos[1]+vector[1]] for vector in [(-1,0), (1, 0), (0, 1), (0, -1)]]
	with dbClient() as client:
		adjForce = [posDoc["force"] for posDoc in list(client.DBot.wargameMap.find({"pos": {"$in": adjCoords}}))]

	extraForce = int(round(sum(adjForce)/len(adjForce))) if len(adjForce) > 0 else 0
	posForce = START_FORCE_BASE + extraForce
	with dbClient() as client:
		client.DBot.wargameMap.update_one({"pos": playerPos}, {"$set": {"force": posForce}})

	return 0

# check if a posDoc is a valid attack for position for another docPos
# based on coordinates (both args)
def isValidAttackCandidate(coordsOrigin, coordsDestination):
	# If any outside of the map
	if (not insideMap(coordsOrigin)) or (not insideMap(coordsDestination)):
		return False

	posOrigin = getPos(coordsOrigin)
	posDestination = getPos(coordsDestination)
	# If destination not claimable
	if not posDestination["claimable"]:
		return False
	# If positions are not adjacent
	elif not isAdjacentPos(coordsOrigin, coordsDestination):
		return False
	# If both positions are owned by same player
	elif posOrigin["ownerID"] == posDestination["ownerID"]:
		return False
	# After all checks, return true
	else:
		return True

def isAdjacentPos(pos1, pos2):
	return pos2 in [[pos1[0]+v[0], pos1[1]+v[1]] for v in [[0,-1], [0,1], [-1,0], [1,0]]]

def combatModifier():
	r = random.randint(1, 20)
	if r == 1:
		return 0.8
	elif 2 <= r <= 3:
		return 0.85
	elif 4 <= r <= 7:
		return 0.9
	elif 8 <= r <= 13:
		return 1
	elif 14 <= r <= 17:
		return 1.1
	elif 18 <= r <= 19:
		return 1.15
	elif r==20:
		return 1.2

def damageModifier():
	r = random.randint(1, 20)
	if r == 1:
		return 0.9
	elif 2 <= r <= 3:
		return 0.925
	elif 4 <= r <= 7:
		return 0.95
	elif 8 <= r <= 13:
		return 1
	elif 14 <= r <= 17:
		return 1.05
	elif 18 <= r <= 19:
		return 1.075
	elif r==20:
		return 1.1

# attack a position
# error codes
# >=0 (battle ID)	ok
# -1				bad coords on origin pos
# -2				bad coords on destination pos
# -3				origin coord does not belong to attacker
# -4				attack force inssuficient
# -5				not valid attack candidate
# -6				not enough command points
def resolveAttack(attackerID, originCoords, destinationCoords, attackForce):
	# Read start origin and destination force
	originPos = getPos(originCoords)
	destinationPos = getPos(destinationCoords)

	# check if those are valid positions
	if type(originPos) == int:
		return -2
	if type(destinationPos) == int:
		return -3

	# check if attacker is the owner of the origin position
	if not checkOwnership(originCoords, attackerID):
		return -3

	# check for enough force in origin position
	if attackForce > originPos["force"]:
		return -4

	# check if attack have enough points for this attack
	attackCPCost = attackForce
	if not checkCommandPoints(attackerID, attackCPCost):
		return -6

	# check if the destination position is not a valid attack position for the origin position
	if not isValidAttackCandidate(originPos["pos"], destinationPos["pos"]):
		return -5

	# check if the defender player was alive before the attack
	# check if defending position is capital
	wasDefenderAlive = isAlive(destinationPos["ownerID"])
	isDefenderCapital = isCapital(destinationCoords, destinationPos["ownerID"])

	# Set base attack parameters
	originForceLeft = originPos["force"] - attackForce

	attackerForce = attackForce
	attackerMod = combatModifier()
	attackerBattleRollBonus = getPlayerDoc(originPos["ownerID"])["battleRollBonus"]
	attackerPower = round(attackerForce * attackerMod * attackerBattleRollBonus, 3)

	defenderForce = destinationPos["force"]
	defenderMod = combatModifier()
	defenderBattleRollBonus = getPlayerDoc(destinationPos["ownerID"])["battleRollBonus"]
	defenderPower = round(defenderForce * defenderMod * defenderBattleRollBonus, 3)

	if isDefenderCapital:
		defenderPower = defenderPower*1.5

	# Clear BattleRollBonus
	clearBattleRollBonus(originPos["ownerID"])
	clearBattleRollBonus(destinationPos["ownerID"])

	with dbClient() as client:
		battleID = client.DBot.wargameBattles.count_documents({})

	battleReport = dict()
	battleReport["battleID"] = battleID
	battleReport["timestamp"] = timeNow().isoformat()
	battleReport["attackerID"] = originPos["ownerID"]
	battleReport["defenderID"] = destinationPos["ownerID"]
	battleReport["isDefenderCapital"] = isDefenderCapital

	battleReport["prelude"] = dict()
	battleReport["prelude"]["attackerForce"] = attackerForce
	battleReport["prelude"]["attackerMod"] = attackerMod
	battleReport["prelude"]["attackerbattleRollBonus"] = attackerBattleRollBonus
	battleReport["prelude"]["attackerPower"] = attackerPower
	battleReport["prelude"]["defenderForce"] = defenderForce
	battleReport["prelude"]["defenderMod"] = defenderMod
	battleReport["prelude"]["defenderbattleRollBonus"] = defenderBattleRollBonus
	battleReport["prelude"]["defenderPower"] = defenderPower

	battleReport["battles"] = []

	doBattle = True
	battles = 0
	attackerPower_initial, defenderPower_initial = attackerPower, defenderPower
	while doBattle:
		doBattle = False
		battles += 1

		attackerDamageMod = damageModifier()
		defenderDamageMod = damageModifier()

		battleDict = dict()
		battleDict["battleNumber"] = battles

		battleDict["before"] = dict()
		battleDict["before"]["attackerPower"]     = attackerPower
		battleDict["before"]["attackerDamageMod"] = attackerDamageMod
		battleDict["before"]["defenderPower"]     = defenderPower
		battleDict["before"]["defenderDamageMod"] = defenderDamageMod

		# Damage calculation
		attackerPower_free    = max(0, attackerPower - defenderPower)
		attackerPower_blocked = attackerPower - AttackerPower_free
		attackerDamage = (attackerPower_free/3 + attackerPower_blocked/5)*attackerDamageMod

		defenderPower_free = max(0, defenderPower - attackerPower)
		defenderPower_blocked = defenderPower - defenderPower_free
		defenderDamage = (defenderPower_free/3 + defenderPower_blocked/5)*defenderDamageMod

		# Damage dealing
		attackerPower = max(0, attackerPower - defenderDamage)
		defenderPower = max(0, defenderPower - attackerDamage)

		battleDict["after"] = dict()
		battleDict["after"]["attackerPower"] = attackerPower
		battleDict["after"]["attackerDamage"] = attackerDamage
		battleDict["after"]["defenderPower"] = defenderPower
		battleDict["after"]["defenderDamage"] = defenderDamage
		battleReport["battles"].append(battleDict)

		# If there is still power left on both sides
		if attackerPower > 0 and defenderPower > 0:
			doBattle = False
			r = random.random()
			if (battles == 1) and (0 <= r <= 0.75):
				doBattle = True
			elif (battles == 2) and (0 <= r <= 0.5):
				doBattle = True
			elif (battles == 3) and (0 <= r <= 0.25):
				doBattle = True
			elif (battles >= 4) and (0 <= r <= 0.1):
				doBattle = True

	remainingAttackerForce = int(max(0, attackerPower)/attackerPower_initial * attackerForce)
	remainingDefenderForce = int(max(0, defenderPower)/defenderPower_initial * defenderForce)

	attackerKills = defenderForce - remainingDefenderForce
	attackerCasualties = attackerForce - remainingAttackerForce

	attackWon = True if (remainingDefenderForce == 0 and remainingAttackerForce > 0) else False

	battleReport["aftermath"] = dict()
	battleReport["aftermath"]["attackWon"] = attackWon
	battleReport["aftermath"]["resultedInCapitulation"] = False
	battleReport["aftermath"]["winnerID"] = originPos["ownerID"] if attackWon else destinationPos["ownerID"]
	battleReport["aftermath"]["attackForce"] = remainingAttackerForce
	battleReport["aftermath"]["defenderForce"] = remainingDefenderForce
	battleReport["aftermath"]["attackerCasualties"] = attackerCasualties
	battleReport["aftermath"]["defenderCasualties"] = attackerKills

	# Refleft changes in DB
	with dbClient() as client:
		# Force change in attack origin position
		client.DBot.wargameMap.update_one({"pos": originPos["pos"]}, {"$set": {"force": originForceLeft}})
	
		# Force/Claim changes in attack destination position
		if attackWon:
			client.DBot.wargameMap.update_one({"pos": destinationPos["pos"]}, {"$set": {"ownerID": originPos["ownerID"], "force": remainingAttackerForce}})
			
			# If defending player was alive before the attack and the attack was made on its capital, capitulate player
			if wasDefenderAlive and isDefenderCapital:
				battleReport["aftermath"]["resultedInCapitulation"] = True
				capitulatePlayer(destinationPos["ownerID"], destinationPos["ownerID"])
		else:
			client.DBot.wargameMap.update_one({"pos": destinationPos["pos"]}, {"$set": {"force": remainingDefenderForce}})

	# Command Points changes in attacker
	changeCommandPoints(attackerID, -attackCPCost)

	# If player was alive when the attack was made, check if its now dead
	isDeadNow = False
	if isAlive(destinationPos["ownerID"]):
		isDeadNow = setIfDead(destinationPos["ownerID"])

	battleReport["aftermath"]["attackKilledDefender"] = isDeadNow

	# Insert battle report
	with dbClient() as client:
		client.DBot.wargameBattles.insert_one(battleReport)

	return battleID

# Returns a path to a full map that this function will create
def askForFullMap(user):
	fullMap_fName = "{}_{}.png".format(time.time(), user.id)
	fullMap_path = os.path.join(WARGAME_PATH, fullMap_fName)
	
	fullMap = drawFrame(drawMap())
	fullMap.save(fullMap_path)
	return fullMap_path

# Deletes a file (used to delete the map created with ask for images functions)
# error codes
# 0		ok
# -1	could not delete file
def deleteMap(mapPath):
	try:
		os.remove(mapPath)
		return 0
	except:
		return -1

# Returns a dictionary with information about the current game
# used with the >war info|summary command
def queryGameInfo():
	with dbClient() as client:
		humanPlayers = list(client.DBot.wargamePlayers.find({}))
		totalPositions = client.DBot.wargameMap.count_documents({"claimable": True})

	gameInfo = dict()
	gameInfo["players"] = []
	for player in humanPlayers:
		playerInfo = dict()
		playerInfo["name"] = player["name"]
		playerInfo["color"] = player["color"]
		playerInfo["tag"] = player["tag"]
		with dbClient() as client:
			territoryNumber = client.DBot.wargameMap.count_documents({"ownerID": player["ID"]})
		playerInfo["territories"] = territoryNumber
		playerInfo["territoryPercent"] = round(territoryNumber/totalPositions*100, 1)

		gameInfo["players"].append(playerInfo)

	return gameInfo

def checkCommandPoints(userID, commandPointsToSpend):
	playerDoc = getPlayerDoc(userID)
	return playerDoc["commandPoints"] >= commandPointsToSpend

# changes the amount of command points of an user
# negative CP_Amount indicates a substraction of CP, a positive amount means CP its being added to the pool
# error codes
# 0		ok
# 1		ok, but amount has been capped to current cap
# -1	not enough CP to do transaction
def changeCommandPoints(userID, CP_Amount):
	if CP_Amount < 0:
		if not checkCommandPoints(userID, CP_Amount):
			return -1

	playerDoc = getPlayerDoc(userID)
	CP_overCap = False
	if CP_Amount > 0:
		if playerDoc["commandPoints"] + CP_Amount > playerDoc["commandPointsCap"]:
			CP_overCap = True

	with dbClient() as client:
		client.DBot.wargamePlayers.update_one({"ID": userID}, 
											  {"$set": {"commandPoints": min(playerDoc["commandPoints"] + CP_Amount, playerDoc["commandPointsCap"])}})

	return 0 if CP_overCap == False else 1

# Returs a coord (x,y) based on a position Index from the map (ie: "4f", "f4", "F4", "4F", etc)
# error codes
# type(list) 	ok
# -1			string passed is not alphanumeric only
# -2			digit quantity is not 1 or 2
# -3			letters quantity is not 1
# -4			position outside map
def posIndexToCoord(posIndex):
	if not posIndex.isalnum():
		return -1

	digits  = [c         for c in posIndex if (c in string.digits)]
	letters = [c.lower() for c in posIndex if (c in string.ascii_letters)]

	if not (len(digits) in [1,2]):
		return -2

	if len(letters) != 1:
		return -3

	number = "".join(digits)
	letter = "".join(letters)

	xPos = int(number)
	yPos = list(string.ascii_lowercase).index(letter)
	pos = (xPos, yPos)

	if not insideMap(pos):
		return -4

	return pos

def battleReportSimple(battleID):
	with dbClient() as client:
		battleReport = client.DBot.wargameBattles.find_one({"battleID": battleID})
		attacker = getPlayerDoc(battleReport["attackerID"])
		defender = getPlayerDoc(battleReport["defenderID"])

	embedTitle = "Battle Report | Battle ID: {}".format(battleID)
	embedDescription = "{} attacks with {} troops to {}, defending with {} troops.".format(attacker["name"],
																						   battleReport["prelude"]["attackerForce"],
																						   defender["name"],
																						   battleReport["prelude"]["defenderForce"])

	# Main Embed
	embed = discord.Embed(title=embedTitle, description=embedDescription)

	# Results Field
	resultName = "Attack Results"
	winnerDoc = attacker if battleReport["aftermath"]["attackWon"] else defender
	battleNumber = len(battleReport["battles"])
	resultValue = "After {} assault{}, {} won.".format(battleNumber, "s" if battleNumber > 1 else "", winnerDoc["name"])

	resultValue2 = ""
	if battleReport["aftermath"]["resultedInCapitulation"]:
		resultValue2 = "This attack resulted in the capitulation of {}".format(defender["name"])
	elif battleReport["aftermath"]["attackKilledDefender"]:
		resultValue2 = "This attack marked the end of {}.".format(defender["name"])
	
	resultValue = (resultValue+"\n"+resultValue2).strip("\n")
	embed.add_field(name=resultName, value=resultValue)

	# Casualties Field
	casualtiesName = "Casualties"
	casualtiesAtkStr = "Attacker: {}".format(battleReport["aftermath"]["attackerCasualties"])
	casualtiesDefStr = "Defender: {}".format(battleReport["aftermath"]["defenderCasualties"])
	casualtiesValue = casualtiesAtkStr+"\n"+casualtiesDefStr
	embed.add_field(name=casualtiesName, value=casualtiesValue)

	# Add timestamp
	t = datetime.datetime.fromisoformat(battleReport["timestamp"])
	embed.set_footer(text="Battle Time: {}".format(t.strftime("%Y-%m-%d %H:%M:%S")))

	return embed

def battleReportExtended(battleID):
	with dbClient() as client:
		battleReport = client.DBot.wargameBattles.find_one({"battleID": battleID})
		attacker = getPlayerDoc(battleReport["attackerID"])
		defender = getPlayerDoc(battleReport["defenderID"])

	# Main Embed
	embedTitle = "Extended Battle Report | Battle ID: {}".format(battleID)
	embedDesc_Attacker = "Attacker: {}\nTroops: {}\nBattle Roll: {}\nBattle Roll Bonus: {}\nAttack Power: {}".format(attacker["name"],
																											  battleReport["prelude"]["attackerForce"],
																											  battleReport["prelude"]["attackerMod"],
																											  battleReport["prelude"]["attackerbattleRollBonus"],
																											  battleReport["prelude"]["attackerPower"])
	embedDesc_Defender = "Defender: {}\nTroops: {}\nBattle Roll: {}\nBattle Roll Bonus: {}\nDefense Power: {}".format(defender["name"],
																											  battleReport["prelude"]["defenderForce"],
																											  battleReport["prelude"]["defenderMod"],
																											  battleReport["prelude"]["defenderbattleRollBonus"],
																											  battleReport["prelude"]["defenderPower"])

	battleNumber = len(battleReport["battles"])
	embedDescription = embedDesc_Attacker+"\n\n"+embedDesc_Defender+"\n\n"+"Battles: {}".format(battleNumber)
	embed = discord.Embed(title=embedTitle, description=embedDescription)

	winnerDoc = attacker if battleReport["aftermath"]["attackWon"] else defender
	resultName = "Battle Result"
	resultValue = "{} ({}) won.".format("Attacker" if battleReport["aftermath"]["attackWon"] else "Defender",
										winnerDoc["name"])

	resultValue2 = ""
	if battleReport["aftermath"]["resultedInCapitulation"]:
		resultValue2 = "This attack made {} capitulate.".format(defender["name"])
	elif battleReport["aftermath"]["attackKilledDefender"]:
		resultValue2 = "This attack eliminated {} from the war.".format(defender["name"])
	
	resultValue = (resultValue+"\n"+resultValue2).strip("\n")
	embed.add_field(name=resultName, value=resultValue)

	# Add a field for each battle
	for battle in battleReport["battles"]:
		attackerBefore = "Attacker: {{Power: {} | Roll: {}}}".format(round(battle["before"]["attackerPower"],3),
																	 round(battle["before"]["attackerDamageMod"],3))
		defenderBefore = "Defender: {{Power: {} | Roll: {}}}".format(round(battle["before"]["defenderPower"],3),
																	 round(battle["before"]["defenderDamageMod"],3))

		damagesBattle = "Damage dealt:\n{{Attacker: {} | Defender: {}}}".format(round(battle["after"]["attackerDamage"],3),
																			   round(battle["after"]["defenderDamage"],3))

		powersAfter = "Aftermath Power:\n{{Attacker: {} | Defender: {}}}".format(round(battle["after"]["attackerPower"],3),
																				round(battle["after"]["defenderPower"],3))

		embedName = "Battle {}/{}".format(battle["battleNumber"], battleNumber)
		embedValue = "Battle Prelude:"+"\n"+attackerBefore+"\n"+defenderBefore+"\n\n"+damagesBattle+"\n"+powersAfter
		embed.add_field(name=embedName, value=embedValue)

	# Add timestamp
	t = datetime.datetime.fromisoformat(battleReport["timestamp"])
	embed.set_footer(text="Battle Time: {}".format(t.strftime("%Y-%m-%d %H:%M:%S")))

	return embed

def setIfDead(playerID):
	isDeadNow = False
	with dbClient() as client:
		if client.DBot.wargameMap.count_documents({"ownerID": playerID}) == 0:
			client.DBot.wargamePlayers.update_one({"ID": playerID}, {"$set": {"isAlive": False}})
			isDeadNow = True
	return isDeadNow

def isAlive(playerID):
	return getPlayerDoc(playerID)["isAlive"]

# Returns a dict with information about a player
# Used with the >wargame me command
# TODO: add CP gain to report
# error codes
# type(dict)	ok
# -1			player not found
def queryPlayerInfo(playerID):
	playerDoc = getPlayerDoc(playerID)
	
	if playerDoc is None:
		return -1

	with dbClient() as client:
		territoryCount = client.DBot.wargameMap.count_documents({"ownerID": playerID})
		totalTerritories = client.DBot.wargameMap.count_documents({"claimable": True})
		totalForce = sum(posDoc["force"] for posDoc in list(client.DBot.wargameMap.find({"ownerID": playerID})))

	playerInfo = dict()
	playerInfo["ID"] = playerDoc["ID"]
	playerInfo["name"] = playerDoc["name"]
	playerInfo["commandPoints"] = playerDoc["commandPoints"]
	playerInfo["commandPointsCap"] = playerDoc["commandPointsCap"]
	playerInfo["territoryCount"] = territoryCount
	playerInfo["territoryPercent"] = round(territoryCount/totalTerritories,1)
	playerInfo["totalForce"] = totalForce
	playerInfo["reserves"] = playerDoc["reserves"]

	return playerInfo

def isCapital(posCoords, playerID):
	capitalPos = getPlayerDoc(playerId)["capital"]
	if capitalPos == None:
		return False
	else:
		return tuple(posCoords) == tuple(capitalPos)

# Gives control of all provinces of the loser to the winner player
# Used when the capital of a player which is playing is lost.
def capitulatePlayer(loserID, winnerID):
	with dbClient() as client:
		client.DBot.wargameMap.update_many({"ownerID": loserID}, {"$set": {"ownerID": winnerID}})

def checkReserves(playerID, reserveAmount):
	currentReserves = getPlayerDoc(playerID)["reserves"]
	return currentReserves >= reserveAmount

# Tries to use an amount of reserves from a player reserve pool
# error codes
# 0		ok
# -1	reservesToUse must be a positive integer
# -2	not enough CP to do transaction
def useReserves(playerID, reservesToUse):
	if not (reservesToUse > 0):
		return -1
	if not checkReserves(playerID, reservesToUse):
		return -2

	newReserves = getPlayerDoc(playerID)["reserves"] - reservesToUse
	with dbClient() as client:
		client.DBot.wargamePlayers({"ID": playerID}, {"$set": {"reserves": newReserves}})
	return 0

# Adds an amount of reserves to a player reserve pool
def addReserves(playerID, reservesToAdd):
	newReserves = getPlayerDoc(playerID)["reserves"] + reservesToAdd
	with dbClient() as client:
		client.DBot.wargamePlayers({"ID": playerID}, {"$set": {"reserves": newReserves}})
	return 0

# Increases the force of a position, as an action of a player
# error codes
# 0		ok
# -1	position outside map
# -2	position not owned by player
# -3	position not connected to capital
# -4	not enough reserves
def increaseForce(playerID, posCoords, forceIncrement):
	if not insideMap(posCoords):
		return -1
	if not checkOwnership(posCoords, playerID):
		return -2
	capitalPos = getPlayerDoc(playerID)["capital"]
	if not (tuple(posCoords) in scanFillOwner(capitalPos, playerID, [])):
		return -3
	if not checkReserves(playerID, forceIncrement):
		return -4

	# After passed checks
	# Update force
	posDoc = getPos(posCoords)
	newForce = posDoc["force"] + forceIncrement
	with dbClient() as client:
		client.DBot.wargameMap.update_one({"pos": posDoc["pos"]}, {"$set": {"force": newForce}})

	# Update reserves
	useReserves(playerID, forceIncrement)
	return 0

# Sacrifices a waifu to get a bonus on the next battle roll
# error codes
# 0		ok
# -1	player does not have this waifu
def sacrificeWaifu(playerUser, waifuID):
	profile = waifu_f.getWaifuProfile(playerUser.id)
	if not (waifuID in profile["waifuList"]):
		return -1

	# Remove the waifu from the user list
	waifu_f.removeWaifu(playerUser, waifuID)

	# Calculate battle roll bonus
	rank = waifu_f.getWaifu(waifuID)["rank"]
	if rank == "E":
		battleRollBonusRange = (1.05, 1.15)
	elif rank == "D":
		battleRollBonusRange = (1.15, 1.25)
	elif rank == "C":
		battleRollBonusRange = (1.25, 1.35)
	elif rank == "B":
		battleRollBonusRange = (1.40, 1.55)
	elif rank == "A":
		battleRollBonusRange = (1.60, 1.75)
	elif rank == "S":
		battleRollBonusRange = (1.80, 2.00)
	elif rank == "SS":
		battleRollBonusRange = (2.50, 3.00)
	elif rank == "SSS":
		battleRollBonusRange = (4.50, 5.00)

	# Sets the battle roll
	battleRollBonus = round(random.uniform(battleRollBonusRange[0], battleRollBonusRange[1]),2)
	setBattleRollBonus(playerUser.id, battleRollBonus)
	return 0
	
def setBattleRollBonus(playerID, battleRollBonus):
	with dbClient() as client:
		client.DBot.wargamePlayers.update_one({"ID": playerID}, {"$set": {"battleRollBonus": battleRollBonus}})

def clearBattleRollBonus(playerID):
	setBattleRollBonus(playerID, 1)

# Starts a new wargame game
# Previous one must be reset using deleteWargame()
def startWargame():
	# Generate a new map and populate it with an NPC player
	generateNewMap()
	registerNPC()

	# Register event times
	t = timeNow()
	gameStart = t
	gameEnd = t + datetime.timedelta(days=WARGAME_GAME_DURATION_DAYS)
	registerEnd = t + datetime.timedelta(days=WARGAME_REGISTER_DURATION_DAYS)

	eventDoc = {"name": "wargameEvent",
				"category": "wargame",
				"active": True,
				"gameStartTime": gameStart.isoformat(),
				"gameEndTime": gameEnd.isoformat(),
				"registerEndTime": registerEnd.isoformat()}
	
	with dbClient() as client:
		client.DBot.events.delete_many({"name": eventDoc["name"]})
		client.DBot.events.insert_one(eventDoc)

def wargameIsRunning():
	eventDoc = getEventDoc("wargameEvent")
	if eventDoc is None or eventDoc["active"] == False:
		return False
	else:
		return True

def deleteWargame():
	# Deletes all previous map and players information
	with dbClient() as client:
		client.DBot.wargameMap.delete_many({})
		client.DBot.wargamePlayers.delete_many({})
		client.DBot.wargameBattles.delete_many({})
		client.DBot.events.update_one({"name": "wargameEvent"}, {"$set": {"active": False}})

def getWargameFinalStats():
	with dbClient() as client:
		humanPlayerList = list(client.DBot.wargamePlayers.find({"ID": {"$ne": -1}}))

		alivePlayerList = []
		for playerDoc in humanPlayerList:
			posList = client.DBot.wargameMap.find({"ownerID": playerDoc["ID"]})
			finalTerritoryCount = len(posList)
			finalForceCount = sum(pos["force"] for pos in posList)

			score = 10*finalTerritoryCount + 1*finalForceCount

			finalDict = {"player": playerDoc,
						 "territories": finalTerritoryCount,
						 "force": finalForceCount,
						 "score": score}

			alivePlayerList.append(finalDict)

	alivePlayerList.sort(key=lambda finalDict: finalDict["score"], reverse=True)
	return finalDict
