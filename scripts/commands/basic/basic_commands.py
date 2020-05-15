from discord.ext import commands


class Basic(commands.Cog):
    def __init__(self, eventChannel):
        self.eventChannel = eventChannel

    @commands.command()
    async def ping(self, ctx, *args):
        await ctx.send("pong \U0001F3D3")

    @commands.command()
    async def help(self, ctx):
        await ctx.send("Check the docs @ https://drizak.github.io/DBot/docs/")
