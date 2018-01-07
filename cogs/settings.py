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
        channels = await self.bot.database.get_contest_channels(ctx.guild.id)
        if None in channels:
            await ctx.send("​Channels for {}: <#{}>, <#{}>, and <#{}>.".format(ctx.guild.name, *channels))
        else:
            await ctx.error("Channels are not set up", "Configuration Error:")

    @_set.command(name="channels")
    async def set_channels(self, ctx, *channels: discord.TextChannel):
        """Set the channels used for the contests"""
        if len(channels) == 1:
            channels *= 3
        elif len(channels) < 3:
            raise TypeError(
                "Too few channels supplied, you need to specify 3 or 1. Type `{}help set channels` for more information".format(ctx.prefix))
        receive_channel_id, allow_channel_id, output_channel_id = [
            channel.id for channel in channels]
        await self.bot.database.set_contest_channels(ctx.guild.id, receive_channel_id, allow_channel_id, output_channel_id)
        await ctx.success("​Set channels to {} {} {}".format(*[channel.mention for channel in channels]))

    @_set.command(name="prefix")
    async def set_prefix(self, ctx, *, prefix: str):
        """Set the bot's prefix for this server"""
        prefix = prefix.strip("'").strip('"')
        self.bot.server_prefixes[ctx.guild.id] = prefix
        await ctx.send("Set prefix to `{}`".format(await self.bot.database.set_prefix(ctx.guild.id, prefix)))

    @get.command(name="prefix")
    async def get_prefix(self, ctx):
        """Get the bot's prefix for this server"""
        prefix = self.bot.server_prefixes.get(ctx.guild.id, "k ")
        await ctx.send("Prefix for {}: `{}`".format(ctx.guild.name, prefix))

    @commands.is_owner()
    @get.command(hidden=True)
    async def permissions(self, ctx):
        await ctx.send()


def setup(bot):
    bot.add_cog(Settings(bot))
