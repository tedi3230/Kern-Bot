from urllib.parse import urlparse
from signal import SIGTERM
import sys
from os import listdir
from os.path import isfile, join
from datetime import datetime
from collections import OrderedDict
import asyncio
from concurrent.futures import FIRST_COMPLETED
from random import choice
import async_timeout

import aiohttp

import discord
from discord.ext import commands

import database as db

def chunks(s, n):
    for start in range(0, len(s), n):
        yield s[start:start+n]

async def bot_user_check(ctx):
    return not ctx.author.bot


class KernBot(commands.Bot):
    def __init__(self, prefix, *args, **kwargs):
        self.prefix = prefix

        self.session = None
        self.owner = None
        self.latest_message_time = None
        self.latest_commit = None
        self.prefixes_cache = {}

        self.launch_time = datetime.utcnow()
        self.crypto = {
            "market_price" : {},
            "coins": []
        }

        super().__init__(*args, **kwargs)

        self.add_check(bot_user_check)
        self.logs = self.get_channel(382780308610744331)

        self.exts = sorted([extension for extension in [f.replace('.py', '') for f in listdir("cogs") if isfile(join("cogs", f))]])

        self.loop.create_task(self.init())

        self.status_task = self.loop.create_task(self.status_changer())

        try:
            self.loop.add_signal_handler(SIGTERM, lambda: asyncio.ensure_future(self.suicide("SIGTERM Shutdown")))
        except NotImplementedError:
            pass

        self.database = db.Database(self)

    async def init(self):
        self.session = aiohttp.ClientSession()
        with async_timeout.timeout(10):
            async with self.session.get("https://min-api.cryptocompare.com/data/all/coinlist") as resp:
                self.crypto['coins'] = {k.upper():v for k, v in (await resp.json())['Data'].items()}
            async with self.session.get("https://api.backstroke.co/_88263c5ef4464e868bfd0323f9272d63"):
                pass

    async def suicide(self, message="Shutting Down"):
        print(f"\n{message}\n")
        em = discord.Embed(title=f"{message} @ {datetime.utcnow().strftime('%H:%M:%S')}",
                           colour=discord.Colour.red())
        em.timestamp = datetime.utcnow()
        await self.logs.send(embed=em)
        await self.database.pool.close()
        self.session.close()
        await self.close()
        self.status_task.cancel()
        sys.exit(0)

    async def wait_for_any(self, events, checks, timeout=None):
        if not isinstance(checks, list):
            checks = [checks]
        if len(checks) == 1:
            checks *= len(events)
        mapped = zip(events, checks)
        to_wait = [self.wait_for(event, check=check) for event, check in mapped]
        done, _ = await asyncio.wait(to_wait, timeout=timeout, return_when=FIRST_COMPLETED)
        return done.pop().result()

    async def status_changer(self):
        await self.wait_until_ready()
        status_messages = [discord.Activity(name="for new contests.", type=discord.ActivityType.watching),
                           discord.Activity(name=f"{len(self.guilds)} servers.", type=discord.ActivityType.watching),
                           discord.Activity(name="bot commands", type=discord.ActivityType.listening),
                           discord.Activity(name=f"prefix {self.prefix}", type=discord.ActivityType.listening)]
        while not self.is_closed():
            message = choice(status_messages)
            await self.change_presence(activity=message)
            await asyncio.sleep(60)

    def get_emojis(self, *ids):
        emojis = []
        for e_id in ids:
            emojis.append(str(self.get_emoji(e_id)))
        return emojis


    async def update_dbots_server_count(self, dbl_token):
        url = f"https://discordbots.org/api/bots/{self.user.id}/stats"
        headers = {"Authorization": dbl_token}
        payload = {"server_count": len(self.guilds)}
        with async_timeout.timeout(10):
            await self.session.post(url, data=payload, headers=headers)

    class ResponseError(Exception):
        pass

class CustomContext(commands.Context):
    def clean_prefix(self):
        user = self.bot.user
        prefix = self.prefix.replace(user.mention, '@' + user.name)
        return prefix

    async def add_reaction(self, reaction):
        try:
            await self.message.add_reaction(reaction)
        except discord.Forbidden:
            pass

    async def del_reaction(self, reaction):
        try:
            await self.message.remove_reaction(reaction, self.guild.me)
        except discord.Forbidden:
            pass

    async def __embed(self, title, description, colour, rqst_by, timestamp, channel, *args, **kwargs):
        e = discord.Embed(colour=colour)
        if title is not None:
            e.title = str(title)
        if description is not None:
            e.description = str(description)
        if rqst_by:
            e.set_footer(text="Requested by: {}".format(self.message.author), icon_url=self.message.author.avatar_url)
        if timestamp:
            e.timestamp = datetime.utcnow()
        if channel is None:
            return await self.send(embed=e, *args, **kwargs)
        return await channel.send(embed=e, *args, **kwargs)

    async def error(self, error, title="Error:", *args, channel: discord.TextChannel = None, **kwargs):
        if isinstance(error, Exception):
            if title == "Error:":
                title = error.__class__.__name__
            error = str(error)
        return await self.__embed(title, error, discord.Colour.red(), False, False, channel, *args, **kwargs)

    async def success(self, success, title="Success:", *args, channel: discord.TextChannel = None, rqst_by=True, timestamp=True, **kwargs):
        return await self.__embed(title, success, discord.Colour.green(), rqst_by, timestamp, channel, *args, **kwargs)

    async def neutral(self, text, title=None, *args, channel: discord.TextChannel = None, rqst_by=True, timestamp=True, **kwargs):
        return await self.__embed(title, text, discord.Colour.blurple(), rqst_by, timestamp, channel, *args, **kwargs)

    async def warning(self, warning, title=None, *args, channel: discord.TextChannel = None, rqst_by=True, timestamp=True, **kwargs):
        return await self.__embed(title, warning, discord.Colour.blurple(), rqst_by, timestamp, channel, *args, **kwargs)

    async def send(self, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None):
        if content is not None:
            contents = list(chunks(content, 1900)) if content else []
            for cnt in contents[:-1]:
                await super().send(cnt, delete_after=delete_after, tts=tts, nonce=nonce)
            return await super().send(contents[-1], tts=tts, embed=embed, file=file, files=files, delete_after=delete_after, nonce=nonce)
        return await super().send(content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after, nonce=nonce)

class Url(commands.Converter):
    async def convert(self, ctx, argument):
        url = str(argument)
        if "://" not in url:
            url = "https://" + url
        if "." not in url:
            url += (".com")  # A bad assumption
        url = urlparse(url).geturl()

        return url
