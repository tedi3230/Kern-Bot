from os import execl
from sys import executable, argv
import asyncio

import discord
from discord.ext import commands

class Administration:
    """Contest functions"""
    def __init__(self, bot):
        self.bot = bot
        self.bot_logs = self.bot.get_channel(bot.bot_logs_id)

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

    @commands.is_owner()
    @commands.command(hidden=True)
    async def leave(self, ctx):
        await ctx.send("Leaving `{}`".format(ctx.guild))
        await ctx.guild.leave()

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

def setup(bot):
    bot.add_cog(Administration(bot))
