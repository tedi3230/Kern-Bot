import asyncio
import async_timeout
import aiohttp
from os import environ

import discord
from discord.ext import commands

class Dictionary:
    def __init__(self, bot):
        self.bot = bot
        self.bot_logs = self.bot.get_channel(382780308610744331)
        self.dictionary_URL = 'https://od-api.oxforddictionaries.com/api/v1/entries/en/{}'
        try:
            app_id = environ["APP_ID"]
            app_key = environ["APP_KEY"]
        except KeyError:
            with open("client_secret.txt", encoding="utf-8") as file:
                lines = [l.strip() for l in file]
                app_id = lines[1]
                app_key = lines[2]
        self.headers = {"Accept": "application/json",
                        "app_id": app_id,
                        "app_key": app_key}

    async def _get_dic_request(self, url):
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(10):
                async with session.get(url, headers=self.headers) as response:
                    assert response.status == 200
                    return await response.json()

    @commands.command
    async def synonym(self, ctx, term):
        if len(term.split()) > 1:
            print("One word only")
            return
        data = await self._get_dic_request(self.dictionary_URL.format(term.lower()) + "/synonyms")
        if data is None:
            ctx.send("No antonyms found for {}".format(term))
            return
        results = data['results']          

    @commands.command
    async def antonym(self, ctx, term):
        if len(term.split()) > 1:
            print("One word only")
            return
        data = await self._get_dic_request(self.dictionary_URL.format(term.lower()) + "/antonyms")
        if data is None:
            ctx.send("No antonyms found for {}".format(term))
            return
        results = data['results']
        for i in results:
            print(i)   

    @commands.command
    async def meaning(self, ctx, term):
        if len(term.split()) > 1:
            print("One word only")
            return
        data = await self._get_dic_request(self.dictionary_URL.format(term.lower()))
        if data is None:
            ctx.send("No meanings found for {}".format(term))
            return
        results = data['results']

def setup(bot):
    bot.add_cog(Dictionary(bot))
