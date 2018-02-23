import discord
from discord.ext import commands

from custom_classes import KernBot

async def manage_server_check(ctx):
    if commands.is_owner():
        return True
    elif commands.has_permissions(manage_server=True):
        return True
    await ctx.error("You do not have valid permissions to do this. (Manage Server Permission).", "Permissions Error")
    return False

class Settings:
    """Sets and gets the settings for the bot"""
    def __init__(self, bot: KernBot):
        self.bot = bot

    async def __error(self, ctx, error):
        print(error)

    @commands.group()
    async def get(self, ctx):
        """Commands related to determining the value of settings."""
        pass

    @commands.check(manage_server_check)
    @commands.group(name="set")
    async def _set(self, ctx):
        """Commands related to the changing of settings."""
        pass

    @get.command(name="channels")
    async def get_channels(self, ctx):
        """Get the channels used for the contests"""
        channels = await self.bot.database.get_contest_channels(ctx)
        if None not in channels:
            await ctx.send("​Channels for {}: <#{}> and <#{}>.".format(ctx.guild.name, *channels))
        else:
            await ctx.error("Channels are not set up", "Configuration Error:")

    @_set.command(name="channels")
    async def set_channels(self, ctx, *channels: discord.TextChannel):
        """Set the channels used for the contests"""
        if len(channels) == 1:
            channels *= 2
        elif len(channels) > 2:
            raise TypeError("set channels takes 2 positional arguments but {} were given".format(len(channels)))
        receive_channel_id, output_channel_id = [channel.id for channel in channels]
        await self.bot.database.set_contest_channels(ctx, receive_channel_id, output_channel_id)
        await ctx.success("​Set channels to {} {}".format(*[channel.mention for channel in channels]))

    @_set.command(name="prefix")
    async def set_prefix(self, ctx, *, prefix: str = None):
        """Set the bot's prefix for this server. Send no prefix to remove."""
        if prefix is not None:
            prefix = prefix.strip("'").strip('"')
            self.bot.server_prefixes[ctx.guild.id] = self.bot.server_prefixes.get(ctx.guild.id, []) + [prefix]
            await ctx.send("Set prefix to `{}`".format(await self.bot.database.set_prefix(ctx, prefix)))
        else:
            await self.bot.database.remove_prefix(ctx)
            await ctx.send("Custom server prefix removed.")

    @get.command(name="prefix")
    async def get_prefix(self, ctx):
        """Get the bot's prefix for this server"""
        prefix = self.bot.server_prefixes.get(ctx.guild.id, self.bot.prefix)
        await ctx.send("Prefix for {}: `{}`".format(ctx.guild.name, prefix))

    @commands.is_owner()
    @get.command(hidden=True)
    async def permissions(self, ctx):
        await ctx.send()

    @_set.command(name="max_rating")
    async def set_max_rating(self, ctx, max_rating: int):
        await self.bot.database.set_max_rating(ctx, max_rating)
        await ctx.success("Max rating set to {}".format(max_rating))

    @get.command(name="max_rating")
    async def get_max_rating(self, ctx):
        max_rating = await self.bot.database.get_max_rating(ctx) or 10
        await ctx.send(f"Max rating is {max_rating}")
        return max_rating


def setup(bot):
    bot.add_cog(Settings(bot))
