import collections
import datetime
from bson.codec_options import CodecOptions

from scripts.helpers.singletons import dbClient, Bot
from scripts.helpers.aux_f import TIMEZONE, utcNow, timeTZ
import scripts.commands.economy.economy_const as economy_const

class UserProfile:
    loadedProfiles = []

    def __init__(self, user, timeCreation, ecoDict, waifuDict):
        # General user settings
        self.user = user
        self.timeCreation = timeCreation

        # Economy user settings
        self.ecoBalance = ecoDict["balance"]
        self.ecoTimeCollection = ecoDict["timeCollection"]
        self.ecoLocked = ecoDict["locked"]

        # Waifu user settings
        self.waifuList = waifuDict["waifuList"]
        self.waifuFavorite = waifuDict["waifuFavorite"]
        self.waifuTimeSummoning = waifuDict["timeSummoning"]

    ##################
    # STATIC METHODS

    @staticmethod
    def load(user):
        matchingProfiles = [profile for profile in UserProfile.loadedProfiles if profile.user == user]
        if len(matchingProfiles) == 1:
            return matchingProfiles[0]

        mongoClient = dbClient.getClient()
        timeAware_UsersColl = mongoClient.DBot.users.with_options(
            codec_options=CodecOptions(tz_aware=True, tzinfo=TIMEZONE))
        profileDoc = timeAware_UsersColl.find_one({"user.id": user.id})

        if profileDoc is None:
            user = user
            timeCreation = utcNow()
            ecoDict = {"balance": economy_const.STARTING_MONEY,
                       "timeCollection": utcNow() - datetime.timedelta(days=1),
                       "locked": False}
            waifuDict = {"waifuList": [],
                         "waifuFavorite": None,
                         "timeSummoning": utcNow() - datetime.timedelta(days=1)}
        else:
            user = Bot.getBot().get_user(profileDoc["user"]["id"])
            timeCreation = profileDoc["timeCreation"]
            ecoDict = profileDoc["ecoDict"]
            waifuDict = profileDoc["waifuDict"]

        userProfile = UserProfile(user, timeCreation, ecoDict, waifuDict)
        if profileDoc is None:
            userProfile._save()

        UserProfile.loadedProfiles.append(userProfile)
        return userProfile

    @staticmethod
    def getAllUsers():
        userDocs = dbClient.getClient().DBot.users.find({})
        userList = [UserProfile.load(Bot.getBot().get_user(userDoc["user"]["id"])) for userDoc in userDocs]
        return userList

    #################
    # PUBLIC METHODS

    ##################
    # ECONOMY METHODS

    def ecoChangeBalance(self, changeAmount, forced=False):
        if forced or self.ecoCheckBalance(changeAmount):
            self.ecoLock()
            self.ecoBalance += changeAmount
            self._save_ecoBalance()
            self.ecoUnlock()
            return 0
        else:
            return -1

    # AmountToCheck > 0
    # returns true if the balance >= amountToCheck
    def ecoCheckBalance(self, amountToCheck):
        amountToCheck = abs(amountToCheck)
        if amountToCheck < 0 or self.ecoBalance >= amountToCheck:
            return True
        else:
            return False

    def ecoCollect(self):
        if self.ecoAbleToCollect():
            self.timeCollection = self._save_ecoTimeCollection()
            return 0
        else:
            return -1

    def ecoAbleToCollect(self):
        return timeTZ().date() > self.ecoTimeCollection.date()

    def ecoIsLocked(self):
        return self.ecoLocked

    def ecoLock(self):
        self.ecoLocked = True
        self._save_ecoLock()
    
    def ecoUnlock(self):
        self.ecoLocked = False
        self._save_ecoLock()
        
    #################
    # WAIFU METHODS

    def waifuAdd(self, waifu):
        self.waifuList.append(waifu["MAL_data"]["charID"])
        self._save_waifuList()

    def waifuRemove(self, waifu):
        self.waifuList.remove(waifu["MAL_data"]["charID"])
        self._save_waifuList()

    def waifuCheck(self, waifu):
        if waifu is None:
            return False
        else:
            return waifu["MAL_data"]["charID"] in self.waifuList

    def waifuGetTotalValue(self):
        waifus = list(dbClient.getClient().DBot.waifus.find({"MAL_data.charID": {"$in": self.waifuList}}))
        totalValue = sum([waifu["value"] for waifu in waifus])
        return totalValue

    def waifuSetFavorite(self, waifuID):
        if waifuID not in self.waifuList:
            return -1
        else:
            self.waifuFavorite = waifuID
            self._save_waifuFavorite()
            return 0

    def waifuClearFavorite(self):
        self.waifuFavorite = None
        self._save_waifuFavorite()

    def waifuGetDuplicateWaifuDict(self):
        countDict = collections.Counter(self.waifuList)
        duplicateDict = {waifuID: countDict[waifuID] for waifuID in countDict.keys() if countDict[waifuID] > 1}
        return duplicateDict

    def waifuSummon(self):
        if self.waifuAbleToSummon():
            self.waifuTimeSummoning = self._save_waifuTimeSummoning()
            return 0
        else:
            return -1

    def waifuAbleToSummon(self):
        return timeTZ().date() > self.waifuTimeSummoning.date()


    ###################
    # PRIVATE METHODS

    def _makeDoc(self):
        profileDoc = {
            "user":{
                "name": self.user.name,
                "id": self.user.id
        },
        "timeCreation": self.timeCreation,
        "ecoDict": {
            "balance": self.ecoBalance,
            "timeCollection": self.ecoTimeCollection,
            "locked": self.ecoLocked
        },
        "waifuDict":{
            "waifuList": self.waifuList,
            "waifuFavorite": self.waifuFavorite,
            "timeSummoning": self.waifuTimeSummoning
        }
        }
        
        return profileDoc

    ##########################
    # PRIVATE SAVING METHODS

    def _save(self):
        mongoClient = dbClient.getClient()
        profileDoc = self._makeDoc()
        
        if mongoClient.DBot.users.count_documents({"user.id": self.user.id}) == 0:
            mongoClient.DBot.users.insert_one(profileDoc)
        else:
            mongoClient.DBot.users.replace_one({"user.id": self.user.id}, profileDoc)

    def _save_ecoBalance(self):
        dbClient.getClient().DBot.users.update_one({"user.id": self.user.id}, {"$set": {"ecoDict.balance": self.ecoBalance}})

    def _save_ecoTimeCollection(self):
        timeAware_usersColl = dbClient.getClient().DBot.users.with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=TIMEZONE))
        timeAware_usersColl.update_one({"user.id": self.user.id}, {"$set": {"ecoDict.timeCollection": utcNow()}})
        return timeAware_usersColl.find_one({"user.id": self.user.id})["ecoDict"]["timeCollection"]

    def _save_ecoLock(self):
        dbClient.getClient().DBot.users.update_one({"user.id": self.user.id}, {"$set": {"waifuDict.waifuList": self.waifuList}})

    def _save_waifuList(self):
        dbClient.getClient().DBot.users.update_one({"user.id": self.user.id}, {"$set": {"waifuDict.waifuList": self.waifuList}})

    # def _save_newWaifu(self, waifuID):
    #     dbClient.getClient().DBot.users.update_one({"user.id": self.user.id}, {"$push": {"waifuDict.waifuList": waifuID}})

    def _save_waifuFavorite(self):
        dbClient.getClient().DBot.users.update_one({"user.id": self.user.id}, {"$set": {"waifuDict.waifuFavorite": self.waifuFavorite}})

    def _save_waifuTimeSummoning(self):
        timeAware_usersColl = dbClient.getClient().DBot.users.with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=TIMEZONE))
        timeAware_usersColl.update_one({"user.id": self.user.id}, {"$set": {"waifuDict.timeSummoning": utcNow()}})
        return timeAware_usersColl.find_one({"user.id": self.user.id})["waifuDict"]["timeSummoning"]
