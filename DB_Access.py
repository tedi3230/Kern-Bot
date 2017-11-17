import sqlite3
import pickle
from random import randint

dataBase = sqlite3.connect("database.db")
cur = dataBase.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS Submissions(id INT,Embed MEDIUMBLOB,rating INT)")
cur.execute("CREATE TABLE IF NOT EXISTS Servers(serverID INT,receiveChannelID INT,allowChannelID INT, outputChannelID INT)")
channelTypes = ["receiveChannelID","allowChannelID","outputChannelID"]

"""receiveChannelID is where !submit gets sent, allowChannelID is where !allow gets sent, outputChannelID is where the final contestants get sent"""

class ChannelTypeFailure(Exception):
    pass
class ServerNotExist(Exception):
    pass
class SubmissionNotExist(Exception):
    pass
class IncorrectNumOfArguments(Exception):
    pass

if __name__ in "__main__":
    pass
    #cur.execute("INSERT INTO Servers VALUES(380288809310617600,380289063040712704,380289087657213952,380364317809311746);")

def cleanUP():
    dataBase.close()

def getServerChannels(server, channelType):
    if channelType not in channelTypes:
        raise ChannelTypeFailure("{} is not a valid channelType".format(channelType))
    cur.execute("SELECT {} FROM Servers WHERE serverID = {}".format(channelType,server,))
    channelID = cur.fetchall() 
    if len(channelID) == 0:
        raise ServerNotExist("{} is not a known server.".format(server))
    return channelID[0][0]

def setServerChannels(*args):
    if len(args) != 4:
        raise IncorrectNumOfArguments("There was an incorrect number of arguments supplied.")
    cur.execute("INSERT OR IGNORE INTO Servers Values(?,?,?,?)",(args[0],args[1],args[2],args[3],))
    dataBase.commit()
    #Make so that serverID & other channels, one has INSERT REPLACe the other is insert IGNORE

def addSubmission(messageID,embedFile):
    dump = pickle.dumps(embedFile)
    cur.execute("INSERT INTO Submissions VALUES(?,?);",(messageID,dump,))
    dataBase.commit()

def getSubmission(messageID):
    cur.execute("SELECT Embed FROM Submissions WHERE id = ?",(messageID,))
    embed = cur.fetchall()
    if len(embed) == 0:
        raise SubmissionNotExist("{} is not a valid submission id".format(messageID))
    embed = embed[0][0]
    return pickle.loads(embed)

def removeSubmission(messageID):
    cur.execute("DELETE FROM Submissions WHERE id = ?",(messageID,))
    dataBase.commit()
    return None

def generateID():
    messageID = "{:06}".format(randint(0,999999))
    cur.execute("SELECT id FROM Submissions")
    submissions = cur.fetchall()
    if len(submissions) == 0:
        return messageID
    while messageID in submissions[0]:
        messageID = "{:06}".format(randint(0,999999))
    return messageID