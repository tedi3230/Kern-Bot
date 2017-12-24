from datetime import datetime
from os import execl
from sys import executable, argv
import inspect
import asyncio

import psutil
import discord
from discord.ext import commands


class Miscellaneous:
    """Miscellaneous functions"""

    def __init__(self, bot):
        self.bot = bot
        self.bot_logs = self.bot.get_channel(bot.bot_logs_id)
        self.bot_launch_time = datetime.utcnow()
        self.bot.remove_command("help")
        self.process = psutil.Process()

    async def on_guild_join(self, guild):
        self.bot_logs.send("Joined {} at {}".format(guild.name, datetime.utcnow().strftime(self.bot.time_format)))

    @commands.is_owner()
    @commands.group(hidden=True, invoke_without_command=True)
    async def delete(self, ctx):
        async for message in ctx.channel.history(limit=100):
            if message.author == self.bot.user:
                await message.delete()
                await ctx.send("Message deleted")
                asyncio.sleep(5)
                await ctx.message.delete()
                return
        ctx.send("No messages were found.")

    @commands.is_owner()
    @delete.command(hidden=True, name="id")
    async def delete_by_id(self, ctx, *, message_id: int):
        msg = await ctx.get_message(message_id)
        if msg.author == self.bot.user:
            await msg.delete()
            await ctx.send("Message deleted")
            asyncio.sleep(5)
            await ctx.message.delete()
        else:
            await ctx.send("The bot did not send that message.")
            asyncio.sleep(5)
            await ctx.message.delete()

    @commands.command(name="help")
    async def _help(self, ctx, command: str = None):
        """Shows this message. Does not display details for each command yet."""
        cogs = {}
        for cmd in self.bot.commands:
            if cmd.hidden:
                continue
            if not cmd.cog_name in cogs:
                cogs[cmd.cog_name] = []
            cogs[cmd.cog_name].append(cmd.qualified_name)

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

    @commands.is_owner()
    @commands.command(hidden=True)
    async def restart(self, ctx):
        """Owner of this bot only command; Restart the bot"""
        if ctx.channel != self.bot_logs:
            await ctx.send("Restarting bot.")
        await self.bot_logs.send("Restarting bot.")
        await self.bot.change_presence(status=discord.Status.offline)
        print("\nRestarting...\n")
        await self.bot.close()
        execl(executable, 'python "' + "".join(argv) + '"')

    @commands.is_owner()
    @commands.command(hidden=True)
    async def shutdown(self, ctx):
        """Owner of this bot only command; Shutdown the bot"""
        if ctx.channel == self.bot_logs:
            await ctx.send("Shutting Down.")
        await self.bot_logs.send("Shutting down bot.")
        await self.bot.change_presence(status=discord.Status.offline)
        print("\nShutting Down...\n")
        await self.bot.close()

    @commands.command()
    async def ping(self, ctx):
        """Returns time taken for a internet packet to go from this bot to discord"""
        await ctx.send("Pong. Time taken: `{:.0f}ms`".format(self.bot.latency * 1000))

    def get_uptime(self):
        delta_uptime = datetime.utcnow() - self.bot_launch_time
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

    @commands.is_owner()
    @commands.command(hidden=True)
    async def leave(self, ctx):
        await ctx.send("Leaving `{}`".format(ctx.guild))
        await ctx.guild.leave()

    @commands.command()
    async def hug(self, ctx, item:str):
        await ctx.send("«{}»".format(item))

    @commands.command()
    async def kiss(self, ctx, item:str):
        await ctx.send(":kiss:{}:kiss:".format(item))

def setup(bot):
    bot.add_cog(Miscellaneous(bot))
