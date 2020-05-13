from scripts.google_fAux import *

########################
# INTERNAL METHODS

def google_img_f(user, query, Google_APIKey, CSE_ID):
	googleJson = googleSearch(query, Google_APIKey, CSE_ID)
	imgDict = getGoogleImage(googleJson, mode="first")
	return googleEmbed(user, imgDict)

def google_imgrandom_f(user, query, Google_APIKey, CSE_ID):
	googleJson = googleSearch(query, Google_APIKey, CSE_ID)
	imgDict = getGoogleImage(googleJson, mode="random")
	return googleEmbed(user, imgDict)
