import asyncpg
import discord
from discord.ext import commands

import custom_classes as cc


def generate_embed(author: discord.Member, title, description, image_url=None, colour=0x00ff00):
    """Generates a discord embed object off the given parameters"""
    embed = discord.Embed(title=title, description=description, colour=colour)
    embed.set_author(name=f"Author: {author.display_name}",
                     icon_url=author.avatar_url)
    if image_url is not None:
        embed.set_image(url=image_url)
    embed.set_thumbnail(url=author.avatar_url)
    return embed


submit_converter = cc.Delimited(" | ", [cc.lower, str, str, cc.url], {
                                        "contest":     True,
                                        "title":       True,
                                        "description": True,
                                        "image_url":   False,
                                })

rename_converter = cc.Delimited(" | ", [str, str], {
                                        "old": True,
                                        "new": True,
                                })


# TODO:
#   - Make the database functions call db_object.fetchval which does the async
#     with automatically. same for execute, etc.
#   - make database a cog and @property
#   - create and get contests (contest_name.lower() !!)


GET_CHANNEL = """
SELECT submission_channel_id FROM guilds WHERE guild_id = $1;
"""

ADD_SUBMISSION = """
INSERT INTO submissions (contest_id, author_id, title, description, image_url)
VALUES ($1, $2, $3, $4, $5);
"""

REMOVE_SUBMISSION = """
DELETE FROM submissions WHERE contest_id = $1 AND author_id = $2;
"""

FIND_CONTEST = """
SELECT contest_id, channel_id FROM contests
WHERE guild_id = $1 AND contest_name = $2;
"""


class Contests:
    """Contest functions"""

    def __init__(self, bot):
        self.bot: cc.KernBot = bot

    async def get_submission_channel(self):
        return await self.bot.database.execute()

    async def __local_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage

        return True

    async def __error(self, ctx, error):
        error = getattr(error, "original", error)
        if isinstance(error, cc.InvalidContest):
            await ctx.error(f"No contest found with name {error}.",
                            "Invalid Contest")

    @cc.group(name="contest")
    async def contest_group(self, ctx):
        # TODO: make this require admin/similar perms + add error for top group
        pass

    @contest_group.command()
    async def create(self, ctx, *, contest):
        """create a contest"""
        pass

    @contest_group.command()
    async def rename(self, ctx, names: rename_converter):
        """renames a contest"""
        pass

    @contest_group.command()
    async def delete(self, ctx, *, contest):
        """remove a contest"""
        pass

    @contest_group.command()
    async def purge(self, ctx, *, contest):
        """removes all submissions from a contest"""
        pass

    @contest_group.command()
    async def remove(self, ctx, contest):
        """remove an invalid submission"""

    @contest_group.command()
    async def results(self, ctx, *, contest):
        """get results for contest (previous list, but sorted)"""
        pass

    @cc.command(usage="<contest> | <title> | <description> | [image_url]")
    async def submit(self, ctx, *, arguments: submit_converter):
        """Allows you to submit something for a contest."""
        contest, title, description, image_url = arguments
        embed = generate_embed(ctx.author, title, description, image_url)

        record = await ctx.database.fetchrow(FIND_CONTEST, ctx.guild.id,
                                             contest)
        if record is None:
            raise cc.InvalidContest(contest)

        try:
            await ctx.database.execute(ADD_SUBMISSION, record["contest_id"],
                                       ctx.author.id, title,
                                       description, image_url)
        except asyncpg.UniqueViolationError:
            message = await ctx.error("You have already have a submission. If "
                                      "you wish to resubmit it, react ✅. If "
                                      "you wish to leave it as it is, react ❌",
                                      "Already Submitted")

            resubmit = await ctx.reaction_check(ctx.author, message)
            await message.delete()

            if not resubmit:
                return

            await ctx.database.execute(REMOVE_SUBMISSION + ADD_SUBMISSION,
                                       record["contest_id"], ctx.author.id,
                                       title, description, image_url)

        await ctx.submissions_channel.send(embed=embed)

    @cc.command()
    async def vote(self, ctx, author: discord.Member):
        """vote on a submission"""
        pass


def setup(bot):
    bot.add_cog(Contests(bot))