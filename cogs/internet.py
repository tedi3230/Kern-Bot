import random
from os import environ, path
from asyncio import sleep
from collections import OrderedDict

import aiohttp
import async_timeout
from bs4 import BeautifulSoup
from tabulate import tabulate

import discord
from discord.ext import commands

import custom_classes as cc

protocols = ['ssh',
             'smb',
             'smtp',
             'ftp',
             'imap',
             'http',
             'https',
             'pop',
             'htcpcp',
             'telnet',
             'tcp',
             'ipoac']

class Internet:
    """Web functions (that make requests)"""
    def __init__(self, bot):
        self.bot = bot
        self.bot_logs = self.bot.get_channel(bot.bot_logs_id)

        try:
            self.streamable_user = environ["STREAM_USER"]
            self.streamable_password = environ["STREAM_PASS"]
        except KeyError:
            file_path = path.join(path.dirname(__file__), '../streamable_secret.txt')
            stream_file = open(file_path, mode='r')
            auth = []
            for line in stream_file:
                auth.append(line)
            stream_file.close()
            self.streamable_user = auth[0].strip('\n')
            self.streamable_password = auth[1]

    async def get_youtube_videos(self, url):
        results = OrderedDict()
        vids = []

        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                async with session.get(url) as resp:
                    soup = BeautifulSoup((await resp.read()).decode('utf-8'), "lxml")

        for link in soup.find_all('a', href=True):
            url = link.get('href', "")
            title = link.get('title', "")
            if "/watch" in url and title and not title.startswith('https') and "googleads" not in url:
                if not url.startswith('https://www.youtube.com'):
                    url = 'https://www.youtube.com' + url
                results[title] = url

        for vid, url in results.items():
            vid = vid.replace("[", "⦋").replace("]", "⦌")
            if vid.isupper():
                vid = vid[:60] + "..."
            if len(vid) > 80:
                vid = vid[:80] + "..."
            vids.append(f"[{vid}]({url})")

        return vids[:5]

    @commands.group("youtube", invoke_without_command=True)
    async def youtube(self, ctx, *, keyword: str):
        """Searches YouTube for a video"""
        url = "https://www.youtube.com/results?search_query={}&sp=EgIQAQ%253D%253D".format(keyword)
        vids = self.get_youtube_videos(url)

        if len(keyword) > 40:
            keyword = keyword[:40] + "..."

        results = "\n".join(vids)
        await ctx.neutral(results, f"YouTube Search Results for: {keyword}")

    @youtube.command()
    async def trending(self, ctx):
        url = "https://www.youtube.com/feed/trending"
        vids = self.get_youtube_videos(url)
        results = "\n".join([f"{index}) {title}" for index, title in enumerate(vids)])
        await ctx.neutral(results, "YouTube Trending")

    @youtube.command()
    async def channel(self, ctx, channel):
        pass

    @youtube.command()
    async def playlist(self, ctx, playlist):
        pass

    @commands.command()
    async def hack(self, ctx, *, url: cc.Url):
        "Starts a fake hacking instance on a specified URL."
        loading = str(self.bot.get_emoji(395834326450831370))
        thousands = str(self.bot.get_emoji(396890900783038499))
        hundreds = str(self.bot.get_emoji(396890900158218242))
        tens = str(self.bot.get_emoji(396890900753547266))
        ones = str(self.bot.get_emoji(396890900426653697))

        fake_ports = sorted([random.randint(0, 65535) for i in range(random.randint(0, 10))])
        prtcls = [random.choice(protocols) for i in range(len(fake_ports))]
        secures = [random.choice(["'false'", 'true']) for i in range(len(fake_ports))]
        table_data = list(zip(fake_ports, prtcls, secures))
        headers = ["PORT", "PROTOCOL", "SECURE"]
        table = str(tabulate(table_data, headers, tablefmt="rst"))
        open_data = [data[0:2] for data in table_data if data[2]]
        open_ports = ", ".join([str(data[0]) for data in open_data])

        msg = await ctx.send(f"Looking for open ports in <{url}>")
        content = msg.content
        await msg.edit(content=f"{content}\nPort: {thousands}{hundreds}{tens}{ones}{loading}")
        await sleep(10)

        if not table_data:
            await msg.edit(content=f"Port scan complete. No ports found.")
            return

        await msg.edit(content=f"Port scan complete. Scan report: ```ml\n{table}```\n{loading}Attempting to bruteforce insecure ports: ({open_ports})")

        #Now do fake atatck on unsecure port (note, add a RFC 1149 reference)

    @commands.command()
    async def obama(self, ctx, *, text: str):
        """Makes obama speak the text"""
        if len(text) - len(ctx.prefix + "obama") > 280:
            await ctx.send("A maximum character total of 280 is enforced. You sent: `{}` characters".format(len(text)))
            return
        await ctx.trigger_typing()

        async def create_video(text):
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.post(url="http://talkobamato.me/synthesize.py", data={"input_text":text}) as resp:
                        if resp.status >= 400:
                            raise self.bot.ResponseError(f"Streamable upload responded with status {resp.status}")
                        text = await resp.text()
                        url = resp.url

            while '<source src="' not in text:
                async with aiohttp.ClientSession() as session:
                    async with async_timeout.timeout(10):
                        async with session.get(url) as resp:
                            text = await resp.text()

            start = text.index('<source src="') + len('<source src="')
            end = text.index('" type="video/mp4">')
            link = "http://talkobamato.me/" + text[start:end]
            return link

        async def upload_streamable(url):
            async with aiohttp.ClientSession() as session:
                with async_timeout.timeout(10):
                    async with session.get('https://api.streamable.com/import?url={}'.format(url), auth=aiohttp.BasicAuth(self.streamable_user, self.streamable_password)) as resp:
                        if resp.status >= 400:
                            raise self.bot.ResponseError(f"Streamable upload responded with status {resp.status}")
                        js = await resp.json()
                        return "https://streamable.com/{}".format(js['shortcode'])


        link = await create_video(text)
        url = await upload_streamable(link)
        msg = await ctx.send(url)
        while True:
            async with aiohttp.ClientSession() as session:
                with async_timeout.timeout(5):
                    async with session.get('https://api.streamable.com/oembed.json?url={}'.format(url)) as resp:
                        if resp.status >= 400:
                            raise self.bot.ResponseError(f"Streamable upload responded with status {resp.status}")
                        js = await resp.json()
                        if js['height'] is not None:
                            await msg.edit(content=url+'/')
                            await msg.edit(content=url)
                            return
            await sleep(5)

def setup(bot):
    bot.add_cog(Internet(bot))
