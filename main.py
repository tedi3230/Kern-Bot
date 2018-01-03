import traceback
from datetime import datetime
from os import environ
from random import choice
import asyncio

import aiohttp
import discord
from discord.ext import commands

import cogs.database_old as db
#import cogs.database as db

async def bot_user_check(ctx):
    return not ctx.author.bot


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

                      #CHANGE THIS TO USE OS.DIRS> REMEMBER TO FILTER OUT THE __PYCHACHE__ folder



bot = commands.Bot(command_prefix=server_prefix,
                   description='Multiple functions, including contests, definitions, and more.')

bot.add_check(bot_user_check)

bot.todo = """TODO: ```
1. Get a new database working in async, preferably asyncpg
2. Finish contests cog
3. Finish and neaten up the help command (possibly use  HelpFormater). Add docstrings to all commands
4. Hack Command - add fake attack
5. Server rules (database - rules)
6. Custom context
7. Pipe command using || via on_message
8. Stackexchange search - https://api.stackexchange.com/docs
```
"""

bot.prefix = "k "

class ResponseError(Exception):
    pass

bot.ResponseError = ResponseError

class Context(commands.Context):
    async def send_error(self, error, title="Error:", channel: discord.TextChannel=None):
        error_embed = discord.Embed(title=title, colour=0xff0000, description=f"{error}")
        if channel is None:
            return await super().send(embed=error_embed)
        return await channel.send(embed=error_embed)

    async def send_success(self, success, title="Success", channel: discord.TextChannel=None):
        success_embed = discord.Embed(title=title, colour=0x00ff00, description=f"{success}")
        if channel is None:
            return await super().send(embed=success_embed)
        return await channel.send(embed=success_embed)

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

@bot.event
async def on_message(message):
    # implement the pipe commnad
    ctx = await bot.get_context(message, cls=Context)
    await bot.invoke(ctx) #this is bot.process_commands, and so is the above

@commands.is_owner()
@bot.command(hidden=True, name="reload")
async def reload_cog(ctx, cog_name: str):
    """Reload the cog `cog_name`"""

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
    ignored = (commands.UserInputError, commands.NotOwner, commands.CheckFailure)

    error = getattr(error, 'original', error)

    if isinstance(error, ignored):
        return

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

    elif isinstance(error, discord.errors.HTTPException) and "Invalid Form Body" in str(error):
        pass

    elif isinstance(error, bot.ResponseError):
        await ctx.error(error, "Response Code > 400:")

    else:
        ctx.send = bot.get_channel(bot.bot_logs_id).send
        await ctx.error("```{}: {}```".format(type(error).__qualname__, error), title=f"Ignoring exception in command *{ctx.command}*:")
        #await bot.get_channel(bot.bot_logs_id).send("{}\nIgnoring exception in command `{}`:```diff\n-{}: {}```".format(bot.owner.mention, ctx.command, type(error).__qualname__, error))
        print('Ignoring exception in command {}:'.format(ctx.command))
        traceback.print_exception(type(error), error, error.__traceback__)
        return

    if do_send:
        print('Ignoring exception in command {}'.format(ctx.command))

try:
    bot.run(token, reconnect=True)
except (KeyboardInterrupt, EOFError):
    pass
