import sqlite3
import os
import os.path
import sys
import datetime
import time
from MySqlTasty import MySqlTasty
sql = ""
         
#-----------CreateListFromArray-------------------------------------
def ListFromArray(array):
    str = ""
    for e in array:
        str += "'"+e+"',"        
    str = str[:-1]
    return str
        
def ValueListFromArray(array):
    str = ""
    for e in array:
        str += "('"+e+"'),"        
    str = str[:-1]
    return str
    
def formatTimeFromEpoc(time,fmt):
    time = datetime.datetime.fromtimestamp(float(time)/1000.)
    time = str(time.strftime(fmt))
    return time

def IsTimeGreaterThanDaysAdded(time,daysToAdd):    
    time = datetime.datetime.fromtimestamp(float(time)/1000.)
    DaysAddedTime = time + datetime.timedelta(days=daysToAdd)
    if datetime.datetime.now() >= DaysAddedTime:
        return True
    else:
        return False
    
class MessageBuilder(object):
    entryCount = 0
    __BuildDetails = False
    __MessageDetailsDict = {}
    
    def __init__(self):
        global sql
        global __MessageDetailsDict
        sql = MySqlTasty('DB_NAME','USER','PASSWORD','IP/URL')
        __MessageDetailsDict = dict.fromkeys(['TotalMembers','Type','DetailType','BenchTimeFmt','BenchTime','DetailTimeFmt','DetailTime','Members'])
                
    def __CreateTableFromChatID(self,messageChatID):
            try:
                sql.execute("CREATE TABLE IF NOT EXISTS T" + messageChatID[:5] + " (UserName TEXT ,TimeStamp TEXT)")
            except:
                pass
                        
    def __DeleteAllDataWithChatId(self,messageChatID):
        sqlString = "Delete from T" + str(messageChatID[:5]) + ""
        sql.execute(sqlString)
                                        
    def __InsertUserEntry(self,message):
        self.__CreateTableFromChatID(message.chat_id)
        sqlString = "INSERT INTO T"+ message.chat_id[:5] +  " VALUES ('" + message.from_user + "','" + str(message.timestamp)+ "')"        
        sql.execute(sqlString)
        
    def InsertBotEntry(self,message):
        self.__CreateTableFromChatID(message.chat_id)
        sql.execute("INSERT INTO T"+ message.chat_id[:5] +  " VALUES ('bot','"+str(message.timestamp)+"')")
        
    def __DeleteAllEntrysSender(self,message):
        sql.execute("Delete from T" + message.chat_id[:5] + " where UserName = '" + message.from_user+"'")

    def __ReturnMinBotTimeStampFromChatID(self,messageChatID):
        sqlString = "SELECT MIN(TimeStamp) as TimeStamp from T" + messageChatID[:5]+ " WHERE UserName = 'bot'"
        sql.execute(sqlString)
        DataMessage = sql.GetResultsDictArray()
        if len(DataMessage) > 0:
            return DataMessage[0]['TimeStamp']
        else:
            return None
    def __BuildResultsMessage(self,Data,BuildDetails = False):
        if sql.GetRowCount() > 0:
            RowCount     = str(sql.GetRowCount())
            Totalmembers = __MessageDetailsDict['TotalMembers']
            BenchTime    =  formatTimeFromEpoc(Data[0]['BotMin'],__MessageDetailsDict['BenchTimeFmt'])
            DetailType   = __MessageDetailsDict['DetailType']
            Members      = __MessageDetailsDict['Members']
            type         = __MessageDetailsDict['Type']
            NewMessage = ""
            if BuildDetails is True:
                for e in range(0,sql.GetRowCount()):
                    UserName     = Data[e]['UserName']
                    TimeStamp    = formatTimeFromEpoc(Data[e]['TimeStamp'],__MessageDetailsDict['DetailTimeFmt']) if __MessageDetailsDict['DetailTimeFmt'] != "" else ""               
                    if UserName in Members:            
                        NewMessage += '@' + UserName + " " + TimeStamp + "\n"
                NewMessage = "**RESULTS**\n" + NewMessage + "\n" + BenchTime +"\n" + type + " " + RowCount + " of " + Totalmembers + "\n" + DetailType
            else:
                NewMessage = "**RESULTS**" + NewMessage + "\n" + BenchTime +"\n" + type + " " + RowCount + " of " + Totalmembers + "\n" + DetailType
        else:
            NewMessage = "No Data has been captured."
        return NewMessage
        
    def __GetInnactiveMemberList(self,message,Data):
        List  = []
        Found = False
        for Name in message.participants:
            Found = False
            for index in range(0,sql.GetRowCount()):
                if Name == Data[index]['UserName']:
                    Found = True
            if Found is False:
                List.append(Name)
        return List
        
    def BuildBenchMarkAnalysisMessageResults(self,message,BuildDetails = False):
        global __MessageDetailsDict
        sqlString = "Select DISTINCT t1.UserName as UserName, t1.TimeStamp as TimeStamp ,(SELECT MIN(TimeStamp) from T" + message.chat_id[:5] + " WHERE UserName = 'bot') as BotMin from T" + message.chat_id[:5] + " as t1 where  UserName <> 'bot' and t1.TimeStamp = (Select Max(t2.timestamp) from T" + message.chat_id[:5] + " as t2 where UserName <> 'bot' and t2.UserName = t1.UserName) and UserName in ("+ListFromArray(message.participants)+") group by TimeStamp, UserName " 
        sql.execute(sqlString)
        DataMessage = sql.GetResultsDictArray()
        __MessageDetailsDict['TotalMembers']  = str(len(message.participants))
        __MessageDetailsDict['Type']          = 'Active Members:'
        __MessageDetailsDict['DetailType']    = 'BENCHMARK ANALYSIS'        
        __MessageDetailsDict['BenchTimeFmt']  = "Benchmark Set:%m/%d/%y %I:%M%p[CT]"
        __MessageDetailsDict['DetailTimeFmt'] = "%m%d%y-%I:%M:%S%p[CT]"
        __MessageDetailsDict['Members'] = message.participants
        NewMessage = self.__BuildResultsMessage(DataMessage,BuildDetails)       
        return NewMessage
                
    def BuildProbeAnalysisMessageResults(self,message):
        sqlString = ("Select DISTINCT t1.UserName,(SELECT max(t2.timeStamp) FROM T" + message.chat_id[:5] + " as t2 WHERE t2.UserName <> 'bot' and t2.UserName = t1.UserName ORDER BY timeStamp DESC limit 1) as TimeStamp,(SELECT max(timeStamp) FROM T"+ message.chat_id[:5] + " WHERE UserName = 'bot' ORDER BY timeStamp DESC limit 1) as BotMin from T"+ message.chat_id[:5] +" as t1 where UserName <> 'bot' and TimeStamp >= (SELECT max(timeStamp) FROM T"+ message.chat_id[:5] + " WHERE UserName = 'bot' ORDER BY timeStamp DESC limit 1) group by TimeStamp, UserName")                   
        sql.execute(sqlString)
        DataMessage = sql.GetResultsDictArray()
        __MessageDetailsDict['TotalMembers']  = str(len(message.participants))
        __MessageDetailsDict['Type']          = 'Lurkers Caught:'
        __MessageDetailsDict['DetailType']    = 'PROBE ANALYSIS'        
        __MessageDetailsDict['BenchTimeFmt']  = "Probe Set:%m/%d/%y %I:%M%p[CT]"
        __MessageDetailsDict['DetailTimeFmt'] = "%m%d%y %I:%M:%S%p[CT]"
        __MessageDetailsDict['Members'] = message.participants
        NewMessage = self.__BuildResultsMessage(DataMessage,True)                     
        return NewMessage
        
    def BuildInactiveAnalysisMessageResults(self,message,BuildDetails = False):
        sqlString = "select UserName,(Select MIN(TimeStamp) from T" + message.chat_id[:5] + " where UserName = 'bot') as BotMin from T" + message.chat_id[:5] + " where UserName != 'bot'"
        print(sqlString)
        sql.execute(sqlString)
        Data             = sql.GetResultsDictArray()
        InnactiveMembers = self.__GetInnactiveMemberList(message,Data)
        RowCount         = str(len(InnactiveMembers))
        Totalmembers     = str(len(message.participants))
        BenchTime        = formatTimeFromEpoc(Data[0]['BotMin'],"Benchmark Set:%m/%d/%y-%I:%M%p[CT]\n")
        DetailType       = 'INACTIVE ANALYSIS'
        Members          = message.participants
        type             = 'Inactive:'
        NewMessage       = ""
        
        if(len(InnactiveMembers)) == 0:
            NewMessage = "ALL MEMBERS ACTIVE ^.^"
        else:
            if BuildDetails is True:
                for e in InnactiveMembers:
                    UserName     = e
                    TimeStamp    = ""               
                    if UserName in Members:
                        NewMessage += '@' + UserName + " " + TimeStamp + "\n"
                            
                NewMessage = "**RESULTS**\n" + NewMessage + BenchTime + type + " " + RowCount + " of " + Totalmembers + "\n" + DetailType
            else:
                NewMessage = "**RESULTS**" + NewMessage + "\n" + BenchTime + type + " " + RowCount + " of " + Totalmembers + "\n" + DetailType
        return NewMessage
        
        
        
        
        InactiveList = self.__BuildResultsMessage(DataMessage,True)  
        return InactiveList
                         
    def ResetBenchMark(self,message):
        self.__DeleteAllDataWithChatId(message.chat_id)
        self.__InsertUserEntry(message)
        self.InsertBotEntry(message)       
        DataMessage ="BENCHMARK HAS BEEN RESET"
        return DataMessage
                
    def SaveReceiptData(self,message):
        self.__DeleteAllEntrysSender(message)
        self.__InsertUserEntry(message)
        
    def ShouldBenchMarkBeReset(self,message):
        TimeStamp = self.__ReturnMinBotTimeStampFromChatID(message.chat_id)
        if TimeStamp is not None:
            return IsTimeGreaterThanDaysAdded(TimeStamp,14)
        else:
            return False
        