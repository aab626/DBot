import random

# internal function
# return a dice throw
def throwDice(faces=6):
	return random.randint(1, faces)

# internal function, sort groups
# returns a list of lists, where each sub-list is a list of strings
def makeGroup(groups, MembersPerGroup, playerListTuple):
	playerList = []
	for player in playerListTuple:
		playerList.append(player)

	random.shuffle(playerList)
	while groups*MembersPerGroup < len(playerList):
		playerList.pop()

	g = 0
	i = 0
	groupList = [[] for i in range(groups)]
	while i < len(playerList):
		groupList[g].append(playerList[i])
		g += 1

		if g >= groups:
			g = 0

		i += 1

	random.shuffle(groupList)

	return groupList
