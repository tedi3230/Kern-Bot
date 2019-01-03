import json
import os
import ssl
from socket import gaierror

import aiofiles
import asyncpg
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# https://magicstack.github.io/asyncpg/current/
# https://magicstack.github.io/asyncpg/current/api/index.html#prepared-statements


class DudPool:
    _closed = True
    ready = False

    async def close(self):
        return


class Database:
    """Accessing database functions"""

    ready = False
    pool: asyncpg.pool.Pool
    dsn: str
    bot: commands.Bot

    @classmethod
    async def start(cls, bot: commands.Bot):
        self = cls()
        self.bot = bot
        self.dsn = os.environ["DATABASE_URL"]

        ssl_object = ssl.create_default_context()
        ssl_object.check_hostname = False
        ssl_object.verify_mode = ssl.CERT_NONE
        try:
            self.pool = await asyncpg.create_pool(self.dsn, ssl=ssl_object,
                                                  command_timeout=60)
        except (asyncpg.exceptions.InvalidCatalogNameError,
                asyncpg.exceptions.InvalidPasswordError,
                ValueError, TimeoutError, gaierror) as e:
            return await self.bot.close("Unable to connect to database")

        async with aiofiles.open("schema.sql") as f:
            await self.pool.execute(await f.read())
            print(await f.read())

        self.ready = True

    async def set_contest_channels(self, ctx, submission_channel):
        sql = """INSERT INTO guilds (guild_id, submission_channel_id)
                 VALUES ($1, $2)
                 ON CONFLICT (guild_id) DO UPDATE
                    SET submission_channel_id = excluded.submission_channel_id;"""
        await self.pool.execute(sql, ctx.guild.id, submission_channel)

    async def get_submission_channel(self, ctx):
        sql = """SELECT submission_channel_id FROM guilds
                 WHERE guild_id = $1"""
        return await self.pool.fetchrow(sql, ctx.guild.id)

    async def add_prefix(self, ctx, prefix: str):
        sql = """UPDATE guilds SET prefixes = array_append(prefixes, $1)
                 WHERE guild_id = $2"""
        await self.pool.execute(sql, prefix, ctx.guild.id)
        return prefix

    async def get_prefixes(self, ctx):
        return await self.pool.fetchval("SELECT prefixes FROM guilds WHERE guild_id = $1", ctx.guild.id) or []

    async def remove_prefix(self, ctx, prefix):
        await self.pool.execute("UPDATE guilds SET prefixes = array_remove(prefixes, $1) WHERE guild_id = $2",
                                 prefix, ctx.guild.id)

    async def add_contest_submission(self, ctx, embed: discord.Embed):
        sub_id = int(await self.generate_id())
        await self.pool.execute("""INSERT INTO submissions (guild_id, owner_id, submission_id, embed) VALUES ($1, $2, $3, $4)""",
                              ctx.guild.id, ctx.author.id, sub_id, json.dumps(embed.to_dict()))
        return sub_id

    async def get_contest_submission(self, submission_id: int):
        title, description, image_url = await self.pool.fetchval("SELECT title, description, image_url FROM submissions WHERE submission_id = $1", submission_id)
        return discord.Embed(title=title,
                             description=description).set_image(url=image_url)

    async def list_contest_submissions(self, ctx):
        return await self.pool.fetch("SELECT owner_id, submission_id, embed, rating FROM submissions WHERE guild_id = $1 ORDER BY rating",
                                      ctx.guild.id)

    async def remove_contest_submission(self, ctx):
        await self.pool.execute('DELETE FROM submissions WHERE owner_id = $1 AND guild_id = $2', ctx.author.id, ctx.guild.id)

    async def clear_contest_submission(self, ctx, submission_id: int):
        await self.pool.execute('DELETE FROM submissions WHERE submission_id = $1 AND guild_id = $2', submission_id, ctx.guild.id)

    async def purge_contest_submissions(self, ctx):
        await self.pool.execute("DELETE FROM submissions WHERE guild_id = $1", ctx.guild.id)

    async def set_max_rating(self, ctx, max_rating: int):
        await self.pool.execute("UPDATE guilds SET max_rating = $1 WHERE guild_id = $2", max_rating, ctx.guild.id)

    async def get_max_rating(self, ctx):
        await self.pool.fetchval("SELECT max_rating FROM guilds WHERE guild_id = $1", ctx.guild.id)

    async def add_submission_rating(self, ctx, rating: int, submission_id: int):
        max_rating = await self.get_max_rating(ctx) or 10
        if int(rating) > int(max_rating):
            raise ValueError("The rating was greater than the maximum rating allowed (defaults to 10).")
        await self.pool.execute("UPDATE submissions SET rating = $1 WHERE submission_id = $2 AND guild_id = $3", rating, submission_id, ctx.guild.id)

    async def get_submission_rating(self, ctx, submission_id: int):
        return await self.pool.fetchval("SELECT rating FROM submissions WHERE submission_id = $1 AND guild_id = $2", submission_id, ctx.guild.id)

    async def check_user_has_submission(self, ctx):
        return await self.pool.fetchval("SELECT EXISTS(SELECT 1 FROM submissions "
                                        "WHERE owner_id=$1)", ctx.author.id)


if __name__ in '__main__':
    async def main():
        database = await Database.start("not_a_bot")

    import asyncio
    import os
    os.chdir("../")
    asyncio.get_event_loop().run_until_complete(main())
