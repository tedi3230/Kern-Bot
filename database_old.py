import os
from urllib import parse
from random import randint
from traceback import print_exc
from atexit import register
import psycopg2

import discord


"""https://github.com/aio-libs/aiopg use for async"""

parse.uses_netloc.append("postgres")

try:
    dB_URL = os.environ["DATABASE_URL"]
except KeyError:
    dBFile = open('database_secret.txt', mode='r')
    dB_URL = dBFile.read()
    dBFile.close()

url = parse.urlparse(dB_URL)

db = psycopg2.connect(database=url.path[1:],
                      user=url.username,
                      password=url.password,
                      host=url.hostname,
                      port=url.port)

cur = db.cursor()

submissions_table = """CREATE TABLE IF NOT EXISTS submissions (
                       submission_id INT NOT NULL,
                       embed VARCHAR NOT NULL,
                       message_id BIGINT NOT NULL,
                       rating VARCHAR
                    )"""

# The rating should be a dictionary - then we can have

servers_table = """
                CREATE TABLE IF NOT EXISTS servers (
                    server_id BIGINT NOT NULL UNIQUE,
                    receive_channel_id BIGINT NOT NULL,
                    allow_channel_id BIGINT NOT NULL,
                    vote_channel_id BIGINT NOT NULL,
                    prefix VARCHAR
                )
                """


def check_for_table_exists():
    """Add the tables to database if not there."""
    try:
        cur.execute("SELECT relname FROM pg_class WHERE relname = 'servers'")
        if cur.fetchall() == []:
            cur.execute(servers_table)
        cur.execute("SELECT relname FROM pg_class WHERE relname = 'submissions'")
        if cur.fetchall() == []:
            cur.execute(submissions_table)

        db.commit()

    except psycopg2.DatabaseError:
        print_exc()


def add_query(command, args=None):
    check_for_table_exists()
    try:
        if not args is None:
            cur.execute(command, args)
        else:
            cur.execute(command)

        db.commit()

    except psycopg2.DatabaseError:
        print_exc()


def get_query(command, args=None):
    check_for_table_exists()
    try:
        if not args is None:
            cur.execute(command, args)
        else:
            cur.execute(command)

        data = cur.fetchall()
        db.commit()
        if len(data) == 1:
            return data[0]
        return data

    except psycopg2.DatabaseError:
        print_exc()


def close_conn():
    if db is not None:
        db.close()


register(close_conn)


def get_num_servers():
    return len(get_query("SELECT server_id FROM servers"))


def set_server_channels(server_id, receive_channel_id, allow_channel_id, vote_channel_id):
    """Sets the channels used for submissions in the database"""

    # sql = """UPDATE servers SET receive_channel_id = %s, allow_channel_id = %s, vote_channel_id = %s
    #          WHERE server_id = %s;
    #          INSERT INTO servers(server_id, receive_channel_id, allow_channel_id, vote_channel_id)
    #          VALUES(%s, %s, %s, %s)"""
    sql = """INSERT INTO servers(server_id, receive_channel_id, allow_channel_id, vote_channel_id)
             VALUES(%s, %s, %s, %s)
             ON CONFLICT (server_id) DO UPDATE
                SET receive_channel_id = excluded.receive_channel_id,
                    allow_channel_id = excluded.allow_channel_id,
                    vote_channel_id = excluded.vote_channel_id;"""

    # add_query(sql, (receive_channel_id, allow_channel_id, vote_channel_id, server_id, server_id, receive_channel_id, allow_channel_id, vote_channel_id,))
    add_query(sql, (server_id, receive_channel_id,
                    allow_channel_id, vote_channel_id,))


def get_server_channels(server_id):
    """Retrieve the channels used for submissions off the ID of a server"""

    sql = """SELECT receive_channel_id, allow_channel_id, vote_channel_id FROM servers
             WHERE server_id = %s"""

    return get_query(sql, (server_id,))


def generate_id():
    """Generate the ID needed to index the submissions"""
    data = get_query("SELECT submission_id FROM submissions")
    submission_id = "{:06}".format(randint(0, 999999))
    print(data)
    if not data:
        return submission_id
    while submission_id in data:
        submission_id = "{:06}".format(randint(0, 999999))
    return submission_id


def get_prefix(server_id):
    """Get the prefix for accessing the bot."""
    data = get_query("SELECT prefix FROM servers WHERE server_id = %s", (server_id,))
    if len(data) == 0:
        return "c!"
    if data[0] is None:
        return "c!"
    return data[0]


def set_prefix(server_id : int, prefix):
    """Set the prefix for accessing the bot.""" #FIX THE CODE FOR WHEN NO SERVERS
    query = """UPDATE servers
                SET prefix = %s
                WHERE server_id = %s"""
    if not get_server_channels(server_id):
        return "No channels setup"
    add_query(query, (prefix, server_id))


def add_submission(submission_id, embed_file, message_id):
    add_query("INSERT INTO submissions (submission_id,embed,message_id) VALUES (%s, %s, %s)",
              (submission_id, embed_file, message_id,))


def get_submission(submission_id):
    embed = get_query(
        "SELECT embed FROM submissions WHERE submission_id = %s", (submission_id,))
    if embed is None:
        raise KeyError("{} is not a valid submission_id".format(submission_id))
    embed = embed[0][0]
    return discord.Embed.from_data(embed)


def del_submission(submission_id):
    add_query("DELETE FROM submissions WHERE submission_id = %s",
              (submission_id,))


if __name__ in "__main__":
##    print(get_server_channels(382780023926554625))
##    set_server_channels(382780023926554625, 382780254382718997, 382780208014557185, 382780181645099008)
##    print(get_query("SELECT * FROM servers"))
##    set_prefix(382780023926554625, "!")
##    print(get_query("SELECT * FROM servers"))
##    print(get_prefix(382780023926554625))
##    print(get_num_servers())
    pass
