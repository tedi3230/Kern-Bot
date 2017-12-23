import traceback
from datetime import datetime
from os import environ
from random import choice
from asyncio import sleep #Timed Commands
import traceback

import discord
from discord.ext import commands

import database_old as db #Database Mangament

"""Add to your server with: https://discordapp.com/oauth2/authorize?client_id=380598116488970261&scope=bot


ADD BAN OPTIONS

https://github.com/Rapptz/discord.py/blob/rewrite/discord/ext/commands/formatter.py#L126%3E
?tag formatter
bot.remove_command("help")

https://gist.github.com/MysterialPy/d78c061a4798ae81be9825468fe146be
"""

prefix = "k "

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
        return prefix

    prefixes = [prefix, db.get_prefix(ctx.guild.id)]

    return commands.when_mentioned_or(*prefixes)(bots, ctx)

initial_extensions = ['dictionary', #database
                      'contests',
                      'misc',
                      'settings']



bot = commands.Bot(command_prefix=server_prefix,
                   description='Multiple functions, including contests, definitions, and more.')

try:
    token = environ["AUTH_KEY"]
except KeyError:
    with open("client_secret.txt", encoding="utf-8") as file:
        lines = [l.strip() for l in file]
        token = lines[0]

bot_logs = None
time_format = '%H:%M:%S UTC on the %d of %B, %Y'
#pylint: disable-msg=w0603
#pylint: disable-msg=w0702
@bot.event
async def on_ready():
    global bot_logs
    bot_logs = bot.get_channel(382780308610744331)
    if __name__ == '__main__':
        for extension in initial_extensions:
            try:
                bot.load_extension(extension)
            except:
                print(f'Failed to load extension {extension}.')
                traceback.print_exc()
    await bot.change_presence(status=discord.Status.online)
    print('\nLogged in as:')
    print(bot.user.name, "(Bot)")
    print(bot.user.id)
    print('------')
    await bot.user.edit(username="Kern")
    await bot_logs.send("Bot Online at {}".format(datetime.utcnow().strftime(time_format)))
    bot.loop.create_task(statusChanger())


@bot.event
async def statusChanger():
    status_messages = [discord.Game(name="for new contests.", type=3),
                       discord.Game(name="{} servers.".format(len(bot.guilds)), type=3)]
    while not bot.is_closed():
        message = choice(status_messages)
        await bot.change_presence(game=message)
        await sleep(60)

@bot.event
async def on_command_error(ctx, error):
    owner = (await bot.application_info()).owner
    # This prevents any commands with local handlers being handled here in on_command_error.
    if hasattr(ctx.command, 'on_error'):
        return

    ignored = (commands.CommandNotFound, commands.UserInputError)

    error = getattr(error, 'original', error)

    if isinstance(error, ignored):
        return

    elif isinstance(error, TypeError):
        if ctx.command == "set":
            await ctx.send("Not all required arguments were passed.")

    else:
        await ctx.send("Something went wrong. The error has been reported and hopefully will be fixed. In the meantime, check your arguments for any errors.")

    await bot_logs.send("{}\nIgnoring exception in command {}:```diff\n-{}: {}```".format(owner.mention, ctx.command, type(error).__qualname__, error))
    print('Ignoring exception in command `{}`:'.format(ctx.command))
    traceback.print_exception(type(error), error, error.__traceback__)

try:
    bot.run(token, reconnect=True)
except (KeyboardInterrupt, EOFError):
    pass
