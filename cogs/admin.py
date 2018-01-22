from os import execl, system
from sys import executable, argv
import asyncio
import io
import textwrap
from contextlib import redirect_stdout

import discord
from discord.ext import commands

async def message_purge_perm_check(ctx):
    if commands.is_owner():
        return True
    elif commands.has_permissions(manage_messages=True):
        return True
    await ctx.send("You do not have valid permissions to do this. (Manage Messages Permission).")
    return False

class Admin:
    """Administration commands."""
    def __init__(self, bot):
        self.bot = bot
        self.bot_logs = bot.get_channel(bot.bot_logs_id)
        self._last_result = None

    @commands.group(hidden=True)
    async def vps(self, ctx):
        pass

    @commands.is_owner()
    @vps.command()
    async def stop(self, ctx):
        await ctx.send("Stopping VPS instance")
        system('heroku ps:scale worker=0 --app discord-kern-bot')

    @commands.is_owner()
    @vps.command()
    async def start(self, ctx):
        await ctx.send("Starting VPS instance")
        system('heroku ps:scale worker=1 --app discord-kern-bot')

    @commands.is_owner()
    @commands.command(hidden=True)
    async def rebirth(self, ctx):
        """Owner of this bot only command; Restart the bot"""
        if ctx.channel != self.bot_logs:
            await ctx.send("Suciding then being reborn.")
        await self.bot_logs.send("Restarting bot.")
        await self.bot.change_presence(status=discord.Status.offline)
        print("\nRestarting...\n")
        await self.bot.close()
        execl(executable, 'python "' + "".join(argv) + '"')

    @commands.is_owner()
    @commands.command(hidden=True)
    async def suicide(self, ctx):
        """Owner of this bot only command; Shutdown the bot"""
        if ctx.channel != self.bot_logs:
            await ctx.send("Suiciding.")
        await self.bot_logs.send("Shutting down bot.")
        await self.bot.change_presence(status=discord.Status.offline)
        print("\nShutting Down...\n")
        await self.bot.close()

    @commands.is_owner()
    @commands.command(hidden=True)
    async def leave(self, ctx):
        await ctx.send("Leaving `{}`".format(ctx.guild))
        await ctx.guild.leave()

    @commands.check(message_purge_perm_check)
    @commands.group(hidden=True, invoke_without_command=True)
    async def delete(self, ctx):
        async for message in ctx.channel.history(limit=100):
            if message.author == self.bot.user:
                await message.delete()
                await ctx.send("Message deleted")
                await asyncio.sleep(5)

                if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                    await ctx.message.delete()
                return
        await ctx.send("No messages were found.")

    @commands.check(message_purge_perm_check)
    @delete.command(hidden=True)
    async def clean(self, ctx, num_messages=200, old: bool = False):
        def is_me(m):
            return m.author == ctx.guild.me

        if old:
            total_deleted = 0
            if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                deleted = await ctx.channel.purge(limit=num_messages, check=is_me)
                total_deleted += len(deleted)
            deleted = await ctx.channel.purge(limit=num_messages, check=is_me, bulk=False)
            total_deleted += len(deleted)
            await ctx.send("Messages cleaned `{}/{}`".format(total_deleted, num_messages))

        else:
            if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                deleted = await ctx.channel.purge(limit=num_messages, check=is_me)
                await ctx.send("Messages cleaned `{}/{}`".format(len(deleted), num_messages), delete_after=10)
            else:
                await ctx.send(":octagonal_sign: This bot does not have the required permissions to delete messages.\nInstead, use: `{} clean <num_messages> True`".format(ctx.prefix), delete_after=10)

    @commands.check(message_purge_perm_check)
    @delete.command(hidden=True, name="id")
    async def delete_by_id(self, ctx, *message_ids: int):
        for m_id in message_ids:
            msg = await ctx.get_message(m_id)
            if msg.author == self.bot.user:
                await msg.delete()
                await ctx.send("Message deleted")
                if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                    await asyncio.sleep(5)
                    await ctx.message.delete()
            else:
                await ctx.send("The bot did not send that message.")
                if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                    await asyncio.sleep(5)
                    await ctx.message.delete()

    @commands.command(hidden=True)
    async def roles(self, ctx, *, member: discord.Member = None):
        if member is None:
            roles = ", ".join([role.name.strip('@') for role in ctx.guild.roles])
            await ctx.send(f"Roles for `{ctx.guild.name}`:```ini\n[{roles}]```")
        else:
            roles = ", ".join([role.name.strip('@') for role in member.roles])
            await ctx.send(f"Roles for `{member.display_name}`: ```ini\n[{roles}]```")

    @commands.group(hidden=True, aliases=["permissions"])
    async def perms(self, ctx):
        pass

    @perms.command(name="user")
    async def perms_user(self, ctx, *, member: discord.Member, here: str = ""):
        if here == "here":
            perms = ", ".join([perm[0] for perm in ctx.chanel.permissions_for(member) if perm[1]])
            if member == ctx.guild.me:
                await ctx.send(f"My permissions in {ctx.channel.mention}: ```ini\n[{perms}]```")
            elif here == "":
                await ctx.send(f"Permissions for member `{member}` in {ctx.channel.mention}: ```ini\n[{perms}]```")
        else:
            perms = ", ".join([perm[0] for perm in member.guild_permissions if perm[1]])
            if member == ctx.guild.me:
                await ctx.send(f"My permissions: ```ini\n[{perms}]```")
            else:
                await ctx.send(f"Permissions for member `{member}`: ```ini\n[{perms}]```")

    @perms.command(name="role")
    async def perms_role(self, ctx, *, role: discord.Role):
        everyone_perms = [perm for perm in ctx.guild.roles[0].permissions]
        perms = [perm for perm in role.permissions]
        neg_perms = ", ".join([perm[0] for perm in perms if perm[1] == everyone_perms[1]])
        pos_perms = ", ".join([perm[0] for perm in perms if perm[1] != everyone_perms[1]])
        await ctx.send(f"Permissions for role `{role}`: ```ini\n[{pos_perms}]``````css\n[{neg_perms}]```")

    @commands.is_owner()
    @commands.command(hidden=True)
    async def servers(self, ctx):
        await ctx.send("My servers:```ini\n[{}]```".format(", ".join([guild.name for guild in self.bot.guilds])))

    @commands.is_owner()
    @commands.command(hidden=True, name="eval")
    async def k_eval(self, ctx, *, body: str):
        """Evaluates code"""
        def cleanup_code(content):
            if content.startswith('```') and content.endswith('```'):
                return '\n'.join(content.split('\n')[1:-1])

            # remove `foo`
            return content.strip('` \n')

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            try:
                await ctx.message.add_reaction("👎")
            except discord.Forbidden:
                pass
            return await ctx.error(f'```py\n{e}\n```', e.__class__.__name__ + ':')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.error(e, e.__class__.__name__ + ":")
            try:
                return await ctx.message.add_reaction("👎")
            except discord.Forbidden:
                return
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction("👍")
            except discord.Forbidden:
                pass

            if ret is None:
                if value:
                    await ctx.success(f'```py\n{value}\n```', "Returns:")
                    try:
                        await ctx.message.add_reaction("👎")
                    except discord.Forbidden:
                        pass
            else:
                self._last_result = ret
                await ctx.success(f'```py\n{value}{ret}\n```', "Returns:")
                try:
                    await ctx.message.add_reaction("👍")
                except discord.Forbidden:
                    pass

def setup(bot):
    bot.add_cog(Admin(bot))
