import random

import discord

import scripts.commands.marketplace.marketplace_const as marketplace_const
import scripts.commands.waifu.waifu_fAux as waifu_fAux
import scripts.commands.economy.economy_fAux as economy_fAux
from scripts.models.userprofile import UserProfile
from scripts.helpers.singletons import dbClient
from scripts.helpers.aux_f import utcNow

# category: string
# itemData: list
def ensureItemDict(category, itemData):
    if category not in marketplace_const.MARKETPLACE_CATEGORIES:
        return False
    elif category == "waifu":
        # waifu itemData has only 1 element, waifuID
        if len(itemData) == 1 and itemData[0].isdigit():
            return True
        else:
            return False
    else:
        return False

def makeItemDict(category, itemData):
    if category == "waifu":
        itemDict = {
            "waifuID": int(itemData[0])
        }
        return itemDict
    else:
        return -1

def isSellable(seller, category, itemDict):
    if category == "waifu":
        profile = UserProfile.load(seller)
        waifu = waifu_fAux.getWaifu(itemDict["waifuID"])
        return profile.waifuCheck(waifu)
    else:
        return -1

def addItem(user, category, itemDict):
    print(user, category, itemDict)
    if category == "waifu":
        waifu = waifu_fAux.getWaifu(itemDict["waifuID"])
        print(waifu)
        UserProfile.load(user).waifuAdd(waifu)
    else:
        raise ValueError("not a valid category: {}".format(category))
    return 0

def removeItem(seller, category, itemDict):
    if category == "waifu":
        waifu = waifu_fAux.getWaifu(itemDict["waifuID"])
        UserProfile.load(seller).waifuRemove(waifu)
        return 0
    else:
        raise ValueError("not a valid category: {}".format(category))

def generateItemID():
    marketItems = list(dbClient.getClient().DBot.marketplace.find({}))
    if len(marketItems) == 0:
        return 0

    itemIDs = [item["itemID"] for item in marketItems]
    
    L = list(range(0, max(itemIDs)+1))
    Lp = [iID for iID in L if iID not in itemIDs]

    if len(Lp) == 0:
        newItemID = max(L)+1
    else:
        newItemID = min(Lp)

    return newItemID


def addToMarketplace(seller, category, itemDict, price):
    itemDoc = {
        "itemID": generateItemID(),
        "seller": {
            "name": seller.name,
            "id": seller.id
        },
        "timeCreation": utcNow(),
        "price": price,
        "category": category,
        "item": itemDict
    }

    dbClient.getClient().DBot.marketplace.insert_one(itemDoc)
    return itemDoc

def removeFromMarketplace(itemID):
    dbClient.getClient().DBot.marketplace.delete_one({"itemID": itemID})

def makeSellEmbed(seller, category, itemDict, price, itemID):
    embedTitle = "Marketplace Item Added \U0001F4E8 | ID: {}".format(itemID)
    embedThumbnail = None
    if category == "waifu":
        waifu = waifu_fAux.getWaifu(itemDict["waifuID"])
        embedThumbnail = random.choice(waifu["pictures"])

    embedDescription = makeSellEmbedItemDescription(seller, category, itemDict, price)
    embed = discord.Embed(title=embedTitle, description=embedDescription)

    if embedThumbnail is not None:
        embed.set_thumbnail(url=embedThumbnail)

    return embed

def makeBuyEmbed(buyer, seller, category, itemDict, price, itemID):
    embedTitle = "Successful Purchase \U0001F4B3"
    embedThumbnail = None
    if category == "waifu":
        waifu = waifu_fAux.getWaifu(itemDict["waifuID"])
        embedThumbnail = random.choice(waifu["pictures"])

    embedDescription = makeBuyEmbedItemDescription(buyer, seller, category, itemDict, price)
    embed = discord.Embed(title=embedTitle, description=embedDescription)

    if embedThumbnail is not None:
        embed.set_thumbnail(url=embedThumbnail)
    
    return embed

def makeSellEmbedItemDescription(seller, category, itemDict, price):
    embedDescription0 = "Seller: {}".format(seller.name)
    embedDescription1 = "Category: {}".format(category)

    if category == "waifu":
        waifu = waifu_fAux.getWaifu(itemDict["waifuID"])
        embedDescription2_part1 = "{}{}".format(marketplace_const.ITEM_VALUENAME, waifu["name"])
        embedDescription2_part2 = "{}Source: {}".format(marketplace_const.ITEM_VALUESPACE, waifu["animeName"])
        embedDescription2_part3 = "{}Rank: {}".format(marketplace_const.ITEM_VALUESPACE, waifu["rank"])
        embedDescription2_part4 = "{}Value: {}".format(marketplace_const.ITEM_VALUESPACE, waifu["value"])
        embedDescription2List = [embedDescription2_part1, embedDescription2_part2, embedDescription2_part3, embedDescription2_part4]
        embedDescription2 = "\n".join(embedDescription2List)
    else:
        return ValueError("Not valid category: {}".format(category))
    
    embedDescriptionValue3 = "Price: {}".format(economy_fAux.pMoney(price))
    
    embedValueList = [embedDescription0, embedDescription1, embedDescription2, embedDescriptionValue3]
    embedDescription = "\n".join(embedValueList)
    return embedDescription

def makeBuyEmbedItemDescription(buyer, seller, category, itemDict, price):
    embedDescription0 = "{} just purchased an item from {} for {}!".format(
        buyer.name, 
        seller.name,
        economy_fAux.pMoney(price))
    
    if category == "waifu":
        waifu = waifu_fAux.getWaifu(itemDict["waifuID"])
        embedDescription1_part1 = "{}{}".format(marketplace_const.ITEM_VALUENAME, waifu["name"])
        embedDescription1_part2 = "{}Source: {}".format(marketplace_const.ITEM_VALUESPACE, waifu["animeName"])
        embedDescription1_part3 = "{}Rank: {}".format(marketplace_const.ITEM_VALUESPACE, waifu["rank"])
        embedDescription1_part4 = "{}Value: {}".format(marketplace_const.ITEM_VALUESPACE, waifu["value"])
        embedDescription1List = [embedDescription1_part1, embedDescription1_part2, embedDescription1_part3, embedDescription1_part4]
        embedDescription1 = "\n".join(embedDescription1List)
    else:
        raise ValueError("Not a valid category: {}".format(category))

    embedDescriptionList = [embedDescription0, "", embedDescription1]
    embedDescription = "\n".join(embedDescriptionList)
    return embedDescription

def retrieveItem(itemDoc):
    category = itemDoc["category"]
    if category == "waifu":
        waifuID = itemDoc["item"]["waifuID"]
        waifu = waifu_fAux.getWaifu(waifuID)
        return waifu
    else:
        raise ValueError("itemDoc with no valid category.\n{}".format(itemDoc))

def makeListField(itemDoc):
    category = itemDoc["category"]
    if category == "waifu":
        waifu = retrieveItem(itemDoc)
        fieldName = "ID {} [{}] | {}".format(itemDoc["itemID"], category, waifu["name"])

        fieldValue0 = "Seller: {}".format(itemDoc["seller"]["name"])
        fieldValue1 = "Price: {}".format(itemDoc["price"])
        fieldValue2 = "{}Source: {}".format(marketplace_const.ITEM_VALUESPACE_HALF, waifu["animeName"])
        fieldValue3 = "{}Rank: {}".format(marketplace_const.ITEM_VALUESPACE_HALF, waifu["rank"])
        fieldValue4 = "{}Value: {}".format(marketplace_const.ITEM_VALUESPACE_HALF, waifu["value"])
        fieldValueList = [fieldValue0, fieldValue1, fieldValue2, fieldValue3, fieldValue4]
        fieldValue = "\n".join(fieldValueList)

    else:
        raise ValueError("itemDoc with no valid category.\n{}".format(itemDoc))

    fieldDict = {
        "name": fieldName,
        "value": fieldValue
    }
    return fieldDict
