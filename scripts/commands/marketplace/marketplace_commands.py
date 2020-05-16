from discord.ext import commands

import scripts.commands.marketplace.marketplace_f as marketplace_f

# Marketplace cog
class Marketplace(commands.Cog):
    def __init__(self, eventChannel):
        self.eventChannel = eventChannel

    # marketplace group
    @commands.group(aliases=["market", "store"])
    async def marketplace(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("{}, Invalid command, use `>help` instead.".format(ctx.author.mention))

    @marketplace.command()
    async def sell(self, ctx, *args):
        code = marketplace_f.sell_f(ctx.author, args)
        if code == -1:
            await ctx.send("{}, the sell commands must take as argument 3 elements: `category`, `item data` (as text) and `price`".format(ctx.author.mention))
        elif code == -2:
            await ctx.send("{}, this category does not exist".format(ctx.author.mention))
        elif code == -3:
            await ctx.send("{}, the `price` argument must be an integer.".format(ctx.author.mention))
        elif code == -4:
            await ctx.send("{}, the `price` argument must be a positive integer".format(ctx.author.mention))
        elif code == -5:
            await ctx.send("{}, the `item data` argument is badly formatted, check `>help`.".format(ctx.author.mention))
        elif code == -6:
            await ctx.send("{}, you can't sell this item.".format(ctx.author.mention))
        else:
            embed = code
            await ctx.send("", embed=embed)

    @marketplace.command()
    async def list(self, ctx, *args):
        code = marketplace_f.list_f(ctx, args)
        if code == -1:
            await ctx.send("{}, you can put at most 1 page number per query.".format(ctx.author.mention))
        elif code == -2:
            await ctx.send("{}, this search returned no items.".format(ctx.author.mention))
        else:
            embed = code
            await ctx.send("", embed=embed)

    @marketplace.command()
    async def cancel(self, ctx, itemID):
        code = marketplace_f.cancel_f(ctx.author, itemID)
        if code == -1:
            await ctx.send("{}, the itemID must be an integer greater or equal than zero.".format(ctx.author.mention))
        elif code == -2:
            await ctx.send("{}, this item ID did not return any items.".format(ctx.author.mention))
        elif code == -3:
            await ctx.send("{}, you can't cancel a sale if it's not yours.".format(ctx.author.mention))
        elif code == 0:
            await ctx.send("{}, the sale {} was successfully cancelled.".format(ctx.author.mention, itemID))

    @marketplace.command()
    async def buy(self, ctx, itemID):
        code = marketplace_f.buy_f(ctx.author, itemID)
        if code == -1:
            await ctx.send("{}, the itemID must be an integer greater or equal than zero.".format(ctx.author.mention))
        elif code == -2:
            await ctx.send("{}, this item ID did not return any items.".format(ctx.author.mention))
        elif code == -3:
            await ctx.send("{}, you can't buy your own item.".format(ctx.author.mention))
        elif code == -4:
            await ctx.send("{}, you don't have enough money to buy this".format(ctx.author.mention))
        else:
            embed = code
            await ctx.send("", embed=embed)
