import os
import pickle
from urllib import parse
from random import randint
from traceback import print_exc
from ast import literal_eval #Putting dic values inside
import psycopg2

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

submissions_table = """
                CREATE TABLE IF NOT EXISTS Submissions (
                    submissionID INT NOT NULL,
                    embed BYTEA NOT NULL,
                    messageID BIGINT NOT NULL,
                    rating INT
                )
                """

##The rating should be a dictionary - then we can have


servers_table = """
                CREATE TABLE IF NOT EXISTS Servers (
                    serverID BIGINT NOT NULL UNIQUE,
                    receiveChannelID BIGINT NOT NULL,
                    allowChannelID BIGINT NOT NULL,
                    voteChannelID BIGINT NOT NULL,
                    prefix VARCHAR(10)
                )
                """

def create_tables():
    """Add the tables to database if not there."""
    conn = None
    try:
        conn = db
        cur = conn.cursor()

        cur.execute(submissions_table)
        cur.execute(servers_table)

        cur.close()
        conn.commit()

    except psycopg2.DatabaseError:
        print_exc()

    finally:
        if conn is not None:
            conn.close()


def add_query(command, args=None):
    create_tables()
    conn = None
    try:
        conn = db
        cur = conn.cursor()

        if not args is None:
            cur.execute(command, args)
        else:
            cur.execute(command)

        cur.close()
        conn.commit()

    except psycopg2.DatabaseError:
        print_exc()

    finally:
        if conn is not None:
            conn.close()

def get_query(command, args=None):
    create_tables()
    conn = None
    try:
        conn = db
        cur = conn.cursor()

        if not args is None:
            cur.execute(command, args)
        else:
            cur.execute(command)

        data = cur.fetchall()
        conn.commit()
        if len(data) == 1:
            return data[0]
        return data

    except psycopg2.DatabaseError:
        print_exc()

    finally:
        if conn is not None:
            conn.close()


def get_num_servers():
    return len(get_query("SELECT serverID From Servers")[0])
    # create_tables()
    # conn = None
    # try:
    #     conn = db.conn()
    #     cur = conn.cursor()

    #     cur.execute("SELECT serverID FROM Servers")

    #     data = cur.fetchall()
    #     return len(data[0])

    # except psycopg2.DatabaseError:
    #     print_exc()

    # finally:
    #     if conn is not None:
    #         conn.close()

def set_server_channels(serverID, receiveChannelID, allowChannelID, voteChannelID):
    """Sets the channels used for submissions in the database"""
    sql = """UPDATE Servers SET receiveChannelID = %s, allowChannelID = %s, voteChannelID = %s
             WHERE serverID = %s;
             INSERT INTO Servers(serverID, receiveChannelID, allowChannelID, voteChannelID)
             VALUES(%s, %s, %s, %s)"""

    add_query(sql, (receiveChannelID, allowChannelID, voteChannelID, serverID, serverID, receiveChannelID, allowChannelID, voteChannelID,))
    # create_tables()
    # conn = None
    # try:
    #     conn = db.conn()
    #     cur = conn.cursor()

    #     cur.execute(sql, (receiveChannelID, allowChannelID, voteChannelID, serverID, serverID, receiveChannelID, allowChannelID, voteChannelID,))

    #     conn.commit()
    #     cur.close()

    # except psycopg2.DatabaseError:
    #     print_exc()

    # finally:
    #     if conn is not None:
    #         conn.close()

def get_server_channels(serverID):
    """Retrieve the channels used for submissions off the ID of a server"""

    sql = """SELECT receiveChannelID, allowChannelID, voteChannelID FROM Servers
             WHERE serverID = %s"""

    return get_query(sql, (serverID,))
    # create_tables()
    # conn = None
    # try:
    #     conn = db.conn()
    #     cur = conn.cursor()

    #     cur.execute(sql, (serverID,))

    #     data = cur.fetchone()
    #     return data

    # except psycopg2.DatabaseError:
    #     print_exc()

    # finally:
    #     if conn is not None:
    #         conn.close()

def generate_id():
    """Generate the ID needed to index the submissions"""
    data = get_query("SELECT submissionID FROM Submissions")
    submissionID = "{:06}".format(randint(0, 999999))
    if not data:
        return submissionID
    while submissionID in data[0]:
        submissionID = "{:06}".format(randint(0, 999999))
    return submissionID

    # create_tables()
    # conn = None
    # try:
    #     conn = db.conn()
    #     cur = conn.cursor()

    #     submissionID = "{:06}".format(randint(0, 999999))
    #     cur.execute("SELECT submissionID FROM Submissions")

    #     data = cur.fetchall()
    #     if not data:
    #         return submissionID
    #     while submissionID in data[0]:
    #         submissionID = "{:06}".format(randint(0, 999999))
    #     return data

    # except psycopg2.DatabaseError:
    #     print_exc()

    # finally:
    #     if conn is not None:
    #         conn.close()

def get_prefix(serverID):
    """Get the prefix for accessing the bot."""
    data = get_query("SELECT prefix FROM Servers WHERE serverID = %s", (serverID,))
    if data is None:
        return "c!"
    return data

    # create_tables()
    # conn = None
    # try:
    #     conn = db.conn()
    #     cur = conn.cursor()

    #     cur.execute("SELECT prefix FROM Servers WHERE serverID = %s", (serverID,))
    #     data = cur.fetchone()

    #     if data is None:
    #         return "c!"

    #     return data

    # except psycopg2.DatabaseError:
    #     print_exc()

    # finally:
    #     if conn is not None:
    #         conn.close()

def set_prefix(serverID, prefix):
    """Set the prefix for accessing the bot."""
    add_query("INSERT INTO Servers (prefix) VALUES (%s) WHERE serverID = %s", (prefix,serverID))
    # create_tables()
    # conn = None
    # try:
    #     conn = db.conn()
    #     cur = conn.cursor()

    #     cur.execute("INSERT INTO Servers (prefix) VALUES (%s) WHERE serverID = %s", (prefix,serverID))

    #     conn.commit()
    #     cur.close()

    # except psycopg2.DatabaseError:
    #     print_exc()

    # finally:
    #     if conn is not None:
    #         conn.close()

def add_submission(submissionID, embedFile, messageID):
    pass

def get_submission(submissionID):
    pass

def del_submission(submissionnID):
    pass

if __name__ in "__main__":
    set_server_channels(382780023926554625, 382780254382718997, 382780208014557185, 382780181645099008)
    print(get_prefix(382780023926554625))
    print(get_num_servers())
    print(get_server_channels(382780023926554625))