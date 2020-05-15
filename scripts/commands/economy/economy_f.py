import discord
import pymongo

import scripts.commands.economy.economy_fAux as economy_fAux
import scripts.commands.economy.economy_const as economy_const
from scripts.helpers.aux_f import isAdmin
from scripts.helpers.singletons import Bot, EventManager, dbClient
from scripts.models.userprofile import UserProfile


def balance_f(ctx, userMentioned):
    if userMentioned != None:
        if isAdmin(ctx.author):
            targetUser = userMentioned
        else:
            return -1
    else:
        targetUser = ctx.author

    profile = UserProfile.load(targetUser)

    embedTitle = "{}'s Balance".format(profile.user.name)
    embedDescription = economy_fAux.pMoney(profile.ecoBalance)
    embed = discord.Embed(title=embedTitle, description=embedDescription)
    return embed


def lottery_f(user, gamesToPlay):
    if gamesToPlay > economy_const.LOTTERY_MAX_GAMES_ALLOWED:
        return -1

    profile = UserProfile.load(user)
    if profile.ecoIsLocked():
        return -2

    totalCost = economy_const.LOTTERY_COST * gamesToPlay
    if not profile.ecoCheckBalance(totalCost):
        return -3

    # When all checks pass, lock the profile
    profile.ecoLock()

    # Play lottery and assemble report embed
    lotteryReport = economy_fAux.gameLottery(gamesToPlay)
    ticketStrings = []
    for game in lotteryReport["games"]:
        ticketStr = "{}: `[{}] ({})` | Prize: {}".format(str(lotteryReport["games"].index(game)+1).zfill(2),
                                                         "-".join([str(t).zfill(2)
                                                                   for t in game["ticket"]]),
                                                         str(game["hits"]).zfill(
            2),
            game["prize"])
        ticketStrings.append(ticketStr)

    totalPrize = sum([game["prize"] for game in lotteryReport["games"]])
    totalChange = totalPrize - totalCost
    if totalChange > 0:
        resultStr = "You won {}!".format(economy_fAux.pMoney(totalChange))
    elif totalChange < 0:
        resultStr = "You just lost {} haha".format(
            economy_fAux.pMoney(abs(totalChange)))
    else:
        resultStr = "You didn't win or lose anything"

    embed = discord.Embed(title="Lottery", description="Winning ticket: `[{}]`".format(
        "-".join([str(t).zfill(2) for t in lotteryReport["winningTicket"]])))
    embed.add_field(name="Tickets", value="\n".join(
        ticketStrings), inline=False)
    embed.add_field(name="Results", value="Total Prize: {}\n{}".format(
        totalPrize, resultStr), inline=False)
    if totalChange == 0:
        embed.set_footer(text="Booooooooooring")

    # Make balance changes and unlock profile
    profile.ecoChangeBalance(totalPrize-totalCost)
    profile.ecoUnlock()

    return embed


def collect_f(user):
    profile = UserProfile.load(user)
    code = profile.ecoCollect()
    if code == -1:
        return -1
    elif code == 0:
        profile.ecoChangeBalance(economy_const.COLLECTION_MONEY, forced=True)
        embedTitle = "Welfare Collected!"
        embedDescription = "You just collected your daily {}".format(economy_fAux.pMoney(economy_const.COLLECTION_MONEY))
        embed = discord.Embed(title=embedTitle, description=embedDescription)
        return embed


def claim_f(user):
    evManager = EventManager.getEventManager()
    claimEvent = evManager.getEvent("claim")

    if not claimEvent.isRunning():
        return -1
    elif user in claimEvent.users:
        return -2
    else:
        claimEvent.users.append(user)
        return 0


def pay_f(originUser, destinationUser, amount):
    if amount <= 0:
        return -1

    originProfile = UserProfile.load(originUser)
    if originProfile.ecoIsLocked():
        return -2

    destinationProfile = UserProfile.load(destinationUser)
    if destinationProfile.ecoIsLocked():
        return -3

    if not originProfile.ecoCheckBalance(amount):
        return -4

    originProfile.ecoChangeBalance(-amount)
    destinationProfile.ecoChangeBalance(amount)

    embedTitle = "Successful transaction"
    embedDescription = "{} just sent {} to {}.".format(
        originUser.name, economy_fAux.pMoney(amount), destinationUser.name)
    embed = discord.Embed(title=embedTitle, description=embedDescription)
    return embed


def ranking_f():
    embed = discord.Embed(title="Economy Ranking",
                          description="Top 5 based on total Balance.")

    mongoClient = dbClient.getClient()
    userDocs = list(mongoClient.DBot.economy.find({}).sort("balance", pymongo.DESCENDING))

    selectedDocs = userDocs[:5]
    for userDoc in selectedDocs:
        profile = UserProfile.load(Bot.getBot().get_user(userDoc["user"]["id"]))
        fieldName = "{}/{}: {}".format(selectedDocs.index(userDoc)+1,
                                       len(selectedDocs), profile.user.name)
        fieldValue = "Balance: {}".format(economy_fAux.pMoney(profile.ecoBalance))
        embed.add_field(name=fieldName, value=fieldValue, inline=False)

    return embed
