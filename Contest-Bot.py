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

def generateEmbed(messageAuthor,color,title,description,imageURL,footerText):
    embed = discord.Embed(title="Submission by", description=messageAuthor, color=color)
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
async def set_config(ctx,receiveChannel,allowChannel,sendChannel):
    print("%s %s %s"%(receiveChannel,allowChannel,sendChannel))

@bot.command(pass_context=True)
async def submit(ctx, title, imageURL, *, description):
    """Submits Contest Item"""
    footerText = "Type !allow %s to allow this and !allow %s False to prevent the moving on this to voting queue."%(ctx.message.id,ctx.message.id)
    embed = generateEmbed(ctx.message.author,0x00ff00,title,description,imageURL,footerText)
    if ctx.message.channel.id == getServerChannels(ctx.message.channel.server.id, "receiveChannelID"):
        #await bot.send_message(discord.Object(id=getServerChannels(ctx.message.channel.server.id, "allowChannelID")),embed=embed)
        await bot.send_message(discord.Object(id=380289087657213952),embed=embed)
        addSubmission(ctx.message.id,pickle.dumps(embed))

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
                # embed = discord.Embed(title="Submission by", description=str(ctx.message.author), color=0x00ff00)
                # embed.add_field(name="Title:", value=title, inline=False)
                # embed.add_field(name="Description:", value=description, inline=False)
                # embed.set_image(url=imageURL)
                #embed.set_footer(text="Type !vote %s yes to allow this and !vote %s False to prevent the moving on this to voting queue."%(ctx.message.id,ctx.message.id))
                embed = pickle.loads()
                await bot.send_message(discord.Object(id=getServerChannels(messageID, "outputChannelID")),"Something not working embed=embed")
            else:
                submissionsFile = open('submissions.txt',"w")
                for line in submissionsLines:
                    if not line.startswith(messageID):
                        submissionsFile.write(line)
                submissionsFile.close()

bot.run(token)
