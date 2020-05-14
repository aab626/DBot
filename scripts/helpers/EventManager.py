class EventManager:
	__instance = None

	def __init__(self):
		if EventManager.__instance == None:
			EventManager.__instance = self
		else:
			raise Exception("EventManager is meant to be a singleton.")

		self._eventDict = dict()

	@staticmethod
	def getEventManager():
		if EventManager.__instance == None:
			EventManager()
		return EventManager.__instance

	def registerEvent(self, event):
		if not (event.name in self._eventDict):
			self._eventDict[event.name] = event
			return 0
		else:
			return -1

	def getEvent(self, eventName):
		if eventName in self._eventDict:
			return self._eventDict[eventName]
		else:
			return -1

	def getEventList(self):
		return self._eventDict.keys()
