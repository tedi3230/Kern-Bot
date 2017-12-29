import os
from random import randint

import asyncio

import discord
from discord.ext import commands
import asyncpg

# https://magicstack.github.io/asyncpg/current/
# https://magicstack.github.io/asyncpg/current/api/index.html#prepared-statements

submissions_table = """CREATE TABLE IF NOT EXISTS submissions (
                       submission_id INT NOT NULL UNIQUE,
                       embed JSONB NOT NULL,
                       server_id BIGINT NOT NULL,
                       owner_id BIGINT NOT NULL,
                       rating JSONB
                    )"""

# The rating should be a dictionary - then we can have

servers_table = """
                CREATE TABLE IF NOT EXISTS servers (
                    server_id BIGINT NOT NULL UNIQUE,
                    receive_channel_id BIGINT,
                    allow_channel_id BIGINT,
                    vote_channel_id BIGINT,
                    prefix VARCHAR
                )
                """

class Database:
    """Accessing database functions"""
    def __init__(self, bot):
        self.bot = bot
        try:
            self.dsn = os.environ["DATABASE_URL"]
        except KeyError:
            database_file = open('database_secret.txt', mode='r')
            self.dsn = database_file.read()
            database_file.close()

        self.pool = None
        self.prefix_conn = None
        self.prefix_stmt = None
        print(self.dsn)

        lop = asyncio.get_event_loop()
        lop.run_until_complete(self.init())

    async def init(self):
        self.pool = await asyncpg.create_pool(self.dsn, ssl=True)
        async with self.pool.acquire() as con:
            self.prefix_stmt = await con.prepare("SELECT prefix FROM servers WHERE server_id = $1")
            if await con.fetch("SELECT relname FROM pg_class WHERE relname = 'servers") is None:
                con.execute(servers_table)
            if await con.fetch("SELECT relname FROM pg_class WHERE relname = 'submissions") is None:
                con.execute(submissions_table)

    async def generate_id(self):
        """Generate the ID needed to index the submissions"""
        submission_id_list = await self.pool.fetchrow("SELECT submission_id FROM submissions")
        submission_id = "{:06}".format(randint(0, 999999))
        print(submission_id_list)
        if not submission_id_list:
            return submission_id
        while submission_id in submission_id_list:
            submission_id = "{:06}".format(randint(0, 999999))
        return submission_id

    async def set_contest_channels(self, server_id: int, *channels):
        sql = """INSERT INTO servers (server_id, receive_channel_id, allow_channel_id, vote_channel_id)
                 VALUES ($1, $2, $3, $4)
                 ON CONFLICT (server_id) DO UPDATE
                    SET receive_channel_id = excluded.receive_channel_id,
                        allow_channel_id = excluded.allow_channel_id,
                        vote_channel_id = excluded.vote_channel_id;"""

        await self.pool.execute(sql, server_id, *channels)

    async def get_contest_channels(self, server_id: int):
        sql = """SELECT receive_channel_id, allow_channel_id, vote_channel_id FROM servers
                 WHERE server_id = $1"""

        return await self.pool.fetchrow(sql, server_id)

    async def set_prefix(self, server_id: int, prefix: str):
        sql = """INSERT INTO servers(server_id, prefix) VALUES ($2, $1)
                 ON CONFLICT (server_id) DO UPDATE
                    SET prefix = $1"""

        await self.pool.execute(sql, prefix, server_id)

    async def get_prefix(self, server_id: int):
        return await self.pool.fetchval("SELECT prefix FROM servers WHERE server_id = $1", server_id)

    async def add_contest_submission(self, server_id: int, user_id: int, submission_id: int, embed: discord.Embed):
        await self.pool.execute("INSERT INTO submissions (submission_id, user_id, embed, server_id) VALUES ($1, $2, $3, $4)",
                                submission_id, user_id, embed.to_dict(), server_id)

    async def get_contest_submission(self, submission_id: int):
        embed = await self.pool.fetchval("SELECT embed FROM submissions WHERE submission_id = $1", submission_id)
        return discord.Embed.from_data(embed)

    async def list_contest_submissions(self, server_id: int):
        await self.pool.fetch("SELECT submission_id, embed FROM submissions WHERE server_id = $1",
                              server_id)

    async def remove_contest_submission(self, server_id: int, owner_id: int, submission_id: int):
        await self.pool.execute('DELETE FROM submissions WHERE submission_id = $1 AND owner_id = $2', submission_id, owner_id)

def setup(bot):
    bot.add_cog(Database(bot))

if __name__ in "__main__":
    loop = asyncio.get_event_loop()
    db = Database('lol')
    d = loop.run_until_complete(db.list_contest_submissions(336642139381301249))
    print(d)