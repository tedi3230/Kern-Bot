import discord
import ast
from discord.ext import commands

'''Add to your server with: https://discordapp.com/oauth2/authorize?client_id=380295391012192256&scope=bot'''

bot = commands.Bot(command_prefix='!', description='Allows for the creation of contests that can be used in servers.')
Client = discord.Client()

token = open('client_secret.txt', mode='r').read()
serverSettingsFile = open('serverSettings.txt','r+')
serverSettings = ast.literal_eval(serverSettingsFile.read())
serverSettingsFile.close()

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command(pass_context=True)
async def submit(ctx, title, imageURL, *, description):
    """Submits Contest Item"""    
    embed = discord.Embed(title="Submission by", description=str(ctx.message.author), color=0x00ff00)
    embed.add_field(name="Title:", value=title, inline=False)
    embed.add_field(name="Description:", value=description, inline=False)
    embed.set_image(url=imageURL)
    for server, channelList in serverSettings.items():
        if ctx.message.channel.server.id == server:
            if ctx.message.channel.id == channelList[1]:
                await bot.send_message(discord.Object(id=channelList[0]),embed=embed)

bot.run(token)
