# Waifu gacha constants
WAIFU_RANKS = ["E", "D", "C", "B", "A", "S","SS", "SSS"]

# Probability per rank
pSSS = 0.0028
pSS  = 0.0112
pS   = 0.056
pA   = 0.07998
pB   = 0.11997
pC   = 0.16926
pD   = 0.25389
pE   = 0.3069

# Cumulative probability per rank
aSSS = pSSS
aSS  = aSSS + pSS
aS   = aSS  + pS
aA   = aS   + pA
aB   = aA   + pB
aC   = aB   + pC
aD   = aC   + pD
aE   = aD   + pE

# Waifu list settings
NO_FAV_WAIFU_URLS = [
    "https://raw.githubusercontent.com/drizak/DBot/master/static/noFavWaifu1.png",
    "https://raw.githubusercontent.com/drizak/DBot/master/static/noFavWaifu2.png"
    "https://raw.githubusercontent.com/drizak/DBot/master/static/noFavWaifu3.png"
    "https://raw.githubusercontent.com/drizak/DBot/master/static/noFavWaifu4.png"
    "https://raw.githubusercontent.com/drizak/DBot/master/static/noFavWaifu5.png"
    "https://raw.githubusercontent.com/drizak/DBot/master/static/noFavWaifu6.png"
    "https://raw.githubusercontent.com/drizak/DBot/master/static/noFavWaifu7.png"
]
WAIFU_LIST_WAIFUS_PER_PAGE = 5