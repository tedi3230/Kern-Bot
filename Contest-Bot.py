import discord
import ast
from discord.ext import commands
import pickle
from DB_Access import *
from atexit import register
'''Add to your server with: https://discordapp.com/oauth2/authorize?client_id=380598116488970261&scope=bot'''

bot = commands.Bot(command_prefix='!', description='Allows for the creation of contests that can be used in servers.')
Client = discord.Client()

tokenFile = open('client_secret.txt', mode='r')
token = tokenFile.read()
tokenFile.close()

def generateEmbed(messageAuthor,title,colour,description,imageURL,footerText):
    embed = discord.Embed(title="Submission by:", description=messageAuthor, colour=colour)
    embed.add_field(name="Title:", value=title, inline=False)
    embed.add_field(name="Description:", value=description, inline=False)
    embed.set_image(url=imageURL)
    embed.set_footer(text=footerText)
    return embed

@register
def cleanUp():
    #await bot.close()
    Client.close()
    cleanUP()

@bot.event
async def on_ready():
    print('Logged in as:')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name="{} servers for new contests.".format(len(bot.servers)),type=3))

@bot.command(pass_context=True)
async def set_channels(ctx,receiveChannel, allowChannel, outputChannel):
    """Defines the server channels for use in the submission of contests."""
    receiveChannelID = receiveChannel.translate({ord(c): None for c in '<>#'})
    allowChannelID = allowChannel.translate({ord(c): None for c in '<>#'})
    outputChannelID = outputChannel.translate({ord(c): None for c in '<>#'})
    setServerChannels(ctx.message.channel.server.id,receiveChannelID, allowChannelID, outputChannelID)
    await bot.say("Set channels to {} {} {}".format(receiveChannel, allowChannel, outputChannel))

@bot.command(pass_context=True)
async def submit(ctx, title, imageURL, *, description):
    """Submits items into the contest. Enclose title & imageURL in quotes."""
    submissionID = generateID() 
    footerText = "Type !allow {} to allow this and !allow {} False to prevent the moving on this to voting queue.".format(submissionID,submissionID)
    embed = generateEmbed(ctx.message.author.mention,title,0x00ff00,description,imageURL,footerText)
    if int(ctx.message.channel.id) == getServerChannels(ctx.message.channel.server.id, "receiveChannelID"):
        messageID = await bot.send_message(discord.Object(id=getServerChannels(ctx.message.channel.server.id, "allowChannelID")),embed=embed)
        addSubmission(submissionID,embed,messageID.id)


# @submit.error
# async def submit_error_handler(error, ctx):
#     if isinstance(error, commands.MissingRequiredArgument):
#         await bot.say("You did not pass all the required arguments, please try again.")
#     else:
#         await bot.say("Submit Warning:\n%s"%str(error))

@bot.command(pass_context=True)
async def allow(ctx,submissionID,allowed="True"):
    """Allows for moderators to approve/disaprove submissions."""
    if allowed.lower() == "true":
        embed = getSubmission(submissionID)
        embed.set_footer(text="Type !vote {} 0 to not like it, type !vote {} 5 to really like it.".format(submissionID,submissionID))
        await bot.send_message(discord.Object(id=getServerChannels(ctx.message.channel.server.id, "outputChannelID")),embed=embed)
    elif allowed.lower() == "false":
        embed = getSubmission(submissionID)
        await bot.say("Submssions with submissionID of {} has been disapproved.".format(submissionID))
        message = await bot.get_message(discord.Object(id=getServerChannels(ctx.message.channel.server.id, "allowChannelID")),getMessageID(submissionID))
        embed.colour = 0xff0000
        await bot.edit_message(message,embed=embed)
        removeSubmission(submissionID)
    else:
        await bot.say("A correct value of true/false was not passed ")

# @allow.error
# async def allow_error_handler(error, ctx):
#     if isinstance(error, SubmissionNotExist):
#         await bot.say(str(error))
#     else:
#         await bot.say("Warning:\n%s"%str(error))
bot.run(token)
