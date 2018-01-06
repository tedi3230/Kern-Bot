import discord
from discord.ext import commands
from urllib.parse import urlparse

class CustomContext(commands.Context):
    def clean_prefix(self, ctx):
        user = ctx.bot.user
        return ctx.prefix.replace(user.mention, '@' + user.name)
    async def error(self, error, title="Error:", channel: discord.TextChannel = None):
        error_embed = discord.Embed(title=title, colour=0xff0000, description=f"{error}")
        if channel is None:
            return await super().send(embed=error_embed)
        return await channel.send(embed=error_embed)

    async def success(self, success, title="Success", channel: discord.TextChannel = None):
        success_embed = discord.Embed(title=title, colour=0x00ff00, description=f"{success}")
        if channel is None:
            return await super().send(embed=success_embed)
        return await channel.send(embed=success_embed)

class ResponseError(Exception):
    pass

class FakeChannel:
    def __init__(self, name):
        self.name = name

class Url(commands.Converter):
    async def convert(self, ctx, argument):
        url = str(argument)
        if not url.startswith('http://'):
            url = "http://" + url
        if "." not in url:
            url += (".com")  # A bad assumption
        url = urlparse(url).geturl()

        return url