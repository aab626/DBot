import math

import discord
import pymongo

import scripts.commands.marketplace.marketplace_const as marketplace_const
import scripts.commands.marketplace.marketplace_fAux as marketplace_fAux
from scripts.helpers.singletons import dbClient, Bot
from scripts.models.userprofile import UserProfile

def sell_f(seller, args):
    # Ensure there is at least 3 arguments (category, item dict (at least 1 elem), price)
    if len(args) < 3:
        return -1
    else:
        categoryArg = args[0]
        itemDictArg = args[1:-1]
        priceArg = args[-1]

    # Parse category
    if categoryArg not in marketplace_const.MARKETPLACE_CATEGORIES:
        return -2
    else:
        category = categoryArg

    # Parse price
    if not priceArg.isdigit():
        return -3
    else:
        price = int(priceArg)

    # Price must be a positive integer
    if price < 0:
        return -4

    # Ensure correct itemdict
    if not marketplace_fAux.ensureItemDict(category, itemDictArg):
        return -5
    else:
        itemDict = marketplace_fAux.makeItemDict(category, itemDictArg)

    # Ensure item is sellable by this seller
    if not marketplace_fAux.isSellable(seller, category, itemDict):
        return -6

    # When all checks pass, add this item to the marketplace and remove it from the user
    itemDoc = marketplace_fAux.addToMarketplace(seller, category, itemDict, price)
    marketplace_fAux.removeItem(seller, category, itemDict)

    # Assemble embed
    embed = marketplace_fAux.makeSellEmbed(seller, category, itemDict, price, itemDoc["itemID"])
    return embed

def list_f(ctx, args):
    # Parse page number
    pageList = [int(arg.split("p")[1]) for arg in args if arg.startswith("p") and len(arg.split("p")) == 2 and arg.split("p")[1].isdigit()]
    if len(pageList) > 1:
        return -1
    elif len(pageList) == 1:
        page = pageList[0]
    else:
        page = 1

    # Parse categories
    categories = [arg for arg in args if arg in marketplace_const.MARKETPLACE_CATEGORIES]

    # Parse mentions:
    mentionMode = False
    mentionedIDs = [user.id for user in ctx.message.mentions]
    if len(mentionedIDs) > 0:
        mentionMode = True

    # When no categories passed, list categories and doc count for each one (can be used with mentions)
    if len(categories) == 0:
        embedTitle = "Marketplace Categories \U0001F3EA"
        embedDescriptionLines = []
        for category in marketplace_const.MARKETPLACE_CATEGORIES:
            if mentionMode:
                query = {"$and": [{"category": category}, {"seller.id": {"$in": mentionedIDs}}]}
            else:
                query = {"category": category}
        
            docCount = dbClient.getClient().DBot.marketplace.count_documents({"category": category})
            embedDescLine = "{}: {}".format(category, docCount)
            embedDescriptionLines.append(embedDescLine)

        embedDescription = "\n".join(embedDescriptionLines)
        embed = discord.Embed(title=embedTitle, description=embedDescription)
        return embed

    # If a category has been passed, list all elements in that category
    if mentionMode:
        query = {"$and": [{"category": {"$in": categories}}, {"seller.id": {"$in": mentionedIDs}}]}
    else:
        query = {"category": {"$in": categories}}

    itemsInMarket = list(dbClient.getClient().DBot.marketplace.find(query).sort("itemID", pymongo.ASCENDING))

    if len(itemsInMarket) == 0:
        return -2

    embed = discord.Embed(title="DBot Marketplace \U0001F3EA", description=discord.Embed.Empty)
    itemStart = marketplace_const.MARKET_ITEMS_PER_PAGE*(page-1)
    itemEnd =  itemStart + marketplace_const.MARKET_ITEMS_PER_PAGE
    for itemDoc in itemsInMarket[itemStart:itemEnd]:
        fieldDict = marketplace_fAux.makeListField(itemDoc)
        embed.add_field(name=fieldDict["name"], value=fieldDict["value"], inline=False)

    footerText1 = "Marketplace list page {} of {}".format(page, math.ceil(len(itemsInMarket)/marketplace_const.MARKET_ITEMS_PER_PAGE))
    footerText2 = "Search other pages by using `>marketplace list [pX]`, where X is the page number."
    footerText = "\n".join([footerText1, footerText2])
    embed.set_footer(text=footerText)

    return embed

def cancel_f(user, itemID):
    if not itemID.isdigit():
        return -1
    else:
        itemID = int(itemID)

    itemDoc = dbClient.getClient().DBot.marketplace.find_one({"itemID": itemID})
    if itemDoc is None:
        return -2

    if itemDoc["seller"]["id"] != user.id:
        return -3

    # Remove from marketplace listing and add to user
    marketplace_fAux.addItem(user, itemDoc["category"], itemDoc["item"])
    marketplace_fAux.removeFromMarketplace(itemDoc["itemID"])
    return 0

def buy_f(buyer, itemID):
    if not itemID.isdigit():
        return -1
    else:
        itemID = int(itemID)

    itemDoc = dbClient.getClient().DBot.marketplace.find_one({"itemID": itemID})
    if itemDoc is None:
        return -2
    
    if itemDoc["seller"]["id"] == buyer.id:
        return -3

    # check if buyer has enough money
    buyerProfile = UserProfile.load(buyer)
    if not buyerProfile.ecoCheckBalance(itemDoc["price"]):
        return -4

    # Remove from marketplace listing and add to buyer
    print(buyer)
    marketplace_fAux.addItem(buyer, itemDoc["category"], itemDoc["item"])
    marketplace_fAux.removeFromMarketplace(itemDoc["itemID"])

    # Remove money from buyer, and add to seller
    UserProfile.load(buyer).ecoChangeBalance(-itemDoc["price"], forced=True)
    
    seller = Bot.getBot().get_user(itemDoc["seller"]["id"])
    sellerProfile = UserProfile.load(seller)
    sellerProfile.ecoChangeBalance(itemDoc["price"], forced=True)

    # Assemble embed
    embed = marketplace_fAux.makeBuyEmbed(buyer, seller, itemDoc["category"], itemDoc["item"], itemDoc["price"], itemID)
    return embed
