from datetime import datetime
import inspect
import re
from collections import OrderedDict
import os

import psutil

import discord
from discord.ext import commands

class Misc:
    """Miscellaneous functions"""
    def __init__(self, bot):
        self.bot = bot
        self.bot_logs = self.bot.get_channel(bot.bot_logs_id)
        self.process = psutil.Process()
        self.bot.remove_command('help')

    @commands.command()
    async def raw(self, ctx, *, message: int = None):
        """Displays the raw code of a message.
        The message can be a message id, some text, or nothing (in which case it will be the most recent message not by you)."""
        msg = None
        if message is not None:
            msg = await ctx.get_message(int(message))
        else:
            async for message in ctx.history(limit=10):
                if message.author == ctx.author:
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
        raw = pattern.sub(replace, msg.content)
        if raw:
            raw = f"​\n{raw}\n​"
        embed_text = str()
        if msg.embeds:
            embed_text += "*Message has {} embed(s).*".format(len(msg.embeds))
        embed = discord.Embed(description=raw + embed_text, timestamp=datetime.utcnow(), colour=discord.Colour.blurple())
        embed.set_footer(text="Requested by: {}".format(ctx.message.author), icon_url=ctx.message.author.avatar_url)
        embed.set_author(name="Message by: {}".format(msg.author), icon_url=msg.author.avatar_url)
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
                        prefix += "⛔"
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
        print(text)

    @commands.command()
    async def source(self, ctx, *, command: str = None):
        """Displays my full source code or for a specific command.
        To display the source code of a subcommand you can separate it by
        periods, e.g. tag.create for the create subcommand of the tag command
        or by spaces.
        """
        source_url = 'https://github.com/Modelmat/Kern-Bot'
        if command is None:
            return await ctx.send(source_url)

        obj = self.bot.get_command(command.replace('.', ' '))
        if obj is None:
            return await ctx.send('Could not find command.')

        # since we found the command we're looking for, presumably anyway, let's
        # try to access the code itself
        src = obj.callback.__code__
        lines, firstlineno = inspect.getsourcelines(src)
        if not obj.callback.__module__.startswith('discord'):
            # not a built-in command
            location = os.path.relpath(src.co_filename).replace('\\', '/')
        else:
            location = obj.callback.__module__.replace('.', '/') + '.py'
            source_url = 'https://github.com/Rapptz/discord.py'

        final_url = f'<{source_url}/blob/master/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>'
        await ctx.send(final_url)

    def make_commands(self):
        cogs_dict = OrderedDict()
        for cog in self.bot.cogs:
            cogs_dict[cog] = cogs_dict.get(cog, []) + [[cmd.name] + cmd.aliases for cmd in self.bot.get_cog_commands(cog) if not cmd.hidden]
        for cmd in self.bot.commands:
            if cmd.cog_name is None and not cmd.hidden:
                cogs_dict['No Category'] = cogs_dict.get('No Category', []) + [[cmd.name] + cmd.aliases]
        cogs_dict = OrderedDict([(key, val) for key, val in cogs_dict.items() if val])
        return cogs_dict

    @commands.command(name="help")
    async def _help(self, ctx, *, command: str = None):
        """Shows this message."""
        cogs_dict = self.make_commands()
        embed = discord.Embed(color=discord.Colour.green())
        if command is None:
            command = "Help"
            embed.description = "{0}\nUse `{1}help command` or `{1}help cog` for further detail.".format(self.bot.description, ctx.clean_prefix())
            for cog, cmds in cogs_dict.items():
                commands_l = []
                for cmd in cmds:
                    if len(cmd) > 1:
                        commands_l += ["{} [{}]".format(cmd[0], ", ".join(cmd[1:]))]
                    else:
                        commands_l += [cmd[0]]
                embed.add_field(name=cog.capitalize(), value=", ".join(commands_l), inline=False)

        elif command.lower() in [cog.lower() for cog in cogs_dict.keys()]:
            #actually a cog
            command = command.capitalize()
            embed.description = inspect.cleandoc(self.bot.get_cog(command).__doc__)
            for cmd in self.bot.get_cog_commands(command):
                if not cmd.hidden:
                    c_help = getattr(cmd, "help", "No description").format(ctx.clean_prefix)
                    embed.add_field(name=cmd.qualified_name, value=c_help, inline=False)

        elif self.bot.get_command(command) in self.bot.commands and not self.bot.get_command(command).hidden:
            cmd_group = self.bot.get_command(command)
            embed.description = cmd_group.help.format(ctx.prefix)
            if isinstance(cmd_group, commands.Group):
                for cmd in cmd_group.commands:
                    if not cmd.hidden:
                        c_help = getattr(cmd, "help", "No description").format(ctx.clean_prefix)
                        embed.add_field(name=cmd.qualified_name, value=c_help, inline=False)

        else:
            embed.description = "The parsed cog or command `{}` does not exist.".format(command)
            command = "Error"

        embed.timestamp = datetime.utcnow()
        embed.set_author(name=command.capitalize(), url="https://discord.gg/bEYgRmc")
        embed.set_footer(text="Requested by: {}".format(ctx.message.author), icon_url=ctx.message.author.avatar_url)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Misc(bot))
