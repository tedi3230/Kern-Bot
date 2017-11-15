import discord
from discord.ext import commands

'''Add to your server with: https://discordapp.com/oauth2/authorize?client_id=380295391012192256&scope=bot'''

description = '''Allows for the creation of contests that can be used in servers.'''
bot = commands.Bot(command_prefix='!', description=description)

token = open('client_secret.txt', mode='r').read()

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def submit_contest_item(*args):
    """Submits Contest Item"""
    await bot.say(' '.join(args))

bot.run(token)