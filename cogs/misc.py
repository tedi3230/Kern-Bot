from datetime import datetime
from os import environ
import inspect
from asyncio import sleep
from urllib.parse import urlparse
import random

from collections import namedtuple

import aiohttp
import async_timeout
import psutil
from tabulate import tabulate

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

protocols = ['ssh', 'smb', 'smtp', 'ftp', 'imap', 'http', 'https', 'pop', 'htcpcp', 'telnet', 'tcp']

class FakeChannel():
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

class Misc:
    """Miscellaneous functions"""

    def __init__(self, bot):
        self.bot = bot
        self.bot_logs = self.bot.get_channel(bot.bot_logs_id)
        self.bot.remove_command("help")
        self.process = psutil.Process()

        try:
            self.streamable_user = environ["STREAM_USER"]
            self.streamable_password = environ["STREAM_PASS"]
        except KeyError:
            stream_file = open('streamable_secret.txt', mode='r')
            auth = []
            for line in stream_file:
                auth.append(line)
            stream_file.close()
            self.streamable_user = auth[0].strip('\n')
            self.streamable_password = auth[1]

    async def on_guild_join(self, guild):
        self.bot_logs.send("Joined {} at {}".format(guild.name, datetime.utcnow().strftime(self.bot.time_format)))

    @commands.command(name="help")
    async def _help(self, ctx, command: str = None):
        """Shows this message. Does not display details for each command yet."""
        cogs = {}
        for cmd in self.bot.commands:
            if cmd.hidden:
                continue
            if not cmd.cog_name in cogs:
                cogs[cmd.cog_name] = []
            cogs[cmd.cog_name].append(" / ".join([cmd.qualified_name, *cmd.aliases]))

        for cog in cogs:
            cogs[cog] = sorted(cogs[cog])

        if command is None:
            command = "Help"
            embed = discord.Embed(description="{0}\nUse `{1}help command` or `{1}help cog` for further detail.".format(self.bot.description, ctx.prefix), color=0x00ff00)
            for cog in sorted(cogs):
                embed.add_field(name=cog, value="\n".join(cogs[cog]))

        elif command.capitalize() in cogs:
            command = command.capitalize()
            embed = discord.Embed(description=inspect.cleandoc(self.bot.get_cog(command).__doc__), colour=0x00ff00)
            for cmd in self.bot.get_cog_commands(command):
                if not cmd.hidden:
                    embed.add_field(name=cmd.qualified_name, value=cmd.help, inline=False)

        elif self.bot.get_command(command) in self.bot.commands and not self.bot.get_command(command).hidden:
            cmd_group = self.bot.get_command(command)
            embed = discord.Embed(description=cmd_group.help.format(ctx.prefix), color=0x00ff00)
            if isinstance(cmd_group, commands.Group):
                for cmd in cmd_group.commands:
                    if not cmd.hidden:
                        embed.add_field(name=cmd.name, value=cmd.help, inline=True)

        else:
            embed = discord.Embed(description="The parsed cog or command `{}` does not exist.".format(command), color=0xff0000)
            command = "Error"

        embed.timestamp = datetime.utcnow()
        embed.set_author(name=command.capitalize(), url="https://discord.gg/bEYgRmc")
        embed.set_footer(text="Requested by: {}".format(ctx.message.author), icon_url=ctx.message.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        """Returns time taken for a internet packet to go from this bot to discord"""
        await ctx.send("Pong. Time taken: `{:.0f}ms`".format(self.bot.latency * 1000))

    def get_uptime(self):
        delta_uptime = datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        output = str()
        if days > 0:
            output += "{} days\n".format(days)
        if hours > 0:
            output += "{} hours\n".format(hours)
        if minutes > 0:
            output += "{} minutes\n".format(minutes)
        if seconds > 0:
            output += "{} seconds\n".format(seconds)
        return output

    @commands.command(aliases=['stats'])
    async def info(self, ctx):
        """Returns information about the bot."""
        owner = (await self.bot.application_info()).owner

        total_members = sum(1 for _ in self.bot.get_all_members())
        total_servers = len(self.bot.guilds)
        total_channels = sum(1 for _ in self.bot.get_all_channels())
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        ram_usage = self.process.memory_full_info().uss / 1024**2

        embed = discord.Embed(description="Information about this bot.", color=0x00ff00)
        embed.set_author(name=str(owner), icon_url=owner.avatar_url, url="https://discord.gg/bEYgRmc")
        embed.add_field(name="Server Statistics:", value="Guilds: {}\nChannels: {}\nUsers: {}".format(total_servers, total_channels, total_members))
        embed.add_field(name="Resource Usage:", value="CPU: {:.2f} %\nRAM: {:.2f} MiB".format(cpu_usage, ram_usage))
        embed.add_field(name="Uptime:", value=self.get_uptime())
        embed.timestamp = datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command()
    async def hug(self, ctx, item: str):
        await ctx.send("«{}»".format(item))

    @commands.command()
    async def kiss(self, ctx, item: str):
        await ctx.send(":kiss:{}:kiss:".format(item))

    @commands.command()
    async def obama(self, ctx, *, text: str):
        if len(text) - 19 > 280:
            await ctx.send("A maximum character total of 280 is enforced. You sent: `{}` characters".format(len(text)))
            return
        await ctx.trigger_typing()

        async def create_video(text):
            async with aiohttp.ClientSession() as session:
                with async_timeout.timeout(10):
                    async with session.post(url="http://talkobamato.me/synthesize.py", data={"input_text":text}) as page:
                        url = page.url
                        text = await page.text()

            if text.__contains__('<source src="'):
                start = text.index('<source src="') + len('<source src="')
                end = text.index('" type="video/mp4">')
                link = "http://talkobamato.me/" + text[start:end]
                vid_hash = text[start:end].split('/')[2]+".mp4"
                return link

            while True:
                async with aiohttp.ClientSession() as session:
                    with async_timeout.timeout(30):
                        async with session.get(url) as r:
                            text = await r.text()
                if text.__contains__('<source src="'):
                    start = text.index('<source src="') + len('<source src="')
                    end = text.index('" type="video/mp4">')
                    link = "http://talkobamato.me/" + text[start:end]
                    vid_hash = text[start:end].split('/')[2]+".mp4"
                    return link

        async def upload_streamable(url):
            async with aiohttp.ClientSession() as session:
                with async_timeout.timeout(10):
                    async with session.get('https://api.streamable.com/import?url={}'.format(url), auth=aiohttp.BasicAuth(self.streamable_user, self.streamable_password)) as resp:
                        assert resp.status == 200
                        js = await resp.json()
                        return "https://streamable.com/{}".format(js['shortcode'])

        link = await create_video(text)
        url = await upload_streamable(link)
        msg = await ctx.send(url)
        print('sent')
        while True:
            print("hi")
            #NOT WORKING???
            async with aiohttp.ClientSession() as session:
                with async_timeout.timeout(5):
                    async with session.get('https://api.streamable.com/oembed.json?url={}'.format(url)) as resp:
                        assert resp.status == 200
                        js = await resp.json()
                        if js['height'] is not None:
                            print('exiting')
                            msg.edit(content=url+'/')
                            msg.edit(content=url)
                            return
                        print('nope')
            await sleep(10)

    #@commands.cooldown(1, 10, BucketType.channel)
    @commands.command()
    async def hack(self, ctx, *, url: Url):
        "Starts a fake hacking instance on a specified URL."
        loading = str(self.bot.get_emoji(395834326450831370))
        thousands = str(self.bot.get_emoji(396890900783038499))
        hundreds = str(self.bot.get_emoji(396890900158218242))
        tens = str(self.bot.get_emoji(396890900753547266))
        ones = str(self.bot.get_emoji(396890900426653697))
        

        msg = await ctx.send(f"Looking for open ports in <{url}>")

        content = msg.content

        fake_ports = sorted([random.randint(0, 65535) for i in range(random.randint(0, 10))])
        prtcls = [random.choice(protocols) for i in range(len(fake_ports))]
        secures = [random.choice(["'false'", 'true']) for i in range(len(fake_ports))]
        table_data = list(zip(fake_ports, prtcls, secures))
        headers = ["PORT", "PROTOCOL", "SECURE"]
        table = str(tabulate(table_data, headers, tablefmt="rst"))
        open_data = [data[0:2] for data in table_data if data[2]]
        open_ports = ", ".join([str(data[0]) for data in open_data])

        await msg.edit(content=f"{content}\nPort: {thousands}{hundreds}{tens}{ones}{loading}")

        await sleep(10)

        if not table_data:
            await msg.edit(content=f"Port scan complete. No ports found.")
            return

        await msg.edit(content=f"Port scan complete. Scan report: ```ml\n{table}```\n{loading}Attempting to bruteforce open ports: ({open_ports})")

        #Now do fake atatck on unsecure port

    @commands.command()
    async def tree(self, ctx):
        tree = {}
        for channel in ctx.guild.text_channels:
            if channel.category is None:
                channel.category = FakeChannel("No category")
            prefix = "📨 "
            if channel.is_nsfw():
                prefix += "❌ "
            tree[channel.category.name] = [prefix + channel.name] + tree.get(channel.category.name, [])

        for channel in ctx.guild.voice_channels:
            if channel.category is None:
                channel.category.name = "No category"
            tree[channel.category.name] = ["🔈 " + channel.name] + tree.get(channel.category.name, [])

        tree_string = ctx.guild.name + "\n"
        for category, channels in tree.items():
            channels.sort()
            tree_string += f"|-- {category.upper()}\n"
            for channel in channels:
                tree_string += f"|  |--{channel}\n"

        await ctx.send(f"```fix\n{tree_string}```")



def setup(bot):
    bot.add_cog(Misc(bot))
