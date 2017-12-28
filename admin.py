from os import execl, path
from sys import executable, argv
import asyncio

import discord
from discord.ext import commands

class Admin:
    """Administration commands."""
    def __init__(self, bot):
        self.bot = bot
        self.bot_logs = self.bot.get_channel(bot.bot_logs_id)

    async def get_path(self):
        path.abspath(__file__)

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
                await asyncio.sleep(5)
                await ctx.message.delete()
                return
        ctx.send("No messages were found.")

    @commands.has_permissions(manage_messages=True)
    @delete.command(hidden=True)
    async def clean(self, ctx, num_messages=200):
        msg_deleted = 0
        async for message in ctx.channel.history(limit=num_messages):
            if msg_deleted % 5 == 0:
                await asyncio.sleep(1)
            if message.author == self.bot.user:
                await message.delete()
                msg_deleted += 1
        msg = await ctx.send("Messages cleaned: `{}/200`".format(msg_deleted))
        await asyncio.sleep(10)
        await msg.delete()

    @commands.is_owner()
    @delete.command(hidden=True, name="id")
    async def delete_by_id(self, ctx, *, message_id: int):
        msg = await ctx.get_message(message_id)
        if msg.author == self.bot.user:
            await msg.delete()
            await ctx.send("Message deleted")
            await asyncio.sleep(5)
            await ctx.message.delete()
        else:
            await ctx.send("The bot did not send that message.")
            await asyncio.sleep(5)
            await ctx.message.delete()

    @commands.is_owner()
    @commands.command(hidden=True)
    async def reload_cog(self, ctx, cog_name: str):
        """stuff"""
        self.bot.remove_cog(cog_name)
        print("Cog unloaded.", end=' | ')
        self.bot.load_extension(cog_name)
        print("Cog loaded.")
        await ctx.send("Cog `{}` sucessfully reloaded.".format(cog_name))

    @commands.is_owner()
    @commands.command(hidden=True)
    async def list_roles(self, ctx):
        roles = [role.name.strip('@').capitalize() for role in ctx.guild.roles]
        await ctx.send(f"Roles in `{ctx.guild.name}`: ```ini\n{roles}```")

    @commands.is_owner()
    @commands.command(hidden=True)
    async def list_permissions(self, ctx, role_name: str=None):
        if role_name is None:
            roles = [role.name.strip('@').capitalize() for role in ctx.guild.me.roles]
            await ctx.send(f"My roles: ```ini\n{roles}```")
        else:
            pass

def setup(bot):
    bot.add_cog(Admin(bot))
