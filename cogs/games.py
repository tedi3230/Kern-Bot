import asyncio
import html
from datetime import datetime
from random import shuffle

import aiohttp
import async_timeout

import discord
from discord.ext import commands

def rgb(r, g, b):
    return discord.Colour.from_rgb(r, g, b)

TRIVIA_URL = "https://opentdb.com/api.php?amount=5"
COLOURS = {'easy': rgb(255, 211, 0), 'medium': rgb(232, 97, 0), 'hard': rgb(255, 36, 0)}
EMOJIS = {1: '1\u20e3', 2: '2\u20e3', 3: '3\u20e3', 4: '4\u20e3'}


class Games:
    def __init__(self, bot):
        self.bot = bot

#
    async def trivia_categories(self, category):
        with async_timeout.timeout(10):
            async with self.bot.session.get("https://opentdb.com/api_category.php") as resp:
                cats = (await resp.json())['trivia_categories']

        categories = {}
        for cat in cats:
            categories[cat['name'].lower()] = cat['id']

        c_id = categories.get(category.lower())
        if c_id is None:
            raise ValueError("Category `{}` does not exist.".format(category))
        return c_id

    async def get_trivia_results(self, category=None):
        if category is None:
            url = TRIVIA_URL
        else:
            url = TRIVIA_URL + "&category=" + str(await self.trivia_categories(category))

        with async_timeout.timeout(10):
            async with self.bot.session.get(url) as resp:
                return (await resp.json())['results']

    @commands.command()
    async def trivia(self, ctx, *, category: str=None):
        """Provides a trivia functionality. 5 questions. Can pass a category"""
        results = await self.get_trivia_results(category)
        corrects = {} #{correct:yours}
        for result in results:
            colour = COLOURS[result['difficulty']]
            category = html.unescape(result['category'])
            question = "*{}*\n".format(html.unescape(result['question']))
            e = discord.Embed(title=category, description=question, colour=colour)
            e.set_footer(text="Data from Open Trivia Database", icon_url=ctx.author.avatar_url)
            e.timestamp = datetime.utcnow()
            ques = result['incorrect_answers'] + [result['correct_answer']]
            shuffle(ques)
            ques = {i:j for i, j in enumerate(ques)}
            for index, q in enumerate(ques.values()):
                e.description += "\n{} {}".format(EMOJIS[index + 1], html.unescape(q))
            msg = await ctx.send(embed=e)
            for index, q in enumerate(ques):
                await msg.add_reaction(EMOJIS[index + 1])
            await msg.add_reaction("⏹")

            def same(reaction, member):
                return ctx.message.author == member and reaction.emoji in list(EMOJIS.values()) + ["⏹"]

            try:
                reaction, member = await self.bot.wait_for("reaction_add", check=same, timeout=30)
            except asyncio.TimeoutError:
                await ctx.error("You took too long to add an emoji.", "Timeout Error", rqst_by=False)
                break

            if str(reaction) == "⏹":
                await msg.delete()
                corrects = {}
                break

            corrects[ques[int(str(reaction)[0]) - 1]] = html.unescape(result['correct_answer'])

            await msg.delete()

        if corrects:
            des = "You answered:"
            correct_qs = 0
            for yours, correct in corrects.items():
                if yours is correct:
                    correct_qs += 1
                    des += f"\n✅ {correct}"
                else:
                    des += f"\n❌ Correct Answer: {correct}"
            des += "\n\nFor a total score of {}/{}".format(correct_qs, len(corrects))

            await ctx.success(des, "Results")

    @trivia.error
    async def trivia_error_handler(self, ctx, error):
        error = getattr(error, 'original', error)
        if isinstance(error, ValueError):
            await ctx.error(error, "Category Not Found", rqst_by=False)
        else:
            await ctx.error(error, rqst_by=False)

def setup(bot):
    bot.add_cog(Games(bot))
