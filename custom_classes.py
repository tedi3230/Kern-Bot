from urllib.parse import urlparse
from os import listdir
from os.path import isfile, join
from datetime import datetime
from collections import OrderedDict
import asyncio
import warnings
from concurrent.futures import FIRST_COMPLETED
from random import choice
import async_timeout

import aiohttp

import discord
from discord.ext import commands

async def bot_user_check(ctx):
    return not ctx.author.bot


class MessageExceededMaxLength(Warning):
    pass


class KernBot(commands.Bot):
    def __init__(self, prefix, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database = None
        self.prefix = prefix
        self.server_prefixes = {}
        self.time_format = '%H:%M:%S UTC on the %d of %B, %Y'
        self.bot_logs_id = 382780308610744331
        self.launch_time = datetime.utcnow()
        self.latest_message_time = None
        super().add_check(bot_user_check)
        self.exts = OrderedDict()
        self.statistics = {'market_price':{}, 'coins':[]}
        for e in sorted([extension for extension in [f.replace('.py', '') for f in listdir("cogs") if isfile(join("cogs", f))]]):
            self.exts[e] = True
        loops = asyncio.get_event_loop()
        loops.run_until_complete(self.init())
        self.status_task = self.loop.create_task(self.status_changer())


    async def init(self):
        self.session = aiohttp.ClientSession()
        with async_timeout.timeout(30):
            async with self.session.get("https://min-api.cryptocompare.com/data/all/coinlist") as resp:
                self.statistics['coins'] = {k.upper():v for k, v in (await resp.json())['Data'].items()}

    async def suicide(self, message="Shutting Down"):
        ch = self.get_channel(self.bot_logs_id)
        em = discord.Embed(title=f"{message} @ {datetime.utcnow().strftime('%H:%M:%S')}",
                           colour=discord.Colour.red())
        em.timestamp = datetime.utcnow()
        await ch.send(embed=em)
        await self.database.pool.close()
        self.session.close()
        await self.logout()
        self.status_task.cancel()

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
        status_messages = [discord.Game(name="for new contests.", type=3),
                           discord.Game(name=f"{len(self.guilds)} servers.", type=3),
                           discord.Game(name="bot commands", type=2),
                           discord.Game(name=f"prefix {self.prefix}", type=2)]
        while not self.is_closed():
            message = choice(status_messages)
            await self.change_presence(game=message)
            await asyncio.sleep(60)

    def get_emojis(self, *ids):
        emojis = []
        for e_id in ids:
            emojis.append(str(self.get_emoji(e_id)))
        return emojis

    class ResponseError(Exception):
        pass

class CustomContext(commands.Context):
    def clean_prefix(self):
        user = self.bot.user
        prefix = self.prefix.replace(user.mention, '@' + user.name)
        return prefix

    async def __embed(self, title, description, colour, rqst_by, timestamp, channel, *args, **kwargs):
        e = discord.Embed(title=str(title), colour=colour, description=str(description))
        if rqst_by:
            e.set_footer(text="Requested by: {}".format(self.message.author), icon_url=self.message.author.avatar_url)
        if timestamp:
            e.timestamp = datetime.utcnow()
        if channel is None:
            return await self.send(embed=e, *args, **kwargs)
        return await channel.send(embed=e, *args, **kwargs)

    async def error(self, error, title="Error:", *args, channel: discord.TextChannel = None, rqst_by=True, timestamp=True, **kwargs):
        if isinstance(error, Exception):
            if title == "Error:":
                title = error.__class__.__name__
            error = str(error)
        return await self.__embed(title, error, discord.Colour.red(), rqst_by, timestamp, channel, *args, **kwargs)

    async def success(self, success, title="Success:", *args, channel: discord.TextChannel = None, rqst_by=True, timestamp=True, **kwargs):
        return await self.__embed(title, success, discord.Colour.green(), rqst_by, timestamp, channel, *args, **kwargs)

    async def neutral(self, text, title, *args, channel: discord.TextChannel = None, rqst_by=True, timestamp=True, **kwargs):
        return await self.__embed(title, text, discord.Colour.blurple(), rqst_by, timestamp, channel, *args, **kwargs)

    async def send(self, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None):
        new_content = str(content) if content is not None else None
        if new_content and len(new_content) > 2000:
            new_content = new_content[:1960]
            new_content += "..."
            if content.endswith('```'):
                new_content += "```"
            new_content += "\n\n*Output Truncated for Discord*"
            warnings.warn("Message exceeded max length allowed by discord. Cutting message off and sending.",
                          MessageExceededMaxLength)
        return await super().send(new_content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after, nonce=nonce)

class Url(commands.Converter):
    async def convert(self, ctx, argument):
        url = str(argument)
        if not url.startswith('http://'):
            url = "http://" + url
        if "." not in url:
            url += (".com")  # A bad assumption
        url = urlparse(url).geturl()

        return url
