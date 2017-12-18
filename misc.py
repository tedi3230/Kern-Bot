from datetime import datetime
from os import execl
from sys import executable, argv

#https://github.com/Rapptz/discord.py/blob/rewrite/discord/ext/commands/formatter.py#L126%3Ex

import discord
from discord.ext import commands

time_format = '%H:%M:%S UTC on the %d of %B, %Y'
        
class Misc:
    def __init__(self, bot):
        self.bot = bot
        self.bot_logs = self.bot.get_channel(382780308610744331)
        self.bot_launch_time = datetime.utcnow().strftime(time_format)
        self.bot.remove_command("help")

    async def on_guild_join(self, guild):
        self.bot_logs.send("Joined {} at {}".format(guild.name, datetime.utcnow().strftime(time_format)))

    @commands.command(name="help")
    async def _help(self, ctx, command : str=None):
        """Shows this message. Does not display details for each command yet."""
        embed = discord.Embed(description=self.bot.description, color=0x00ff00)
        embed.set_author(name="Help", url="https://discord.gg/qWkyxjg")
        embed.set_footer(text="Requested by: {} | {}".format(ctx.message.author, datetime.utcnow().strftime(time_format)), icon_url=ctx.message.author.avatar_url)
        known_cogs = []
        for command in self.bot.commands:
            if command.cog_name not in known_cogs:
                known_cogs.append(command.cog_name)
                cog_commands_length = len([i for i in self.bot.get_cog_commands(command.cog_name) if not i.hidden])
                embed.add_field(name="-----{}-----".format(command.cog_name), value="{} commands".format(cog_commands_length), inline=False)
                for cog_command in self.bot.get_cog_commands(command.cog_name):
                    if not cog_command.hidden:
                        c_help = cog_command.short_doc
                        if c_help == "":
                            c_help = "No information available."
                        embed.add_field(name=cog_command.name, value=c_help, inline=False)
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
        await ctx.send("Pong. Time taken: `{}ms`".format(self.bot.latency * 1000))

    @commands.command()
    async def bot_info(self, ctx):
        """Returns when bot last started."""
        await ctx.send("Latest Build @ {}".format(self.bot_launch_time))

    @commands.is_owner()
    @commands.command(hidden=True)
    async def leave(self, ctx):
        await ctx.send("Leaving `{}`".format(ctx.guild))
        await ctx.guild.leave()

def setup(bot):
    bot.add_cog(Misc(bot))
