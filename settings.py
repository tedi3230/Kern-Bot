import discord
from discord.ext import commands
import database_old as db

class Settings:
    def __init__(self, bot):
        self.bot = bot

    # async def settings_perm_check(self, ctx):
    #     if commands.is_owner():
    #         print("owner")
    #         return True
    #     elif commands.has_permissions(manage_server=True):
    #         print("manage server")
    #         return True
    #     else:
    #         return False

    @commands.group()
    async def get(self, ctx):
        await ctx.send("For commands, type _help settings get")

    @commands.check(settings_perm_check)
    @commands.group(name="set")
    async def _set(self, ctx):
        await ctx.send("For commands, type _help settings set")

    @get.command(name="channels")
    async def get_channels(self, ctx):
        channels = db.get_server_channels(ctx.guild.id)
        if len(channels) == 3:
            await ctx.send("​Channels for {}: <#{}>, <#{}>, and <#{}>.".format(ctx.guild.name,
                                                                               channels[0],
                                                                               channels[1],
                                                                               channels[2]))
        else:
            print(channels)
            await ctx.send("​This server does not have channels set up yet, use c!settings channels set <receiveChannel> <allowChannel> <outputChannel>.")

    @_set.command(name="channels")
    async def set_channels(self, ctx, *args):
        if len(args) < 3:
            raise TypeError("Too few channels supplied, you need three. Type c!help settings set channels for more inforamtion")
        print(args)
        receiveChannelID = args[0].translate({ord(c): None for c in '<>#'})
        allowChannelID = args[1].translate({ord(c): None for c in '<>#'}) #UPDATE FOR NEW SYNTAX
        outputChannelID = args[2].translate({ord(c): None for c in '<>#'})
        db.set_server_channels(ctx.guild.id, receiveChannelID, allowChannelID, outputChannelID)
        await ctx.send("​Set channels to {} {} {}".format(args[0], args[1], args[2]))

    @_set.command(name="prefix")
    async def set_prefix(self, ctx, prefix):
        if db.set_prefix(ctx.guild.id, prefix): 
            await ctx.send("Channels are not set. Currently a limitation.")
        await ctx.send("Set prefix to `{}`".format(db.get_prefix(ctx.guild.id)))

    @get.command(name="prefix")
    async def get_prefix(self, ctx):
        await ctx.send("Prefix for {}: `{}`".format(ctx.guild.name, db.get_prefix(ctx.guild.id)))

    @get.error
    async def get_error_handler(self, ctx, error):
        if isinstance(error, TypeError):
            ctx.send(str(error))
        else:
            ctx.send("Warning:\n{}".format(str(error)))

    @_set.error
    async def set_error_handler(self, ctx, error):
        if isinstance(error, TypeError):
            ctx.send(str(error))
        else:
            ctx.send("Warning:\n{}".format(str(error)))

    @commands.is_owner()
    @get.command(hidden=True)
    async def permissions(self, ctx):
        await ctx.send()

def setup(bot):
    bot.add_cog(Settings(bot))
