#pylint: disable-msg=C0413
import io
import async_timeout
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import discord
from discord.ext import commands

def translate(value, left_min, left_max, right_min, right_max):
    return right_min + ((float(value - left_min) / float(left_max - left_min)) * (right_max - right_min))


class Statistics:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def currency(self, ctx):
        await ctx.send("```" + "\n".join(self.bot.statistics['currency'].keys()) + "```")

    async def get_data(self, coin, currency, days):
        coin = coin.lower()
        if coin not in self.bot.statistics['coins'].keys():
            raise ValueError(f'Coin {coin} does not exist')
        if self.bot.statistics['market_price'].get(coin) is None:
            with async_timeout.timeout(10):
                async with self.bot.session.get(f"https://min-api.cryptocompare.com/data/histoday?fsym={coin}&tsym={currency}&limit={days}") as resp:
                    vals = (await resp.json())['Data']
                    self.bot.statistics['market_price'][coin] = {}
                    self.bot.statistics['market_price'][coin]['high'] = [[-i, v['high']] for i, v in enumerate(vals)]
                    self.bot.statistics['market_price'][coin]['low'] = [[-i, v['low']] for i, v in enumerate(vals)]

        return self.bot.statistics['market_price'][coin]

    @commands.command()
    async def coin(self, ctx, coin, currency = "USD", days: int = 30):
        async with ctx.typing():
            try:
                data = await self.get_data(coin, currency, days)
            except ValueError as e:
                return await ctx.error('', str(e))
            plt.figure()
            print(data['high'])
            print(data['low'])
            plt.plot([x[0] for x in data['high']], [y[1] for y in data['high']])
            plt.plot([x[0] for x in data['low']], [y[1] for y in data['low']])
            plt.title(coin)
            plt.legend(['High', 'Low'], loc='upper left')
            plt.xlabel("Days")
            plt.ylabel("Worth: USD")
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            coin_data = self.bot.statistics['coins'][coin.lower()]
            f = discord.File(buf, filename="image.png")
            e = discord.Embed()
            e.set_author(name=coin_data['CoinName'], icon_url="https://www.cryptocompare.com" + coin_data['ImageUrl'])
            e.set_image(url="attachment://image.png")
            await ctx.send(file=f, embed=e)


def setup(bot):
    bot.add_cog(Statistics(bot))