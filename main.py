from datetime import datetime, timedelta
from os import environ, system, execl
import traceback
import asyncio
from sys import version_info, executable, argv
from pkg_resources import get_distribution
import async_timeout
import requests

import discord
from discord.ext import commands

import database as db
import custom_classes as cc

# update: pip install -U git+https://github.com/Modelmat/discord.py@rewrite#egg=discord.py[voice]

async def server_prefix(bots, message):
    """A callable Prefix for our bot.

    This allow for per server prefixes.

    Arguments:
        bots {discord.ext.commands.Bot} -- A variable that is passed automatically by commands.Bot.
        message {discord.Message} -- Also passed automatically, used to get Guild ID.

    Returns:
        string -- The prefix to be used by the bot for receiving commands.
    """
    if not message.guild:
        return bots.prefix

    if bots.server_prefixes.get(message.guild.id) is None:
        guild_prefixes = await bots.database.get_prefix(message)
        bots.server_prefixes[message.guild.id] = list(set(guild_prefixes))
    else:
        guild_prefixes = bots.server_prefixes[message.guild.id]
    prefixes = set()
    for prefix in [bots.prefix, *guild_prefixes]:
        prefixes.update(prefix)
        prefixes.update(prefix + " ")
    print(prefixes)
    return commands.when_mentioned_or(*prefixes)(bots, message)

try:
    token = environ["AUTH_KEY"]
    name = environ["BOT_NAME"]
    bot_prefix = environ["BOT_PREFIX"]
    dbl_token = environ["DBL_TOKEN"]
except KeyError:
    with open("client_secret.txt", encoding="utf-8") as file:
        lines = [l.strip() for l in file]
        token = lines[0]
        name = lines[3]
        bot_prefix = lines[4]
        dbl_token = lines[5]

bot = cc.KernBot(bot_prefix, command_prefix=server_prefix,
                 description='Multiple functions, including contests, definitions, and more.')

var_dict = {}

async def load_extensions(bots):
    await asyncio.sleep(2)
    for extension in bots.exts:
        try:
            bots.load_extension("cogs." + extension)
        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.')
            traceback.print_exc()
            await bot.suicide()

@bot.event
async def on_connect():
    bot.database = db.Database(bot)
    await bot.update_dbots_server_count(dbl_token)
    with async_timeout.timeout(20):
        async with bot.session.get("https://api.github.com/repos/Modelmat/discord.py/commits/rewrite") as r:
            var_dict['sha'] = "g" + (await r.json())['sha'][:7]
        await bot.session.get("https://api.backstroke.co/_88263c5ef4464e868bfd0323f9272d63")

@bot.event
async def on_guild_join(guild: discord.Guild):
    e = discord.Embed(title="Joined {} @ {}".format(guild.name, datetime.utcnow().strftime('%H:%M:%S UTC')),
                      colour=discord.Colour.green(),
                      timestamp=datetime.utcnow())
    await bot.get_channel(bot.bot_logs_id).send(embed=e)
    await bot.update_dbots_server_count(dbl_token)

@bot.event
async def on_guild_remove(guild: discord.Guild):
    e = discord.Embed(title="Left {} @ {}".format(guild.name, datetime.utcnow().strftime('%H:%M:%S UTC')),
                      colour=discord.Colour.red(),
                      timestamp=datetime.utcnow())
    await bot.get_channel(bot.bot_logs_id).send(embed=e)
    await bot.update_dbots_server_count(dbl_token)

@bot.event
async def on_ready():
    await load_extensions(bot)
    await bot.change_presence(status=discord.Status.online)
    bot.owner = (await bot.application_info()).owner
    await bot.user.edit(username=name)
    e = discord.Embed(title=f"Bot Online @ {datetime.utcnow().strftime('%H:%M:%S UTC')}",
                      colour=discord.Colour.green(),
                      timestamp=datetime.utcnow())
    print(f"""
Username: {bot.user.name}
ID:       {bot.user.id}
Bot:      {bot.user.bot}
Guilds:   {len(bot.guilds)}
Members:  {sum(1 for _ in bot.get_all_members())}
Channels: {sum(1 for _ in bot.get_all_channels())}
Python:   {".".join([str(v) for v in version_info[:3]])}
Discord:  {get_distribution('discord.py').version}
Cur. Com: {var_dict['sha']}
---------------
""")

    while bot.get_channel(bot.bot_logs_id) is None:
        asyncio.sleep(1)
    await bot.get_channel(bot.bot_logs_id).send(embed=e)

@bot.event
async def on_resumed():
    if bot.latest_message_time > datetime.utcnow() + timedelta(seconds=30):
        ch = bot.get_channel(bot.bot_logs_id)
        em = discord.Embed(title=f"Resumed @ {datetime.utcnow().strftime('%H:%M:%S')}",
                           description=f"Down since: {datetime.utcnow().strftime(bot.time_format)}",
                           colour=discord.Colour.red())
        await ch.send(embed=em)
    print(bot.latest_message_time)
    print(bot.latest_message_time == datetime.utcnow())
    print(datetime.utcnow() + timedelta(seconds=30))

@bot.event
async def on_socket_raw_receive(_):
    bot.latest_message_time = datetime.utcnow()

@bot.event
async def on_message(message: discord.Message):
    if bot.database is None:
        return
    async with bot.database.lock:
        if " && " in message.content:
            cmds_run_before = []
            failed_to_run = {}
            messages = message.content.split(" && ")
            for msg in messages:
                message.content = msg
                ctx = await bot.get_context(message, cls=cc.CustomContext)
                if ctx.valid:
                    if msg.strip(ctx.prefix) not in cmds_run_before:
                        await bot.invoke(ctx)
                        cmds_run_before.append(msg.strip(ctx.prefix))
                    else:
                        failed_to_run[msg.strip(ctx.prefix)] = "This command has been at least once before."
                else:
                    if ctx.prefix is not None:
                        failed_to_run[msg.strip(
                            ctx.prefix)] = "Command not found."

            if failed_to_run:
                errors = ""
                for fail, reason in failed_to_run.items():
                    errors += f"{fail}: {reason}\n"
                await ctx.error(f"```{errors}```", "These failed to run:")

        else:
            # is a command returned
            ctx = await bot.get_context(message, cls=cc.CustomContext)
            await bot.invoke(ctx)


@commands.is_owner()
@bot.command(name="reload", hidden=True)
async def reload_cog(ctx, cog_name: str):
    """Reload the cog `cog_name`"""
    bot.unload_extension("cogs." + cog_name)
    print("Cog unloaded.", end=' | ')
    bot.load_extension("cogs." + cog_name)
    print("Cog loaded.")
    await ctx.send("Cog `{}` sucessfully reloaded.".format(cog_name))


@bot.event
async def on_command_error(ctx, error):
    # This prevents any commands with local handlers being handled here in on_command_error.
    do_send = True
    if hasattr(ctx.command, 'on_error'):
        return
    #This prevents any
    if ctx.command is not None:
        if hasattr(bot.get_cog(ctx.command.cog_name), '_' + ctx.command.cog_name + '__error'):
            return

    ignored = (commands.UserInputError, commands.NotOwner,
               commands.CheckFailure, commands.CommandNotFound, discord.Forbidden)

    error = getattr(error, 'original', error)
    if isinstance(error, ignored):
        return

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.error(ctx.error, "Missing Required Argument(s)")

    elif isinstance(error, asyncio.TimeoutError):
        await ctx.error("A web request timed out. This is on our end, not yours.", "Timeout Error")

    elif isinstance(error, ModuleNotFoundError):
        await ctx.error(str(error).split("'")[1].capitalize(), "Cog not found:")
        do_send = False
        print("Cog failed to unload.")

    elif isinstance(error, bot.ResponseError):
        await ctx.error(error, "Response Code > 400:")

    elif isinstance(error, ValueError) and ctx.command in ['vote']:
        await ctx.error(error, "Error while voting: ")

    else:
        await ctx.error("```{}: {}```".format(type(error).__qualname__, error), title=f"Ignoring exception in command *{ctx.command}*:", channel=bot.get_channel(bot.bot_logs_id))
        print('Ignoring {} in command {}'.format(type(error).__qualname__,
                                                 ctx.command))
        traceback.print_exception(type(error), error, error.__traceback__)
        do_send = False

    if do_send:
        print('Ignoring {} in command {}'.format(type(error).__qualname__,
                                                 ctx.command))


loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(bot.start(token))
except KeyboardInterrupt:
    loop.run_until_complete(bot.suicide())
