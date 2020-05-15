import discord
import pymongo

import scripts.economy_fAux as economy_fAux
from scripts.helpers.aux_f import isAdmin
from scripts.helpers.singletons import Bot, EventManager, dbClient
from scripts.models.economy import EcoProfile


def balance_f(ctx, userMentioned):
    if userMentioned != None:
        if isAdmin(ctx.author):
            targetUser = userMentioned
        else:
            return -1
    else:
        targetUser = ctx.author

    profile = EcoProfile.load(targetUser)

    embedTitle = "{}'s Balance".format(profile.user.name)
    embedDescription = economy_fAux.pMoney(profile.balance)
    embed = discord.Embed(title=embedTitle, description=embedDescription)
    return embed


def lottery_f(user, gamesToPlay):
    if gamesToPlay > economy_fAux.LOTTERY_MAX_GAMES_ALLOWED:
        return -1

    profile = EcoProfile.load(user)
    if profile.isLocked():
        return -2

    totalCost = economy_fAux.LOTTERY_COST * gamesToPlay
    if not profile.checkBalance(totalCost):
        return -3

    # When all checks pass, lock the profile
    profile.lock()

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
    profile.changeBalance(totalPrize-totalCost)
    profile.unlock()

    return embed


def collect_f(user):
    profile = EcoProfile.load(user)
    code = profile.collect()
    if code == -1:
        return -1
    elif code == 0:
        embedTitle = "Welfare Collected!"
        embedDescription = "You just collected your daily {}".format(
            economy_fAux.pMoney(EcoProfile.COLLECTION_MONEY))
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

    originProfile = EcoProfile.load(originUser)
    if originProfile.isLocked():
        return -2

    destinationProfile = EcoProfile.load(destinationUser)
    if destinationProfile.isLocked():
        return -3

    if not originProfile.checkBalance(amount):
        return -4

    originProfile.changeBalance(-amount)
    destinationProfile.changeBalance(amount)

    embedTitle = "Successful transaction"
    embedDescription = "{} just sent {} to {}.".format(
        originUser.name, economy_fAux.pMoney(amount), destinationUser.name)
    embed = discord.Embed(title=embedTitle, description=embedDescription)
    return embed


def ranking_f():
    embed = discord.Embed(title="Economy Ranking",
                          description="Top 5 based on total Balance.")

    mongoClient = dbClient.getClient()
    ecoDocs = list(mongoClient.DBot.economy.find(
        {}).sort("balance", pymongo.DESCENDING))

    selectedDocs = ecoDocs[:5]
    for ecoDoc in selectedDocs:
        profile = EcoProfile.load(Bot.getBot().get_user(ecoDoc["user"]["id"]))
        fieldName = "{}/{}: {}".format(selectedDocs.index(ecoDoc)+1,
                                       len(selectedDocs), profile.user.name)
        fieldValue = "Balance: {}".format(economy_fAux.pMoney(profile.balance))
        embed.add_field(name=fieldName, value=fieldValue, inline=False)

    return embed
