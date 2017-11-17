import discord
import ast
from discord.ext import commands
import pickle
from DB_Access import *
'''Add to your server with: https://discordapp.com/oauth2/authorize?client_id=380598116488970261&scope=bot'''

bot = commands.Bot(command_prefix='!', description='Allows for the creation of contests that can be used in servers.')
Client = discord.Client()

tokenFile = open('client_secret.txt', mode='r')
token = tokenFile.read()
tokenFile.close()

def generateEmbed(messageAuthor,title,colour,description,imageURL,footerText):
    embed = discord.Embed(title="Submission by:", description=messageAuthor, color=colour)
    embed.add_field(name="Title:", value=title, inline=False)
    embed.add_field(name="Description:", value=description, inline=False)
    embed.set_image(url=imageURL)
    embed.set_footer(text=footerText)
    return embed

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command(pass_context=True)
async def set_config(ctx,receiveChannel, allowChannel, outputChannel):
    receiveChannelID = receiveChannel.translate({ord(c): None for c in '<>#'})
    allowChannelID = allowChannel.translate({ord(c): None for c in '<>#'})
    outputChannelID = outputChannel.translate({ord(c): None for c in '<>#'})
    setServerChannels(ctx.message.channel.server.id,receiveChannelID, allowChannelID, outputChannelID)
    await bot.say("Set channels to {} {} {}".format(receiveChannel, allowChannel, outputChannel))

@bot.command(pass_context=True)
async def submit(ctx, title, imageURL, *, description):
    """Submits Contest Item"""
    footerText = "Type !allow {} to allow this and !allow {} False to prevent the moving on this to voting queue.".format(ctx.message.id,ctx.message.id)
    embed = generateEmbed(ctx.message.author.mentions,title,0x00ff00,description,imageURL,footerText)
    if int(ctx.message.channel.id) == getServerChannels(ctx.message.channel.server.id, "receiveChannelID"):
        await bot.send_message(discord.Object(id=getServerChannels(ctx.message.channel.server.id, "allowChannelID")),embed=embed)
        addSubmission(ctx.message.id,embed)

# @submit.error
# async def submit_error_handler(error, ctx):
#     if isinstance(error, commands.MissingRequiredArgument):
#         await bot.say("You did not pass all the required arguments, please try again.")
#     else:
#         await bot.say("Warning:\n%s"%str(error))

@bot.command(pass_context=True)
async def allow(messageID,allowed=True):
    submissionsFile = open('submissions.txt',"r+")
    submissionsLines = submissionsFile.readlines()
    submissionsFile.close()
    for line in submissionsLines:
        if line.startswith(messageID):
            if allowed:
                embed = getSubmission(messageID)
                embed.set_footer(text="Type !vote {} 0 to not like it, type !vote {} 5 to really like it.".format(messageID,messageID))
                await bot.send_message(discord.Object(id=getServerChannels(messageID, "outputChannelID")),embed=embed)
            else:
                submissionsFile = open('submissions.txt',"w")
                for line in submissionsLines:
                    if not line.startswith(messageID):
                        submissionsFile.write(line)
                submissionsFile.close()

bot.run(token)
