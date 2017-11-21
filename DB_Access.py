import sqlite3
import pickle
from random import randint

dataBase = sqlite3.connect("database.db")
cur = dataBase.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS Submissions(submissionID INT,Embed MEDIUMBLOB,messageID INT,rating INT)")
cur.execute("CREATE TABLE IF NOT EXISTS Servers(serverID INT,receiveChannelID INT,allowChannelID INT, voteChannelID INT,prefix TEXT)")
channelTypes = [0,1,2,3]

"""receiveChannelID is where !submit gets sent, allowChannelID is where !allow gets sent, voteChannelID is where the final contestants get sent"""

class ChannelTypeFailure(Exception):
    pass
class ServerNotExist(Exception):
    pass
class SubmissionNotExist(Exception):
    pass
class IncorrectNumOfArguments(Exception):
    pass

def cleanUP():
    dataBase.close()



def checkKeyExists(dic,keyList):    
    values = []
    fails = []
    for key in KeyList:
        if key in dic.keys():
            values.append(dic[key])
        else:
            fails.append(key)
    if len(key) > 0:
        tempString = " ".join(fails)
        raise TypeError("function() missing at least 1 required keyword argument: {}".format(tempString))
    else:
        return values

def accessDatabase(aType,table,columns="*",values=tuple(),whereCol=str(),colValues=str()):
    """Access the database with easy commands.
    accessDatabase(aType,table,data=None,fields="*",)
    aType: 0="SELECT",1="INSERT",2="DELETE",3="SELECT WHERE".4="INSERT OR IGNORE" Integer.
    table = "Table Name". String
    columns = (col1,col2,etc.). Tuple of strings or "*".
    values = (value1,value2,etc.). Tuple of strings
    whereCol = (col). String
    colValues = (value). String."""

    """Do soemething to detect if those exist (aside from try)"""

    """Access Like So: accessDatabase(1,"Server",values=(col1,col2),colValues="hi
    
    Named arguments, argumentName=value

    """"

    values = kwargs['values']
    whereCol = kwargs['wherCol']
    colValues = kwargs['colValues']
    if aType == 0:
        """SELECT"""
        checkKeyExists(kwargs,['columns'])
        cur.execute("SELECT ? FROM ?",(columns,table))
        return cur.fetchall()
    elif aType == 1:
        """INSERT"""
        if "columns" in kwargs.keys():
            columns = kwargs['columns']
        else:
            
        values = kwargs['values']
        if len(columns) != len(values) and columns != "*":

        cur.execute("INSERT INTO ? ? VALUES ?",(table,columns,values))
    elif aType == 2:
        """DELETE"""
        pass
    elif aType ==3:
        """SELECT WHERE"""
        cur.execute("SELECT ? FROM ? WHERE ? = ?",(columns,table,whereCol,colValues))
        return cur.fetchall()
    elif aType == 4:
        """ INSERT OR IGNORE"""
    else:
        pass
        #Fail

def getServerChannels(server, channelType):
    """Get the submission channels in the server, 0=All Channels,1=Receive Channel",2=Allow Channel,4=Vote Channel"""
    if channelType not in channelTypes:
        raise ChannelTypeFailure("{} is not a valid channelType".format(channelType))
    if channelType == 0:
        cur.execute("SELECT receiveChannelID,allowChannelID,voteChannelID FROM Servers WHERE serverID = (?)",server)
        accessDatabase(3,)
        channelIDs = list(cur)
        channelIDs = list(channelIDs[0])
        channelIDs.pop(0)
        return channelIDs
    else:
        cur.execute("SELECT {} FROM Servers WHERE serverID = {}".format(channelType,server))
    channelID = cur.fetchall() 
    if len(channelID) == 0:
        raise ServerNotExist("{} is not a known server.".format(server))
    return channelID[0][0]

def setServerChannels(*args):
    """Set up the channels for making, allowing, and voting for submissions."""
    if len(args) != 4:
        raise IncorrectNumOfArguments("There was an incorrect number of arguments supplied.")
    cur.execute("INSERT OR IGNORE INTO Servers Values(?,?,?,?)",(args[0],args[1],args[2],args[3],))
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
        raise SubmissionNotExist("{} is not a valid submissionID".format(submissionID))
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
    cur.execute("SELECT messageID FROM Submissions WHERE submissionID = (?)",submissionID)
    messageID=cur.fetchall()
    return messageID[0][0]

def getPrefix(serverID):
    cur.execute("SELECT prefix FROM Servers WHERE serverID = (?)",int(serverID))
    prefix = cur.fetchall()
    if prefix[0][0] == None:
        return "!"
    return prefix[0][0]

def setPrefix(serverID,prefix):
    cur.execute("INSERT INTO Servers (prefix) VALUES (?);",prefix)
    dataBase.commit()
    return None

if __name__ in "__main__":
    pass
    #cur.execute("INSERT INTO Servers VALUES(380288809310617600,380289063040712704,380289087657213952,380364317809311746);")