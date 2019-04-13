import asyncio
from os import environ

import async_timeout
import discord
from dotenv import load_dotenv

import custom_classes as cc

load_dotenv()

URLS = {
    "DBL": "https://discordbots.org/api/bots/{}/stats",
    "BFD": "https://botsfordiscord.com/api/bot/{}",
    "DBG": "https://discord.bots.gg/api/v1/bots/{}/stats",
}


class DiscordLists:
    def __init__(self, bot: cc.KernBot):
        self.bot = bot
        self.bot.loop.create_task(self.send_loop())

    async def send_loop(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(10)
        while not self.bot.is_closed():
            for service, url in URLS.items():
                await self.post_server_count(service, url.format(380598116488970261))
            await asyncio.sleep(30 * 60)

    async def send_error(self, service, error):
        embed = discord.Embed(title=f"Sending server count failed for {service}",
                              description=error,
                              colour=discord.Colour.red())
        await self.bot.logs.send(embed=embed)

    async def post_server_count(self, service: str, url: str):
        headers = {
            "Authorization": environ[f"{service}_TOKEN"],
        }
        body = {
            "server_count": len(self.bot.guilds),  # BFD, DBL
            "guildCount": len(self.bot.guilds),  # DBG
        }
        try:
            with async_timeout.timeout(30):
                async with self.bot.session.post(url,
                                                 headers=headers,
                                                 data=body) as r:
                    if r.status >= 400:
                        await self.send_error(service,
                                              await r.text())
        except asyncio.TimeoutError:
            await self.send_error(service, "Timeout occurred.")
        except Exception as e:
            await self.send_error(service, str(e))


def setup(bot):
    bot.add_cog(DiscordLists(bot))
