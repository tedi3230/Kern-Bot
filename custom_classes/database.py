import os
import ssl

import aiofiles
import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def create_database():
    ssl_object = ssl.create_default_context()
    ssl_object.check_hostname = False
    ssl_object.verify_mode = ssl.CERT_NONE

    database = await asyncpg.create_pool(os.environ["DATABASE_URL"],
                                         ssl=ssl_object,
                                         command_timeout=60)

    async with aiofiles.open("schema.sql") as f:
        await database.execute(await f.read())

    return database


if __name__ in '__main__':
    async def main():
        database = await create_database()

    import asyncio
    os.chdir("../")
    asyncio.get_event_loop().run_until_complete(main())
