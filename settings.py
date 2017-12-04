import discord
from discord.ext import commands
import database as db

class Settings:
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def settings(self, ctx):
        """Change and manage all settings of this bot"""
        await ctx.send("For commands, type `!help settings set` or `!help settings get`")
        # no subcommand invoked, just [p]settings

    @settings.group(invoke_without_command=True,name="get")
    async def settings_get(self, ctx):
        await ctx.send("For commands, type !help settings get")

    @settings.group(invoke_without_command=True,name="set")
    async def settings_set(self, ctx):
        await ctx.send("For commands, type !help settings set")

    @settings_get.command(name="channels")
    async def settings_get_channels(self, ctx):
        channels = db.get_server_channels(ctx.guild.id)
        if len(channels) == 3:
            await ctx.send("​Channels for {}: <#{}>, <#{}>, and <#{}>.".format(ctx.guild.name,
                                                                               channels[0],
                                                                               channels[1],
                                                                               channels[2]))
        else:
            print(channels)
            await ctx.send("​This server does not have channels set up yet, use c!settings channels set <receiveChannel> <allowChannel> <outputChannel>.")

    @settings_set.command(name="channels")
    async def settings_set_channels(self, ctx, *args):
        if len(args) < 3:
            raise TypeError("Too few channels supplied, you need three. Type c!help settings set channels for more inforamtion")
        print(args)
        receiveChannelID = args[0].translate({ord(c): None for c in '<>#'})
        allowChannelID = args[1].translate({ord(c): None for c in '<>#'}) #UPDATE FOR NEW SYNTAX
        outputChannelID = args[2].translate({ord(c): None for c in '<>#'})
        db.set_server_channels(ctx.guild.id, receiveChannelID, allowChannelID, outputChannelID)
        await ctx.send("​Set channels to {} {} {}".format(args[0], args[1], args[2]))

    @settings_set.command(name="prefix")
    async def settings_set_prefix(self, ctx, prefix):
        db.set_prefix(ctx.guild.id, prefix)
        await ctx.send("Set prefix to `{}`".format(prefix))

    @settings_get.command(name="prefix")
    async def settings_get_prefix(self, ctx):
        await ctx.send("Prefix for {}: `{}`".format(ctx.guild.name, db.get_prefix(ctx.guild.id)))

    @settings.error
    async def settings_error_handler(self, ctx, error):
        if isinstance(error, TypeError):
            ctx.send(str(error))
        else:
            ctx.send("Warning:\n{}".format(str(error)))

def setup(bot):
    bot.add_cog(Settings(bot))
