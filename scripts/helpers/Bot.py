from discord.ext import commands

class Bot:
	__instance = None

	def __init__(self, command_prefix):
		if Bot.__instance == None:
			Bot.__instance = commands.Bot(command_prefix)
		else:
			raise Exception("Bot class is meant to be a singleton.")

	@staticmethod
	def getBot(*args):
		if Bot.__instance == None:
			if len(args) != 1 or type(args[0]) != str:
				raise Exception("For the first initialization of Bot, a command_prefix argument must be passed.")
			else:
				command_prefix = args[0]
				Bot(command_prefix)
		
		return Bot.__instance
