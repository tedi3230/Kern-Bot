#pylint: disable-msg=C0413
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import discord
from discord.ext import commands

class Statistics:
    def __init__(self, bot):
        self.bot = bot

    # async def uh(self, ctx):
    #     plt.figure()
    #     plt.plot([1, 2])
    #     plt.title("test")
    #     buf = io.BytesIO()
    #     plt.savefig(buf, format='png')

    #     f = discord.File(buf, filename="image.png")
    #     e = discord.Embed(image_url="attachment://image.png")
    #     await messagable.send(file=f, embed=e)


def setup(bot):
    bot.add_cog(Statistics(bot))