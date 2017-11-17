import sqlite3

dataBase = sqlite3.connect("database.db")
cur = dataBase.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS Submissions(id INT,Embed MEDIUMBLOB)")
cur.execute("CREATE TABLE IF NOT EXISTS Servers(serverid INT,receiveChannelID INT,allowChannelID INT, outputChannelID INT)")
channelTypes = ["receiveChannelID","allowChannelID","outputChannelID"]

"""receiveChannelID is where !submit gets sent, allowChannelID is where !allow gets sent, outputChannelID is where the final contestants get sent"""

class ChannelTypeFailure(Exception):
    pass
class ServerNotExist(Exception):
    pass
class IncorrectNumOfArguments(Exception):
    pass

if __name__ in "__main__":
    pass
    #cur.execute("INSERT INTO Servers VALUES(380288809310617600,380289063040712704,380289087657213952,380364317809311746);")

def getServerChannels(server, channelType):
    if channelType not in channelTypes:
        raise ChannelTypeFailure("{} is not a valid channelType".format(channelType))
    cur.execute("SELECT {} FROM Servers WHERE serverid = {}".format(channelType,server))
    channelID = cur.fetchall()
    if len(channelID) == 0:
        raise ServerNotExist("{} is not a known server.".format(server))
    return "".join(map(str, channelID[0]))

def setServerChannels(*args):
    if len(args) != 4:
        raise IncorrectNumOfArguments("There was an incorrect number of arguments supplied.")
    cur.execute("INSERT OR IGNORE INTO Servers Values({},{},{},{})".format(args[0],args[1],args[2],args[3]))
    #Make so that serverID & other channels, one has INSERT REPLACe the other is insert IGNORE
    pass

def addSubmission(messageID,embedFile):
    cur.execute("INSERT INTO Submissions VALUES({},{});".format(messageID,embedFile))
