import discord

import scripts.commands.random.random_fAux as random_fAux

def dice_f(diceArgs):
    if len(diceArgs) == 0:
        diceSource = ["1d6"]
    else:
        diceSource = diceArgs

    diceDict = dict()
    for dice in diceSource:
        throws, faces = [int(x) for x in dice.split("d")]

        for t in range(throws):
            value = random_fAux.throwDice(faces)

            if faces not in diceDict.keys():
                diceDict[faces] = []

            diceDict[faces].append(value)

    sumDict = dict()
    for faces in diceDict.keys():
        if faces not in sumDict.keys():
            sumDict[faces] = 0

        sumDict[faces] += sum(diceDict[faces])

    # Assemble output embed			
    keysSorted = list(diceDict.keys())
    keysSorted.sort()
    valueStrs = []
    for faces in keysSorted:
        valueStr_thisLine = "d{}: {} ({})".format(faces, ", ".join([str(t) for t in diceDict[faces]]), sumDict[faces])
        valueStrs.append(valueStr_thisLine)

    throwString = "\n".join(valueStrs)

    successEmbed = discord.Embed(title="Throwing dice \U0001F3B2...")
    successEmbed.add_field(name="Throws", value=throwString, inline=True)
    successEmbed.add_field(name="Total", value=str(sum(sumDict.values())), inline=True)
    
    return successEmbed

def teams_f(args):
    nGroups = int(args[0])
    nMembersPerGroup = int(args[1])
    playerList = args[2:]
    groupList = random_fAux.makeGroup(nGroups, nMembersPerGroup, playerList)

    membersInGroup = []
    for group in groupList:
        for member in group:
            membersInGroup.append(member)

    membersLeftOut = [player for player in playerList if ((player in membersInGroup) == False)]

    message_out = ""
    for group in groupList:
        message_out = message_out + "\nTeam {}: {}".format(groupList.index(group)+1, ", ".join(group))

    message_out = message_out.strip("\n")

    successEmbed = discord.Embed(title="Team Randomizer \U0001F38C")
    for group in groupList:
        fieldTitle = "Team {}".format(groupList.index(group)+1)
        fieldValue = ", ".join(group)
        successEmbed.add_field(name=fieldTitle, value=fieldValue, inline=False)

    if len(membersLeftOut) > 0:
        successEmbed.set_footer(text="Players left out: {}".format(", ".join(membersLeftOut)))

    return successEmbed
