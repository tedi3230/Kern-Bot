from urllib import parse
import os

import discord
from discord.ext import commands
import asyncpg
import asyncio

# https://magicstack.github.io/asyncpg/current/
# https://magicstack.github.io/asyncpg/current/api/index.html#prepared-statements

class Database:
    def __init__(self, bot):
        self.bot = bot
        try:
            self.database_url = os.environ["DATABASE_URL"]
        except KeyError:
            database_file = open('database_secret.txt', mode='r')
            database_url = database_file.read()
            database_file.close()

        self.dsn = parse.urlparse(database_url)
        self.pool = None
        self.prefix_conn = None
        self.prefix_stmt = None

        
    async def init(self):
        self.pool = await asyncpg.create_pool(self.dsn)
        #self.prefix_conn = await self.pool.acquire()
        self.prefix_conn = await asyncpg.connect()
        self.prefix_stmt = await self.prefix_conn.prepare("SELECT prefix FROM servers WHERE server_id = $1")

    async def get_prefix(self, ctx, server_id):
        """Get the prefix for accessing the bot."""
        data = await self.prefix_stmt.fetchrow(server_id)
        print(data)
        if len(data) == 0:
            return "m!"
        if data[0] is None:
            return "m!"
        return data[0]

def setup(bot):
    bot.add_cog(Database(bot))

if __name__ in "__main__":
    loop = asyncio.get_event_loop()
    db = Database("ho")
    loop.run_until_complete(db.get_prefix(336642139381301249))