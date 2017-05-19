import pymysql
import traceback

#********************************************************************sqlitetasty**********************************************************************************    
class MySqlTasty():
    __conn = None
    __DBName = ''
    __UserName = ''
    __Password = ''
    __Host = ''
    __resultsDictArray = []
    __resultsIndexArray = []
    __DataSetFields = []
    __CommitAfterExecute = True
    __CloseAfterExecute  = True
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - PRIVATE FUNCTIONS - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            
    def __PopulateDataSetFields(self,cursor):
        global __DataSetFields
        try:           
            __DataSetFields = [None] * len(cursor.description)
            for i in range(len(cursor.description)):
                __DataSetFields[i] = cursor.description[i][0]
        except:
            __DataSetFields = []
    def __CreateDictFromFieldListAndRowData(self,row):
        Dict = {}
        for i in range(len(__DataSetFields)):
            Dict[__DataSetFields[i]] = row[i]
        return Dict
        
    def __CreateListFromRowData(self,row):
        list = []
        for i in row:
            list.append(i)
        return list
        
    def __PopulateResultData(self,cursor):
        global __resultsDictArray
        global __resultsIndexArray
        __resultsDictArray = []
        __resultsIndexArray = []
        for row in cursor:
            dict = self.__CreateDictFromFieldListAndRowData(row)
            list = self.__CreateListFromRowData(row)
            __resultsDictArray.append(dict)
            __resultsIndexArray.append(list)

                           
    def __SetLoginInfo(self,DatabaseName,UserName,Password,Host):
        global __DBName
        global __UserName
        global __Password
        global __Host
        __DBName = DatabaseName
        __UserName = UserName
        __Password = Password
        __Host = Host
        
    def __PrintError(self,err):
        try:
            traceback.print_exc()
        except:
            print(err)
            
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - PUBLIC FUNCTIONS - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
 
    def __init__(self, DB, User, Passwd, Host):        
        self.connect(DB, User, Passwd, Host)
        self.SetAutoCommit(True)
        self.SetAutoClose(True)
        self.close();
        
    def SetAutoClose(self, boolean):
        global __CloseAfterExecute
        __CloseAfterExecute = boolean
       
    def SetAutoCommit(self, boolean):
        global __CommitAfterExecute
        __CommitAfterExecute = boolean
   
    def connect(self,DB,User,Passwd,Host):
        global __conn
        self.__SetLoginInfo(DB,User,Passwd,Host)
        try:
            __conn = pymysql.connect(
            db=DB,
            user=User,
            passwd=Passwd,
            host=Host)
        except pymysql.Error as err:
            self.__PrintError(err)
       
    def close(self):
        global __conn
        try:
            __conn.close()
        except pymysql.Error as err:
            self.__PrintError(err)
       
    def commit(self):
        global __conn
        try:
            __conn.commit()
        except pymysql.Error as err:
            self.__PrintError(err)

    def GetRowCount(self):
        try:
            return len(__resultsDictArray)
        except:
            return 0
    def GetFieldCount(self):
        try:
            return  len(__resultsDictArray[0])
        except:
            return 0
            
    def GetFieldsList(self):
        try:
            return __DataSetFields
        except:
            return []
            
    def GetResultsDictArray(self):
        try:
            return __resultsDictArray
        except Exception as err:
            return []
            
    def GetResultsIndexArray(self):
        try:
            return __resultsIndexArray
        except Exception as err:
            return []
   
    def execute(self,sqlstring):        
        self.connect(__DBName,__UserName,__Password,__Host)
        try:
            c  = __conn.cursor()           
            c.execute(sqlstring)
            self.__PopulateDataSetFields(c)
            self.__PopulateResultData(c)
            if __CommitAfterExecute is True:__conn.commit()                    
            if __CloseAfterExecute  is True:__conn.close()              
        except pymysql.Error as err:
            self.__PrintError(err)
                        
               
#***************************************************************************************************************************************************      
        
    

    
    