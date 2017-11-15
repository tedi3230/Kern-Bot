import discord
import ast
from discord.ext import commands

'''Add to your server with: https://discordapp.com/oauth2/authorize?client_id=380295391012192256&scope=bot'''

description = '''Allows for the creation of contests that can be used in servers.'''
bot = commands.Bot(command_prefix='!', description=description)
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
async def submit(ctx, *args):
    """Submits Contest Item"""
    for server, channelList in serverSettings.items():
        if ctx.channel.id == server:
            ctx.chann
    await bot.say(' '.join(args))

bot.run(token)