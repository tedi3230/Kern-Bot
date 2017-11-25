from os import execl, environ #Getting values off the environment
from sys import argv, executable #Bot Restarting >>> BAD
from asyncio import sleep #Timed Commands
from random import choice
from datetime import datetime
import discord #API
from discord.ext import commands #API
import DB_Access as db #Database Mangament
from PyDictionary import PyDictionary

"""Add to your server with: https://discordapp.com/oauth2/authorize?client_id=380598116488970261&scope=bot"""

def server_prefix(bots, message):
    """A callable Prefix for our bot.

    This allow for per server prefixes.

    Arguments:
        bots {discord.ext.commands.Bot} -- A variable that is passed automatically by commands.Bot.
        message {discord.Message} -- Also passed automatically, used to get Guild ID.

    Returns:
        string -- The prefix to be used by the bot for receiving commands.
    """
    if not message.guild:
        return 'c!'

    prefix = db.get_prefix(message.guild.id)

    return commands.when_mentioned_or(prefix)(bots, message)

bot = commands.Bot(command_prefix=server_prefix,
                   description='Creates, manages and votes for contests in servers.')

try:
    token = environ["AUTH_KEY"]
except KeyError:
    tokenFile = open('client_secret.txt', mode='r')
    token = tokenFile.read()
    tokenFile.close()

#pylint: disable-msg=too-many-arguments
def generateEmbed(messageAuthor, title, description, footerText, imageURL="", colour=0x00ff00):
    """Generates a discord embed object off the given parameters

    Arguments:
        messageAuthor {discord.User} -- Allows for the mention and user's logo to be added to the embed
        title {string} -- Title of the embed, the first heading
        description {string} -- The description of this object
        footerText {string} -- The text shown in the footer, usually for commands that operate upon this

    Keyword Arguments:
        colour {hex} -- Used for the bar on the left's colour (default: {0x00ff00} -- green)
        imageURL {string} -- The image shown at the bottom of the embed. (default: {""} -- no image)

    Returns:
        [discord.Embed] -- The embed object generated.
    """
    embed = discord.Embed(title="Submission by:", description=messageAuthor.mention, colour=colour)
    embed.add_field(name="Title:", value=title, inline=False)
    embed.add_field(name="Description:", value=description, inline=False)
    embed.set_image(url=imageURL)
    embed.set_footer(text=footerText)
    embed.set_thumbnail(url=messageAuthor.avatar_url)
    return embed
#pylint: enable-msg=too-many-arguments
modelmat = None
bot_logs = None
time_format = '%H:%M:%S UTC on the %d of %B, %Y'

@bot.event
async def on_ready():
    global modelmat
    global bot_logs
    modelmat = bot.get_user(310316666171162626)
    bot_logs = bot.get_channel(382780308610744331)
    print('\nLogged in as:')
    print(bot.user.name, "(Bot)")
    print(bot.user.id)
    print('------')
    await bot_logs.send("Bot Online at {}".format(
        datetime.utcnow().strftime(time_format)))
    bot.loop.create_task(statusChanger())

@bot.event
async def on_guild_join(guild):
    bot_logs.send("Joined {} at {}".format(guild.name, datetime.utcnow().strftime(time_format)))

@bot.event
async def statusChanger():
    status_messages = [discord.Game(name="for new contests.", type=3),
                       discord.Game(name="{} servers.".format(len(bot.guilds)), type=3)]
    while not bot.is_closed():
        message = choice(status_messages)
        await bot.change_presence(game=message)
        await sleep(60)

@bot.is_owner
@bot.command(hidden=True)
async def restart(ctx):
    """Owner of this bot only command; Restart the bot"""
    if ctx.channel != bot_logs:
        await ctx.send("Restarting bot.")
    await bot_logs.send("Restarting bot.")
    await bot.close()
    execl(executable, 'python "' + "".join(argv) + '"')

@bot.is_owner
@bot.command(hidden=True)
async def shutdown(ctx):
    """Owner of this bot only command; Shutdown the bot"""
    if ctx.channel == bot_logs:
        await ctx.send("Shutting Down.")
    await bot_logs.send("Shutting down bot.")
    await bot.close()

@bot.group(invoke_without_command=True)
async def settings(ctx):
    """Change and manage all settings of this bot"""
    await ctx.send("For commands, type `!help settings set` or `!help settings get`")
    # no subcommand invoked, just [p]settings

@settings.group(invoke_without_command=True,name="get")
async def settings_get(ctx):
    await ctx.send("For commands, type !help settings get")

@settings.group(invoke_without_command=True,name="set")
async def settings_set(ctx):
    await ctx.send("For commands, type !help settings set")

@settings_get.command(name="channels")
async def settings_get_channels(ctx):
    channels = db.get_server_channels(ctx.guild.id)
    if len(channels) == 3:
        await ctx.send("​Channels for {}: <#{}>, <#{}>, and <#{}>.".format(ctx.guild.name,
                                                                           channels[0],
                                                                           channels[1],
                                                                           channels[2]))
    else:
        print(channels)
        await ctx.send("​This server does not have channels set up yet, use !settings channels set <receiveChannel> <allowChannel> <outputChannel>.")

@settings_set.command(name="channels")
async def settings_set_channels(ctx, *args):
    if len(args) < 3:
        raise TypeError("Too few channels supplied, you need three. Type {}help settings set channels for more inforamtion".format(server_prefix(bot, ctx)))
    receiveChannelID = args[0].translate({ord(c): None for c in '<>#'})
    allowChannelID = args[1].translate({ord(c): None for c in '<>#'}) #UPDATE FOR NEW SYNTAX
    outputChannelID = args[2].translate({ord(c): None for c in '<>#'})
    db.set_server_channels(ctx.guild.id, receiveChannelID, allowChannelID, outputChannelID)
    await ctx.send("​Set channels to {} {} {}".format(args[0], args[1], args[2]))

@settings_set.command(name="prefix")
async def settings_set_prefix(ctx, prefix):
    db.set_prefix(ctx.guild.id, prefix)
    await ctx.send("Set prefix to `{}`".format(prefix))

@settings_get.command(name="prefix")
async def settings_get_prefix(ctx):
    await ctx.send("Prefix for {}: `{}`".format(ctx.guild.name, db.get_prefix(ctx.guild.id)))

@settings.error
async def settings_error_handler(ctx, error):
    if isinstance(error, TypeError):
        ctx.send(str(error))
    else:
        ctx.send("Warning:\n{}".format(str(error)))

@bot.command()
async def submit(ctx, title, imageURL, *, description):
    """Submits items into the contest. Enclose title & imageURL in quotes."""
    submissionID = db.generate_id()
    footerText = "Type !allow {} to allow this and !allow {} False to prevent the moving on this to voting queue.".format(submissionID, submissionID)
    embed = generateEmbed(ctx.author, title, description, footerText, imageURL, 0x00ff00)
    print(db.get_server_channels(ctx.guild.id)[0])
    if ctx.channel.id == db.get_server_channels(ctx.guild.id)[0]:
        channel = ctx.guild.get_channel(db.get_server_channels(ctx.guild.id)[1])
        messageID = await channel.send(embed=embed)
        db.add_submission(submissionID, embed, messageID.id)

@submit.error
async def submit_error_handler(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You did not pass all the required arguments, please try again.")
    else:
        await ctx.send("​Submit Warning:\n%s"%str(error))

@bot.command()
async def allow(ctx, submissionID, allowed="True"):
    """Allows for moderators to approve/disaprove submissions."""
    #CHECK IF SAME SERVER
    embed = db.get_submission(submissionID)
    if allowed.lower() == "true":
        embed.set_footer(text="Type !vote {} 0 to not like it, type !vote {} 5 to really like it.".format(submissionID, submissionID))
        await ctx.send(embed=embed)
    elif allowed.lower() == "false":
        await ctx.send("​Submssions with submissionID of {} has been rejected.".format(submissionID))
        channel = ctx.guild.get_channel(db.get_server_channels(ctx.guild.id)[1])
        message = await channel.get_message(db.get_server_channels(ctx.message.guild.id)[1])
        embed.colour = 0xff0000
        await message.edit(embed=embed)
        db.del_submission(submissionID)
    else:
        await ctx.send("​A correct value of true/false was not passed ")

@allow.error
async def allow_error_handler(ctx, error):
    if isinstance(error, LookupError):
        await ctx.send(str(error))
    else:
        await ctx.send("​Warning:\n%s"%str(error))

dic = PyDictionary()

@bot.command()
async def define(ctx, word):
    ctx.send(dic.meaning(str(word)))

try:
    bot.run(token)
except (KeyboardInterrupt, EOFError):
    pass
