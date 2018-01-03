import discord
from discord.ext import commands

async def settings_perm_check(ctx):
    if commands.is_owner():
        return True
    elif commands.has_permissions(manage_server=True):
        return True
    await ctx.send("You do not have valid permissions to do this. (Manage Server Permission).")
    return False

class Settings:
    """Sets and gets the settings for the bot"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def get(self, ctx):
        """Commands related to determining the value of settings."""
        pass

    @commands.check(settings_perm_check)
    @commands.group(name="set")
    async def _set(self, ctx):
        """Commands related to the changing of settings."""
        pass

    @get.command(name="channels")
    async def get_channels(self, ctx):
        """Get the channels used for the contests"""
        channels = (await self.bot.database.get_server_channels(ctx.guild.id))
        if len(channels) == 3:
            await ctx.send("​Channels for {}: <#{}>, <#{}>, and <#{}>.".format(ctx.guild.name, *channels))
        else:
            await ctx.send("​This server does not have channels set up yet, use {}settings channels set <receiveChannel> <allowChannel> <outputChannel>.".format(ctx.prefix))

    @_set.command(name="channels")
    async def set_channels(self, ctx, *channels: discord.TextChannel):
        """Set the channels used for the contests"""
        if len(channels) == 1:
            channels *= 3
        elif len(channels) < 3:
            raise TypeError("Too few channels supplied, you need three. Type `{}help settings set channels` for more information".format(ctx.prefix))
        receiveChannelID, allowChannelID, outputChannelID = [channel.id for channel in channels]
        await self.bot.database.set_server_channels(ctx.guild.id, receiveChannelID, allowChannelID, outputChannelID)
        await ctx.send("​Set channels to {} {} {}".format(*[channel.mention for channel in channels]))

    @_set.command(name="prefix")
    async def set_prefix(self, ctx, *, prefix: str):
        """Set the bot's prefix for this server"""
        prefix = prefix.strip("'").strip('"')
        await ctx.send("Set prefix to `{}`".format(await self.bot.database.get_prefix(ctx.guild.id)))

    @get.command(name="prefix")
    async def get_prefix(self, ctx):
        """Get the bot's prefix for this server"""
        await ctx.send("Prefix for {}: `{}`".format(ctx.guild.name, self.bot.database.get_prefix(ctx.guild.id)))

    @commands.is_owner()
    @get.command(hidden=True)
    async def permissions(self, ctx):
        await ctx.send()

def setup(bot):
    bot.add_cog(Settings(bot))
