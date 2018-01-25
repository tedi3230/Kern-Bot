from datetime import datetime
from os import environ
import traceback
import asyncio
from random import choice

import discord
from discord.ext import commands

import database as db
import custom_classes as cc

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
        prefix = await bots.database.get_prefix(message)
        bots.server_prefixes[message.guild.id] = prefix
    else:
        prefix = bots.server_prefixes[message.guild.id]

    prefixes = [bots.prefix + " ", prefix + " ", bots.prefix, prefix]

    return commands.when_mentioned_or(*prefixes)(bots, message)

bot = cc.Bot(command_prefix=server_prefix,
             description='Multiple functions, including contests, definitions, and more.')

try:
    token = environ["AUTH_KEY"]
except KeyError:
    with open("client_secret.txt", encoding="utf-8") as file:
        lines = [l.strip() for l in file]
        token = lines[0]

async def load_extensions(bots):
    await asyncio.sleep(2)
    for extension in bots.exts:
        try:
            bots.load_extension("cogs." + extension)
        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.')
            traceback.print_exc()
            await bot.close()

@bot.event
async def on_connect():
    bot.database = db.Database(bot)

@bot.event
async def on_guild_join(guild: discord.Guild):
    e = discord.Embed(title="Joined {}".format(guild.name), description=datetime.utcnow().strftime(bot.time_format), colour=discord.Colour.green())
    await bot.get_channel(bot.bot_logs_id).send(embed=e)

@bot.event
async def on_ready():
    await load_extensions(bot)
    await bot.change_presence(status=discord.Status.online)
    bot.owner = (await bot.application_info()).owner
    await bot.user.edit(username="Kern")
    e = discord.Embed(title="Bot Online:", description=datetime.utcnow().strftime(bot.time_format), colour=discord.Colour.green())
    await bot.get_channel(bot.bot_logs_id).send(embed=e)
    bot.loop.create_task(status_changer())
    print('\nLogged in as:')
    print(bot.user.name, "(Bot)")
    print(bot.user.id)
    print('------')

async def status_changer():
    status_messages = [discord.Game(name="for new contests.", type=3),
                       discord.Game(name="{} servers.".format(len(bot.guilds)), type=3)]
    while not bot.is_closed():
        message = choice(status_messages)
        await bot.change_presence(game=message)
        await asyncio.sleep(60)

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
                        failed_to_run[msg.strip(ctx.prefix)] = "Command not found."
                    else:
                        pass

            if failed_to_run:
                errors = ""
                for fail, reason in failed_to_run.items():
                    errors += f"{fail}: {reason}\n"
                await ctx.error(f"```{errors}```", "These failed to run:")

        else:
            ctx = await bot.get_context(message, cls=cc.CustomContext) #is a command returned
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
    ignored = (commands.UserInputError, commands.NotOwner, commands.CheckFailure)

    error = getattr(error, 'original', error)
    if isinstance(error, ignored):
        return

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.error(ctx.error, "Missing Required Argument(s)")

    elif isinstance(error, commands.CommandNotFound):
        print("Command: {} not found.".format(ctx.invoked_with))
        return

    elif isinstance(error, TypeError) and ctx.command in ["set", "get"]:
        pass

    elif isinstance(error, asyncio.TimeoutError) and ctx.command in ['obama', 'meaning', 'synonym', 'antonym']:
        pass

    elif isinstance(error, ModuleNotFoundError):
        await ctx.error(str(error).split("'")[1].capitalize(), "Cog not found:")
        do_send = False
        print("Cog failed to unload.")

    elif isinstance(error, discord.errors.HTTPException):
        if "Invalid Form Body" in str(error):
            pass

    elif isinstance(error, bot.ResponseError):
        await ctx.error(error, "Response Code > 400:")

    elif isinstance(error, ValueError):
        if ctx.command in ['vote']:
            await ctx.error(error, "Error while voting: ")

    else:
        await ctx.error("```{}: {}```".format(type(error).__qualname__, error), title=f"Ignoring exception in command *{ctx.command}*:", channel=bot.get_channel(bot.bot_logs_id))
        print('Ignoring {} in command {}'.format(type(error).__qualname__, ctx.command))
        traceback.print_exception(type(error), error, error.__traceback__)
        do_send = False

    if do_send:
        print('Ignoring {} in command {}'.format(type(error).__qualname__, ctx.command))


bot.run(token, reconnect=True)