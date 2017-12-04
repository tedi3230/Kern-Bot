import asyncio
import async_timeout
import aiohttp
from bs4 import BeautifulSoup

import discord
from discord.ext import commands

class DictionaryCog(object):
    def __init__(self, bot, *args):
        self.bot = bot
        self.bot_logs = self.bot.get_channel(382780308610744331)
        try:
            if isinstance(args[0], list):
                self.args = args[0]
            else:
                self.args = args
        except:
            self.args = args
        self.loop = asyncio.get_event_loop()
    
    async def _get_soup_object(self, url):
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(10):
                async with session.get(url) as response:
                    return BeautifulSoup(response.text)

    @commands.command
    async def synonym(self, ctx, term, formatted=False):
        if len(term.split()) > 1:
            print("One word only")
        else:
            try:
                data = self.loop.run_until_complete(self._get_soup_object("http://www.thesarus.com/browse/{}".format(term)))
                terms = data.select("div#filters-0")[0].findAll("li")
                if len(terms) > 5:
                    terms = terms[:5:]
                li = [t.select("span.text")[0].getText() for t in terms]
                if formatted:
                    return {term : li}
                return li
            except: #Get exceptions
                print("No synonyms found for {}".format(term))          

    @commands.command
    async def antonym(self, ctx, term, formatted=False):
        if len(term.split()) > 1:
            print("One word only")
        else:
            try:
                data = self.loop.run_until_complete(self._get_soup_object("http://www.thesarus.com/browse/{}".format(term)))
                terms = data.select("section.antonyms")[0].findAll("div.def-content")
                if len(terms) > 5:
                    terms = terms[:5:]
                li = [t.select("span.text")[0].getText() for t in terms]
                if formatted:
                    return {term : li}
                return li
            except: #Get exceptions
                print("No synonyms found for {}".format(term))

    @commands.command        
    async def meaning(self, ctx, term, formatted=False):
        if len(term.split()) > 1:
            print("One word only")
        else:
            try:
                data = self.loop.run_until_complete(self._get_soup_object("http://www.dictionary.com/browse/{}".format(term)))
                print(data)
                """Figure out how to do it from dictionary.com"""
                terms = data.select("section.luna-box")[0].findAll("def-set")
                if len(terms) > 5:
                    terms = terms[:5:]
                li = [t.select("def-content")[0].getText() for t in terms]
                if formatted:
                    return {term : li}
                return li
            except:
                print("No synonyms found for {}".format(term))  

def setup(bot):
    bot.add_cog(DictionaryCog(bot))