from datetime import datetime
from os import environ, path
import inspect
from asyncio import sleep
import random
import re

import aiohttp
import async_timeout
import psutil
from tabulate import tabulate

import discord
from discord.ext import commands

import custom_classes as cc

protocols = ['ssh', 'smb', 'smtp', 'ftp', 'imap', 'http', 'https', 'pop', 'htcpcp', 'telnet', 'tcp', 'ipoac']

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
            file_path = path.join(path.dirname(__file__), '../streamable_secret.txt')
            stream_file = open(file_path, mode='r')
            auth = []
            for line in stream_file:
                auth.append(line)
            stream_file.close()
            self.streamable_user = auth[0].strip('\n')
            self.streamable_password = auth[1]

    async def on_guild_join(self, guild):
        self.bot_logs.send("Joined {} at {}".format(guild.name, datetime.utcnow().strftime(self.bot.time_format)))

    @commands.command()
    async def raw(self, ctx, *, message: int = None):
        """Displays the raw code of a message.
        The message can be a message id, some text, or nothing (in which case it will be the most recent message not by you)."""
        msg = None
        if message is not None:
            msg = await ctx.get_message(int(message))
        else:
            async for message in ctx.history(limit=10):
                if msg.author == ctx.author:
                    continue
                msg = message
                break

        if msg is None:
            msg = ctx.message
            msg.content = msg.content.split('raw ')[1]

        transformations = {
            re.escape(c): '\\' + c
            for c in ('*', '`', '_', '~', '\\', '<')
        }

        def replace(obj):
            return transformations.get(re.escape(obj.group(0)), '')

        pattern = re.compile('|'.join(transformations.keys()))
        await ctx.send(f"**Message by: @{msg.author.name} at {0}\n".format(msg.created_at.strftime(self.bot.time_format)) + pattern.sub(replace, msg.content))

    @commands.command(name="help")
    async def _help(self, ctx, command: str = None):
        """Shows this message. Does not display details for each command yet."""
        cogs = {}
        for cmd in self.bot.commands:
            if cmd.hidden:
                continue
            if not cmd.cog_name in cogs:
                cogs[cmd.cog_name] = []
            aliases = ", ".join(cmd.aliases)
            if not aliases:
                cogs[cmd.cog_name].append(cmd.qualified_name)
            else:
                cogs[cmd.cog_name].append("{} [{}]".format(cmd.qualified_name, ", ".join(cmd.aliases)))
        for cog in cogs.copy():
            cogs[cog] = sorted(cogs[cog])

        if command is None:
            command = "Help"
            embed = discord.Embed(description="{0}\nUse `{1}help command` or {1}help cog` for further detail.".format(
                self.bot.description, ctx.clean_prefix()), color=0x00ff00)
            for cog in sorted(cogs):
                embed.add_field(name=cog, value=", ".join(cogs[cog]), inline=False)

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
                        embed.add_field(name=cmd.name, value=cmd.help, inline=False)

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
        """Makes obama speak the text"""
        if len(text) - len(ctx.prefix + "obama") > 280:
            await ctx.send("A maximum character total of 280 is enforced. You sent: `{}` characters".format(len(text)))
            return
        await ctx.trigger_typing()

        async def create_video(text):
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.post(url="http://talkobamato.me/synthesize.py", data={"input_text":text}) as resp:
                        if resp.status >= 400:
                            raise self.bot.ResponseError(f"Streamable upload responded with status {resp.status}")
                        text = await resp.text()
                        url = resp.url

            while '<source src="' not in text:
                async with aiohttp.ClientSession() as session:
                    async with async_timeout.timeout(10):
                        async with session.get(url) as resp:
                            text = await resp.text()

            start = text.index('<source src="') + len('<source src="')
            end = text.index('" type="video/mp4">')
            link = "http://talkobamato.me/" + text[start:end]
            return link

        async def upload_streamable(url):
            async with aiohttp.ClientSession() as session:
                with async_timeout.timeout(10):
                    async with session.get('https://api.streamable.com/import?url={}'.format(url), auth=aiohttp.BasicAuth(self.streamable_user, self.streamable_password)) as resp:
                        if resp.status >= 400:
                            raise self.bot.ResponseError(f"Streamable upload responded with status {resp.status}")
                        js = await resp.json()
                        return "https://streamable.com/{}".format(js['shortcode'])


        link = await create_video(text)
        url = await upload_streamable(link)
        msg = await ctx.send(url)
        while True:
            async with aiohttp.ClientSession() as session:
                with async_timeout.timeout(5):
                    async with session.get('https://api.streamable.com/oembed.json?url={}'.format(url)) as resp:
                        if resp.status >= 400:
                            raise self.bot.ResponseError(f"Streamable upload responded with status {resp.status}")
                        js = await resp.json()
                        if js['height'] is not None:
                            await msg.edit(content=url+'/')
                            await msg.edit(content=url)
                            return
            await sleep(5)

    @commands.command()
    async def hack(self, ctx, *, url: cc.Url):
        "Starts a fake hacking instance on a specified URL."
        loading = str(self.bot.get_emoji(395834326450831370))
        thousands = str(self.bot.get_emoji(396890900783038499))
        hundreds = str(self.bot.get_emoji(396890900158218242))
        tens = str(self.bot.get_emoji(396890900753547266))
        ones = str(self.bot.get_emoji(396890900426653697))

        fake_ports = sorted([random.randint(0, 65535) for i in range(random.randint(0, 10))])
        prtcls = [random.choice(protocols) for i in range(len(fake_ports))]
        secures = [random.choice(["'false'", 'true']) for i in range(len(fake_ports))]
        table_data = list(zip(fake_ports, prtcls, secures))
        headers = ["PORT", "PROTOCOL", "SECURE"]
        table = str(tabulate(table_data, headers, tablefmt="rst"))
        open_data = [data[0:2] for data in table_data if data[2]]
        open_ports = ", ".join([str(data[0]) for data in open_data])

        msg = await ctx.send(f"Looking for open ports in <{url}>")
        content = msg.content
        await msg.edit(content=f"{content}\nPort: {thousands}{hundreds}{tens}{ones}{loading}")
        await sleep(10)

        if not table_data:
            await msg.edit(content=f"Port scan complete. No ports found.")
            return

        await msg.edit(content=f"Port scan complete. Scan report: ```ml\n{table}```\n{loading}Attempting to bruteforce insecure ports: ({open_ports})")

        #Now do fake atatck on unsecure port (note, add a RFC 1149 reference)

    @commands.command()
    async def tree(self, ctx):
        tree_string = ctx.guild.name + "\n"
        cat_list = ctx.guild.by_category()
        for cat_tup in cat_list:
            if cat_tup[0] is not None:
                tree_string += f"|-- {cat_tup[0].name.upper()}\n"
            for channel in cat_tup[1]:
                prefix = str()
                if isinstance(channel, discord.TextChannel):
                    prefix += "📨"
                    if channel.is_nsfw():
                        prefix += "⚠"
                elif isinstance(channel, discord.VoiceChannel):
                    prefix += "🔊"
                tree_string += "|  |--{}\n".format(prefix + " " + channel.name.lower())

        await ctx.send(f"```fix\n{tree_string}```")

    @commands.command()
    async def invite(self, ctx):
        await ctx.send("Add to your server: https://discordapp.com/oauth2/authorize?client_id=380598116488970261&scope=bot")

    @commands.command()
    async def todo(self, ctx):
        await ctx.send(self.bot.todo)

    @commands.is_owner()
    @commands.command(hidden=True)
    async def echo(self, ctx, *, text):
        await ctx.send(text)

def setup(bot):
    bot.add_cog(Misc(bot))
