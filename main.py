import traceback
from datetime import datetime
from os import environ
from random import choice
import asyncio

import discord
from discord.ext import commands

import cogs.database_old as db
#import cogs.database as db

"""Add to your server with: https://discordapp.com/oauth2/authorize?client_id=380598116488970261&scope=bot


ADD BAN OPTIONS

"""

def server_prefix(bots, ctx):
    """A callable Prefix for our bot.

    This allow for per server prefixes.

    Arguments:
        bots {discord.ext.commands.Bot} -- A variable that is passed automatically by commands.Bot.
        message {discord.Message} -- Also passed automatically, used to get Guild ID.

    Returns:
        string -- The prefix to be used by the bot for receiving commands.
    """
    if not ctx.guild:
        return bots.prefix

    prefixes = [bot.prefix, db.get_prefix(ctx.guild.id)]

    return commands.when_mentioned_or(*prefixes)(bots, ctx)

initial_extensions = ['dictionary', #database
                      'contests',
                      'misc',
                      'settings',
                      'admin']



bot = commands.Bot(command_prefix=server_prefix,
                   description='Multiple functions, including contests, definitions, and more.')

bot.prefix = "k "

try:
    token = environ["AUTH_KEY"]
except KeyError:
    with open("client_secret.txt", encoding="utf-8") as file:
        lines = [l.strip() for l in file]
        token = lines[0]

bot.time_format = '%H:%M:%S UTC on the %d of %B, %Y'
bot.bot_logs_id = 382780308610744331
bot.launch_time = datetime.utcnow()
#pylint: disable-msg=w0603
#pylint: disable-msg=w0702
@bot.event
async def on_ready():
    if __name__ == '__main__':
        for extension in initial_extensions:
            try:
                bot.load_extension("cogs." + extension)
            except:
                print(f'Failed to load extension {extension}.')
                traceback.print_exc()
    await bot.change_presence(status=discord.Status.online)
    bot.owner = (await bot.application_info()).owner
    print('\nLogged in as:')
    print(bot.user.name, "(Bot)")
    print(bot.user.id)
    print('------')
    await bot.user.edit(username="Kern")
    await bot.get_channel(bot.bot_logs_id).send("Bot Online at {}".format(datetime.utcnow().strftime(bot.time_format)))
    bot.loop.create_task(statusChanger())

@commands.is_owner()
@bot.command(hidden=True, name="reload")
async def reload_cog(ctx, cog_name: str):
    """stuff"""
    bot.unload_extension("cogs." + cog_name)
    print("Cog unloaded.", end=' | ')
    bot.load_extension("cogs." + cog_name)
    print("Cog loaded.")
    await ctx.send("Cog `{}` sucessfully reloaded.".format(cog_name))

@bot.event
async def statusChanger():
    status_messages = [discord.Game(name="for new contests.", type=3),
                       discord.Game(name="{} servers.".format(len(bot.guilds)), type=3)]
    while not bot.is_closed():
        message = choice(status_messages)
        await bot.change_presence(game=message)
        await asyncio.sleep(60)

@bot.event
async def on_command_error(ctx, error):
    # This prevents any commands with local handlers being handled here in on_command_error.
    do_send = True
    if hasattr(ctx.command, 'on_error'):
        return

    ignored = (commands.UserInputError, commands.NotOwner)

    error = getattr(error, 'original', error)

    if isinstance(error, commands.CommandNotFound,):
        print("Command: {} not found.".format(ctx.command))
        return

    elif isinstance(error, ignored):
        return

    elif isinstance(error, TypeError) and ctx.command in ["set", "get"]:
        pass

    elif isinstance(error, asyncio.TimeoutError) and ctx.command in ['obama', 'meaning', 'synonym', 'antonym']:
        pass

    elif isinstance(error, ModuleNotFoundError):
        await ctx.send("Cog not found: `{}`".format(str(error).split("'")[1]))
        do_send = False
        print("Cog failed to unload.")

    elif isinstance(error, discord.errors.HTTPException) and "Invalid Form Body" in str(error):
        pass

    elif isinstance(error, commands.errors.CommandOnCooldown):
        await ctx.send(":octagonal_sign:This can only be used once every 20 seconds.")

    else:
        await bot.get_channel(bot.bot_logs_id).send("{}\nIgnoring exception in command `{}`:```diff\n-{}: {}```".format(bot.owner.mention, ctx.command, type(error).__qualname__, error))
        print('Ignoring exception in command {}:'.format(ctx.command))
        traceback.print_exception(type(error), error, error.__traceback__)
        return

    if do_send:
        print('Ignoring exception in command {}'.format(ctx.command))

try:
    bot.run(token, reconnect=True)
except (KeyboardInterrupt, EOFError):
    pass
