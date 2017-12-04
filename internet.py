#from .utils import _get_soup_object #NOT correct

"""
Also make the pydictioanry script non-blocking https://github.com/geekpradd/PyDictionary/blob/master/PyDictionary/core.py

https://aiohttp.readthedocs.io/en/stable/

Convert this to a cog
"""

import json
import re
import asyncio
import aiohttp
import async_timeout
from PyDictionary import PyDictionary

async def get_images(URL, parameters=None):
    async with aiohttp.ClientSession() as session:
        with async_timeout.timeout(10):
            async with session.get(URL,params=parameters) as response:
                print(response.url,end="\n\n")
                json_response = json.loads(await response.text())
                return json_response['results']

async def post_search(URL, parameters):
    async with aiohttp.ClientSession() as session:
        with async_timeout.timeout(10):
            async with session.post(URL, data=parameters) as response:
                text_response = await response.text()
        return re.search(r'vqd=(\d+)\&', text_response, re.M|re.I)
        

keywords = "cars"
requestUrl = 'https://duckduckgo.com/i.js'
url = 'https://duckduckgo.com/'

params = {
    'q': keywords
    }

loop = asyncio.get_event_loop()
searchObj = loop.run_until_complete(post_search(url, params))
params = (
    ('l', 'wt-wt'),
    ('o', 'json'),
    ('q', keywords),
    ('vqd', searchObj.group(1)),
    ('f', ',,,'),
    ('p', '2')
)

results = loop.run_until_complete(get_images(requestUrl, params))
imageUrls = []
for result in results:
    imageUrls.append(result['image'])
print(imageUrls[0])

dic = PyDictionary()

@bot.command()
async def define(ctx, word):
    meanings = dic.meaning(word)
    embed = discord.Embed(title=word.capitalize(), colour=0x0000ff)
    if meanings is None:
        await ctx.send("There were no results for `{}`. Try another word.".format(word))
        return
    for word_class, meaning in meanings.items():
        output_meaning = ""
        for number, definition in enumerate(meaning):
            output_meaning += "**{}:** {}\n".format(number+1, definition).capitalize()
        embed.add_field(name=word_class, value=output_meaning, inline=False)

    #embed.set_image(url=image_url) -- Get from aiohttp google api
    embed.set_footer(text="Definitions by [Princetown University](http://wordnetweb.princeton.edu/perl/webwn)")
    await ctx.send(embed=embed)