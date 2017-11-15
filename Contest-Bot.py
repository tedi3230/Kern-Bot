import discord
from discord.ext import commands

description = '''An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here.'''
bot = commands.Bot(command_prefix='?', description=description)

baseURL = "https://discordapp.com/api/oauth2/authorize"
tokenURL = "https://discordapp.com/api/oauth2/token"
revocationURL = "https://discordapp.com/api/oauth2/token/revoke"

CLIENT_SECRET = open('client_secret.txt', mode='r').read()
CLIENT_ID = open('client_id.txt', mode='r').read()