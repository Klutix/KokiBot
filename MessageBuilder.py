import sqlite3
import os
import os.path
import sys
import datetime
import time
from kik import KikApi
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
        sql = MySqlTasty('kokibot','Koki','311311Susi','107.170.42.28')
        __MessageDetailsDict = dict.fromkeys(['TotalMembers','Type','DetailType','BenchTimeFmt','BenchTime','DetailTimeFmt','DetailTime','Members'])
                
    def __CreateTableFromChatID(self,messageChatID):
            try:
                sql.execute("CREATE TABLE IF NOT EXISTS T" + messageChatID[:10] + " (UserName TEXT ,TimeStamp TEXT)")
            except:
                pass
                        
    def __DeleteAllDataWithChatId(self,messageChatID):
        sqlString = "Delete from T" + str(messageChatID[:10]) + ""
        sql.execute(sqlString)
                                        
    def __InsertUserEntry(self,message,from_user):
        self.__CreateTableFromChatID(message.chat_id)
        sqlString = "INSERT INTO T"+ message.chat_id[:10] +  " VALUES ('" + from_user+ "','" + str(message.timestamp)+ "')"        
        sql.execute(sqlString)
        
    def InsertBotEntry(self,message):
        self.__CreateTableFromChatID(message.chat_id)
        sql.execute("INSERT INTO T"+ message.chat_id[:10] +  " VALUES ('bot','"+str(message.timestamp)+"')")
        
    def __DeleteAllEntrysSender(self,message,from_user):
        sql.execute("Delete from T" + message.chat_id[:10] + " where UserName = '" + from_user+"'")

    def __ReturnMinBotTimeStampFromChatID(self,messageChatID):
        sqlString = "SELECT MIN(TimeStamp) as TimeStamp from T" + messageChatID[:10]+ " WHERE UserName = 'bot'"
        sql.execute(sqlString)
        Data = sql.GetResultsDictArray()
        if len(Data) > 0:
            return Data[0]['TimeStamp']
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
                #NewMessage = "**RESULTS**\n" + NewMessage + "\n" + BenchTime +"\n" + type + " " + RowCount + " of " + Totalmembers + "\n" + DetailType
                NewMessage = "**RESULTS**\n" + NewMessage + "\n" +"Since " + BenchTime +"there have been "+ RowCount + type +" of " + Totalmembers + "\n" + DetailType
            else:
                NewMessage = "**RESULTS**" + NewMessage + "\n" + BenchTime +"\n" + type + " " + RowCount + " of " + Totalmembers + "\n" + DetailType
        else:
            NewMessage = "No Data has been captured."
        return NewMessage
        
    def __GetInnactiveMemberList(self,message,Data,participants):
        List  = []
        Found = False
        for Name in participants:
            Found = False
            for index in range(0,sql.GetRowCount()):
                if Name == Data[index]['UserName']:
                    Found = True
            if Found is False:
                List.append(Name)
        List = sorted(List)
        return List
        
    def BuildBenchMarkAnalysisMessageResults(self,message,BuildDetails = False,participants=[]):
        global __MessageDetailsDict
        sqlString = "Select DISTINCT t1.UserName as UserName, t1.TimeStamp as TimeStamp ,(SELECT MIN(TimeStamp) from T" + message.chat_id[:10] + " WHERE UserName = 'bot') as BotMin from T" + message.chat_id[:10] + " as t1 where  UserName <> 'bot' and t1.TimeStamp = (Select Max(t2.timestamp) from T" + message.chat_id[:10] + " as t2 where UserName <> 'bot' and t2.UserName = t1.UserName) and UserName in ("+ListFromArray(participants)+") group by TimeStamp, UserName " 
        sql.execute(sqlString)
        Data = sql.GetResultsDictArray()
        __MessageDetailsDict['TotalMembers']  = str(len(participants))
        __MessageDetailsDict['Type']          = ''#'Active Members:'
        __MessageDetailsDict['DetailType']    = 'BENCHMARK ANALYSIS'        
        __MessageDetailsDict['BenchTimeFmt']  = "%m/%d/%y %I:%M%p[CT]"#"Benchmark Set:%m/%d/%y %I:%M%p[CT]"
        __MessageDetailsDict['DetailTimeFmt'] = "%m%d%y-%I:%M:%S%p[CT]"
        __MessageDetailsDict['Members'] = participants
        
        if sql.GetRowCount() > 0:
            RowCount     = str(sql.GetRowCount())
            Totalmembers = str(len(participants))
            BenchTime    = formatTimeFromEpoc(Data[0]['BotMin'],"%m/%d/%y")
            DetailType   = 'BENCHMARK ANALYSIS'  
            Members      = participants
            type         = ''#'Active Members:'
            NewMessage = ""
            
            if BuildDetails is True:
                for e in range(0,sql.GetRowCount()):
                    UserName     = Data[e]['UserName']
                    TimeStamp    = formatTimeFromEpoc(Data[e]['TimeStamp'],__MessageDetailsDict['DetailTimeFmt']) if __MessageDetailsDict['DetailTimeFmt'] != "" else ""               
                    if UserName in Members:            
                        NewMessage += '@' + UserName + " " + TimeStamp + "\n"
                NewMessage += "\n^Here is the last captured details for all active members."    
                #NewMessage = "**RESULTS**\n" + NewMessage + "\n" + BenchTime +"\n" + type + " " + RowCount + " of " + Totalmembers + "\n" + DetailType
                #NewMessage = "**RESULTS**\n" + NewMessage + "\n" + "Since benchmark:" + BenchTime + " there are " + RowCount + " active members out of " + TotalMembers
                
            NewMessage = "**RESULTS**\n" + NewMessage + " There are " + RowCount + " active in chat out of " + Totalmembers + " since " + BenchTime  + "."
            
        else:
            NewMessage = "No Data has been captured."
        return NewMessage

                
        #NewMessage = self.__BuildResultsMessage(DataMessage,BuildDetails)       
        return NewMessage
        
    def GetFormatedDateDiff(self,date1,date2):
        delta = date1 - date2
        timeDiff = "..";
        if delta.days > 0:
            timeDiff += str(delta.days) + "d ago.."
        elif delta.total_seconds()//3600 > 0:
            timeDiff += str(int(delta.seconds//3600 - (24*delta.days))) + "h ago.."
        elif delta.total_seconds() > 60:
            timeDiff += str(int((delta.seconds//60)%60)) + "m ago.."
        else:
            timeDiff += str(int(delta.total_seconds())) + "s ago.."            
        return timeDiff
                
    def BuildProbeAnalysisMessageResults(self,message,participants):
        sqlString = ("Select DISTINCT t1.UserName,(SELECT max(t2.timeStamp) FROM T" + message.chat_id[:10] + " as t2 WHERE t2.UserName <> 'bot' and t2.UserName = t1.UserName ORDER BY timeStamp DESC limit 1) as TimeStamp,(SELECT max(timeStamp) FROM T"+ message.chat_id[:10] + " WHERE UserName = 'bot' ORDER BY timeStamp DESC limit 1) as BotMin from T"+ message.chat_id[:10] +" as t1 where UserName <> 'bot' and TimeStamp >= (SELECT max(timeStamp) FROM T"+ message.chat_id[:10] + " WHERE UserName = 'bot' ORDER BY timeStamp DESC limit 1) group by TimeStamp, UserName")                   
        sql.execute(sqlString)
        Data = sql.GetResultsDictArray()
        __MessageDetailsDict['TotalMembers']  = str(len(participants))
        __MessageDetailsDict['Type']          = 'Lurkers Caught:'
        __MessageDetailsDict['DetailType']    = 'Probe Analysis'        
        __MessageDetailsDict['BenchTimeFmt']  = "%y-%m-%d %H:%M:%S.%f"#"Probe Set:%m/%d/%y %I:%M%p[CT]"
        __MessageDetailsDict['DetailTimeFmt'] = "%y-%m-%d %H:%M:%S.%f"
        __MessageDetailsDict['Members'] = participants
        
        
        RowCount     = str(sql.GetRowCount())
        Totalmembers = str(len(participants))
        BenchTime    = formatTimeFromEpoc(Data[0]['BotMin'],"%y-%m-%d %H:%M:%S.%f")
        DetailType   = 'PROBE ANALYSIS'  
        Members      = participants
        type         = ''#'Active Members:'
        NewMessage = ""
        

        for e in range(0,sql.GetRowCount()):
            UserName     = Data[e]['UserName']
            TimeStamp    = formatTimeFromEpoc(Data[e]['TimeStamp'],__MessageDetailsDict['DetailTimeFmt']) if __MessageDetailsDict['DetailTimeFmt'] != "" else ""               
            BenchTime    = formatTimeFromEpoc(Data[0]['BotMin'],'%y-%m-%d %H:%M:%S.%f') 
             #test ---          
            TimeNow = datetime.datetime.now()
            
            #convert All into datetime object so they pluged in and subtracted against by GetFormatedDateDiff
            TimeNow = datetime.datetime.strptime(str(TimeNow),'%Y-%m-%d %H:%M:%S.%f')
            TimeStamp = datetime.datetime.strptime(TimeStamp, '%y-%m-%d %H:%M:%S.%f')
            BenchTime = datetime.datetime.strptime(BenchTime, '%y-%m-%d %H:%M:%S.%f')
            BenchTime = self.GetFormatedDateDiff(TimeNow,BenchTime)
            TimeStamp =self.GetFormatedDateDiff(TimeNow,TimeStamp)
            #-------------------------------
            if UserName in Members:            
                NewMessage += '@' + UserName + " " + TimeStamp + "\n"
        #NewMessage = "**RESULTS**\n" + NewMessage + "\n" + BenchTime +"\n" + type + " " + RowCount + " of " + Totalmembers + "\n" + DetailType
        #NewMessage = "**RESULTS**\n" + NewMessage + "\n" + "Since benchmark:" + BenchTime + " there are " + RowCount + " active members out of " + TotalMembers
        NewMessage = "**RESULTS**\n" + NewMessage + "\n" + RowCount  + " out of "+ Totalmembers + " members were caught by the probe since it was set " + BenchTime+"." 
        
        return NewMessage
        
    

        
    def BuildInactiveAnalysisMessageResults(self,message,BuildDetails = False,participants=[]):
        #self.__CreateTempTableFromParticpants(participants)
        #sqlString = "select UserName,(Select MIN(TimeStamp) from " + message.chat_id + " where UserName = 'bot') as BotMin from TMP where UserName not in (Select UserName from " + message.chat_id + " where UserName != 'bot')"
        sqlString = "select UserName,(Select MIN(TimeStamp) from T" + message.chat_id[:10] + " where UserName = 'bot') as BotMin from T" + message.chat_id[:10] + " where UserName != 'bot'"
        print(sqlString)
        sql.execute(sqlString)
        Data             = sql.GetResultsDictArray()
        InnactiveMembers = self.__GetInnactiveMemberList(message,Data,participants)
        RowCount         = str(len(InnactiveMembers))
        Totalmembers     = str(len(participants))
        BenchTime        = formatTimeFromEpoc(Data[0]['BotMin'],"%m/%d/%y")
        DetailType       = 'INACTIVE ANALYSIs'
        Members          = participants
        type             = 'Inactive:'
        NewMessage       = ""
        
        if(len(InnactiveMembers)) == 0:
            NewMessage = "All members active ^.^"
        else:
            if BuildDetails is True:
                for e in InnactiveMembers:
                    UserName     = e
                    TimeStamp    = ""               
                    if UserName in Members:
                        NewMessage += '@' + UserName + " " + TimeStamp + "\n"
                    else:
                        Totalmembers = str(int(Totalmembers)-1)
                #NewMessage = "**RESULTS**\n" + NewMessage + BenchTime + type + " " + RowCount + " of " + Totalmembers + "\n" + DetailType
                #NewMessage = "**RESULTS**\n" + NewMessage + "\n" + "Since " + BenchTime + " there are " + RowCount + " inactive members out of " + TotalMembers
        NewMessage = "**RESULTS**\n" + NewMessage + "\n" + " There are " + RowCount + " inactive members out of " + Totalmembers + " since " + BenchTime  + "."    
            
            #NewMessage = "**RESULTS**" + NewMessage + "\n" + BenchTime + type + " " + RowCount + " of " + Totalmembers + "\n" + DetailType             
            
        return NewMessage
        
        
        
        
        #InactiveList = self.__BuildResultsMessage(DataMessage,True)  
        #return InactiveList

    def UpdateDailyUsers(self,message,from_user):
        count = 1
        sql.execute("Select UserName, count from TDAILY where UserName = '"+from_user+"'")
        Data = sql.GetResultsDictArray() 
        if sql.GetRowCount() > 0:
            count =  int(Data[0]['count']) + 1 #update the count
            sql.execute("Delete from TDAILY where UserName = '" + from_user+"'")        
        sql.execute("INSERT INTO TDAILY VALUES ('" + from_user + "','"+str(message.timestamp)+"','"+str(count)+"')")
            
    
                         
    def ResetBenchMark(self,message,from_user):
        self.__DeleteAllDataWithChatId(message.chat_id)
        self.__InsertUserEntry(message,from_user)
        self.InsertBotEntry(message)       
        DataMessage ="BENCHMARK HAS BEEN RESET"
        return DataMessage
                
    def SaveReceiptData(self,message,from_user):
        print(from_user)
        self.__DeleteAllEntrysSender(message,from_user)
        self.__InsertUserEntry(message,from_user)
        
    def ShouldBenchMarkBeReset(self,message):
        TimeStamp = self.__ReturnMinBotTimeStampFromChatID(message.chat_id)
        if TimeStamp is not None:
            return IsTimeGreaterThanDaysAdded(TimeStamp,14)
        else:
            return False
        
