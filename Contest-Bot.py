import discord
import ast
from discord.ext import commands
import pickle
from DB_Access import *
from os import execv,getenv
from sys import argv,executable
from asyncio import sleep
from random import choice
'''Add to your server with: https://discordapp.com/oauth2/authorize?client_id=380598116488970261&scope=bot'''

modelmat = discord.Object(id=310316666171162626)

def server_prefix(bot, message):
    """A callable Prefix for our bot. This could be edited to allow per server prefixes."""
    
    # Notice how you can use spaces in prefixes. Try to keep them simple though.
    prefix = getPrefix(message.guild.id)

    # Check to see if we are outside of a guild. e.g DM's etc.
    if not message.guild:
        # Only allow ? to be used in DMs
        return 'c!'

    # If we are in a guild, we allow for the user to mention us or use any of the prefixes in our list.
    return commands.when_mentioned_or(prefix)(bot, message)

bot = commands.Bot(command_prefix=server_prefix, description='Creates, manages and votes for contests in servers.')
Client = discord.Client()

token = getenv("AUTH_KEY")

if token == None:
    tokenFile = open('client_secret.txt', mode='r')
    token = tokenFile.read()
    tokenFile.close()

def generateEmbed(messageAuthor,title,colour,description,imageURL,footerText):
    embed = discord.Embed(title="Submission by:", description=messageAuthor.mention, colour=colour)
    embed.add_field(name="Title:", value=title, inline=False)
    embed.add_field(name="Description:", value=description, inline=False)
    embed.set_image(url=imageURL)
    embed.set_footer(text=footerText)
    embed.set_thumbnail(url=messageAuthor.avatar_url)
    return embed

class InvalidParameter(Exception):
    pass

@bot.event
async def on_ready():
    print('\nLogged in as:')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    bot.loop.create_task(statusChanger())

@bot.event
async def statusChanger():
    status_messages = [discord.Game(name="for new contests.",type=3),discord.Game(name="{} servers.".format(getNumServers()),type=3),discord.Game(name="for new contests.",type=3)]
    while not bot.is_closed:
        message = choice(status_messages)
        await bot.change_presence(game=message)
        await sleep(60)

@bot.command(hidden=True)
async def restart(ctx):
    """Owner of this bot only command; Restart the bot"""
    if ctx.author == modelmat:
        await ctx.send("Restarting Bot.")
        await bot.logout()
        execv(executable,['py'] + argv)
    else:
        #owner = discord.id
        await ctx.send("You are not {}".format(modelmat.mention))

@bot.command(hidden=True)
async def shutdown(ctx):
    """Owner of this bot only command; Shutdown the bot"""
    if ctx.author == modelmat:
        await ctx.send("Shutting Down.")
        await bot.close()

@bot.group(invoke_without_command=True)
async def settings(ctx):
    """Change and manage all settings of this bot"""
    await ctx.send("For commands, type `!help settings set` or `!help settings get ")
    # no subcommand invoked, just [p]settings

@settings.group(invoke_without_command=True,name="get")
async def settings_get(ctx):
    await ctx.send("For commands, type !help settings get")

@settings.group(invoke_without_command=True,name="set")
async def settings_set(ctx):
    await ctx.send("For commands, type !help settings set")

@settings_get.command(name="channels")
async def settings_get_channels(ctx): 
    channels = getServerChannels(ctx.guild.id,0)
    if len(channels) == 3:
        await ctx.send("​Channels for {}: <#{}>, <#{}>, and <#{}>.".format(ctx.guild.name,channels[0],channels[1],channels[2]))
    else:
        print(channels)
        await ctx.send("​This server does not have channels set up yet, use !settings channels set <receiveChannel> <allowChannel> <outputChannel>.")

@settings_set.command(name="channels")
async def settings_set_channels(ctx, *args):
    if len(args) != 3:
        raise IncorrectNumOfArguments("Too many/little channels supplied, only 3 required.")
    receiveChannelID = args[0].translate({ord(c): None for c in '<>#'})
    allowChannelID = args[1].translate({ord(c): None for c in '<>#'})
    outputChannelID = args[2].translate({ord(c): None for c in '<>#'})
    setServerChannels(ctx.guild.id,receiveChannelID, allowChannelID, outputChannelID)
    await ctx.send("​Set channels to {} {} {}".format(args[0], args[1], args[2]))

@settings_set.command(name="prefix")
async def settings_set_prefix(ctx, prefix):
    bot = commands.Bot(command_prefix=prefix)
    setPrefix(ctx.guild.id,prefix)
    await ctx.send("Set prefix to `{}`".format(prefix))

@settings_get.command(name="prefix")
async def settings_get_prefix(ctx):
    await ctx.send("Prefix for {}: `{}`".format(ctx.guild.name,getPrefix(ctx.guild.id)))

@settings.error
async def settings_error_handler(ctx,error):
    if isinstance(error,InvalidParameter):
        ctx.send(str(error))
    elif isinstance(error,IncorrectNumOfArguments):
        ctx.send(str(error))
    else:
        ctx.send("Warning:\n{}".format(str(error)))

@bot.command()
async def submit(ctx, title, imageURL, *, description):
    """Submits items into the contest. Enclose title & imageURL in quotes."""
    submissionID = generateID() 
    footerText = "Type !allow {} to allow this and !allow {} False to prevent the moving on this to voting queue.".format(submissionID,submissionID)
    embed = generateEmbed(ctx.author,title,0x00ff00,description,imageURL,footerText)
    print(getServerChannels(ctx.guild.id, 1))
    if ctx.channel.id == getServerChannels(ctx.guild.id, 1):
        channel = ctx.guild.get_channel( getServerChannels( ctx.guild.id, 2 ) )
        messageID = await channel.send(embed=embed)
        addSubmission(submissionID,embed,messageID.id)

@submit.error
async def submit_error_handler(ctx,error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You did not pass all the required arguments, please try again.")
    else:
        await ctx.send("​Submit Warning:\n%s"%str(error))

@bot.command()
async def allow(ctx,submissionID,allowed="True"):
    """Allows for moderators to approve/disaprove submissions."""
    if allowed.lower() == "true":
        embed = getSubmission(submissionID)
        embed.set_footer(text="Type !vote {} 0 to not like it, type !vote {} 5 to really like it.".format(submissionID,submissionID))
        await ctx.send(embed=embed)
    elif allowed.lower() == "false":
        embed = getSubmission(submissionID)
        await ctx.send("​Submssions with submissionID of {} has been disapproved.".format(submissionID))
        channel = ctx.guild.get_channel( getServerChannels( ctx.guild.id, 2 ) )
        message = await channel.get_message( getServerChannels(ctx.message.guild.id, 2) )
        embed.colour = 0xff0000
        await message.edit(embed=embed)
        removeSubmission(submissionID)
    else:
        await ctx.send("​A correct value of true/false was not passed ")

@allow.error
async def allow_error_handler(ctx,error):
    if isinstance(error, SubmissionNotExist):
        await ctx.send(str(error))
    else:
        await ctx.send("​Warning:\n%s"%str(error))

try:
    bot.run(token)
except (KeyboardInterrupt, EOFError):
    pass