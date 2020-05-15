import scripts.google_fAux as google_fAux

########################
# INTERNAL METHODS

def google_img_f(user, query, Google_APIKey, CSE_ID):
	googleJson = google_fAux.googleSearch(query, Google_APIKey, CSE_ID)
	imgDict = google_fAux.getGoogleImage(googleJson, mode="first")
	return google_fAux.googleEmbed(user, imgDict)

def google_imgrandom_f(user, query, Google_APIKey, CSE_ID):
	googleJson = google_fAux.googleSearch(query, Google_APIKey, CSE_ID)
	imgDict = google_fAux.getGoogleImage(googleJson, mode="random")
	return google_fAux.googleEmbed(user, imgDict)
