import psycopg2
from urllib import parse
import os
import pickle
from random import randint

parse.uses_netloc.append("postgres")

try:
    dB_URL = os.environ["DATABASE_URL"]
except KeyError:
    dBFile = open('database_secret.txt', mode='r')
    dB_URL = dBFile.read()
    dBFile.close()

url = parse.urlparse(dB_URL)

dataBase = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

cur = dataBase.cursor()

def execute(command,cursor=None):
    if cursor is None:
        cursor = cur
    try:
        cursor.execute(command)
        return cursor.fetchall()
    except psycopg2.InternalError as error:
        dataBase.commit()
        return error    
    except psycopg2.ProgrammingError as error:
        dataBase.commit()
        return error

execute("CREATE TABLE IF NOT EXISTS Submissions(submissionID INT,Embed bytea,messageID INT,rating INT)") #Works
execute("CREATE TABLE IF NOT EXISTS Servers(serverID INT,receiveChannelID INT,allowChannelID INT, voteChannelID INT,prefix TEXT)") #Works
channelTypes = [0,1,2,3]

"""receiveChannelID is where !submit gets sent, allowChannelID is where !allow gets sent, voteChannelID is where the final contestants get sent"""

class ChannelTypeFailure(Exception):
    pass
class ServerNotExist(Exception):
    pass
class LookupError(Exception):
    pass
class TypeError(Exception):
    pass

def cleanUP():
    dataBase.close()

def getNumServers():
    """Get the number of servers in the database"""
    #print(accessDatabase(0,"Servers","serverID"))
    #return len(accessDatabase(0,"Servers","serverID")[0])


def getServerChannels(server, channelType):
    """Get the submission channels in the server, 0=All Channels,1=Receive Channel",2=Allow Channel,4=Vote Channel"""
    if channelType not in channelTypes:
        raise TypeError("{} is not a valid channelType".format(channelType))
    if channelType == 0:
        cur.execute("SELECT receiveChannelID,allowChannelID,voteChannelID FROM Servers WHERE serverID = ?",(server,))
        channelIDs = list(cur)
        print(channelIDs)
        channelIDs = list(channelIDs[0])
        channelIDs.pop(0)
        return channelIDs
    else:
        if channelType == 1:
            channelType = "receiveChannelID"
        elif channelType == 2:
            channelType = "allowChannelID"
        elif channelType == 3:
            channelType = "voteChannelID"
        cur.execute("SELECT {} FROM Servers WHERE serverID = {}".format(channelType,server))
    channelID = cur.fetchall() 
    if len(channelID) == 0:
        raise LookupError("{} is not a known server.".format(server))
    return channelID[0][0]

def setServerChannels(*args):
    """Set up the channels for making, allowing, and voting for submissions."""
    if len(args) != 4:
        raise TypeError("There was an incorrect number of arguments supplied.")
    cur.execute("INSERT OR IGNORE INTO Servers Values(?,?,?,?,?)",(args[0],args[1],args[2],args[3],"c!"))
    dataBase.commit()
    #Make so that serverID & other channels, one has INSERT REPLACe the other is insert IGNORE

def addSubmission(submissionID,embedFile,messageID):
    """Add to the database the submission, by the submission ID & also including the embed File"""
    dump = pickle.dumps(embedFile)
    cur.execute("INSERT INTO Submissions (submissionID,Embed,messageID) VALUES (?,?,?)",(submissionID,dump,messageID,))
    dataBase.commit()

def getSubmission(submissionID):
    cur.execute("SELECT Embed FROM Submissions WHERE submissionID = (?)",(submissionID,))
    embed = cur.fetchall()
    if len(embed) == 0:
        raise LookupError("{} is not a valid submissionID".format(submissionID))
    embed = embed[0][0]
    return pickle.loads(embed)

def removeSubmission(submissionID):
    cur.execute("DELETE FROM Submissions WHERE submissionID = ?",(submissionID,)) 
    dataBase.commit()
    return None

def generateID():
    submissionID = "{:06}".format(randint(0,999999))
    cur.execute("SELECT submissionID FROM Submissions")
    submissions = cur.fetchall()
    if len(submissions) == 0:
        return submissionID
    while submissionID in submissions[0]:
        submissionID = "{:06}".format(randint(0,999999))
    return submissionID

def getMessageID(submissionID):
    cur.execute("SELECT messageID FROM Submissions WHERE submissionID = ?",(submissionID,))
    messageID=cur.fetchall()
    return messageID[0][0]

def getPrefix(serverID):
    cur.execute("SELECT prefix FROM Servers WHERE serverID = {}".format(serverID))
    prefix = cur.fetchall()
    if len(prefix) == 0:
        return "c!"
    elif prefix[0][0] is None:
        return "c!"
    return prefix[0][0]

def setPrefix(serverID,prefix):
    cur.execute("INSERT INTO Servers (prefix) VALUES ?;",(prefix,))
    dataBase.commit()
    return None

if __name__ in "__main__":
    pass
    #cur.execute("INSERT INTO Servers VALUES(380288809310617600,380289063040712704,380289087657213952,380364317809311746);")