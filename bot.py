from MessageBuilder import MessageBuilder
from flask import Flask, request, Response
from kik import KikApi, Configuration
from kik.messages import messages_from_json, TextMessage, ReceiptMessage, ReadReceiptMessage, SuggestedResponseKeyboard, TextResponse,StartChattingMessage
import os
import requests
reset = False
resetUser = ""
MessageHandler = MessageBuilder()
app = Flask(__name__)
kik = KikApi('BOTNAME', 'APIKEY')

#-------------------------KIK BOT CONFIG------------------------------------------------------

afeatures = {"manuallySendReadReceipts" : False,
            "receiveReadReceipts": True,
            "receiveDeliveryReceipts": False,
            "receiveIsTyping": False}
            
staticKeyboard = SuggestedResponseKeyboard(
                         responses=[TextResponse('Set Probe'),
                                    TextResponse('Benchmark Analysis'),
                                    TextResponse('Probe Analysis'),
                                    TextResponse('Inactive Analysis'),
                                    TextResponse('Help')]
                          )            
            
kik.set_configuration(Configuration(webhook='webhook',features = afeatures,static_keyboard = staticKeyboard))

banlist = ""
adminlist ={'kokimetsu','houtarou_','originalparakeet',"svennyberg","gaytheistjake","icancamelcase","adminship","xitulk"}
userList = {'kokimetsu','houtarou_','originalparakeet',"svennyberg","gaytheistjake","muzzysquad"}

#-----------------Returns Keyboard based on if user in in adminlist or not
def SetKeyboard(user):
    if user in adminlist:
        Keyboard = [SuggestedResponseKeyboard(
            to=user,
            hidden=True,
            responses=[TextResponse('Set Probe'),
                        TextResponse('Benchmark Analysis'),
                        TextResponse('Probe Analysis'),
                        TextResponse('Inactive Analysis'),
                        TextResponse('Reset Benchmark')]
            )]
    else:
        Keyboard = [SuggestedResponseKeyboard(
            to=user,
            hidden=True,
            responses=[TextResponse('Set Probe'),
                        TextResponse('Benchmark Analysis'),
                        TextResponse('Probe Analysis'),
                        TextResponse('Inactive Analysis'),
                        TextResponse('Help')]
            )]        
    return Keyboard

#-------Sends reset message---------------------       
def SendResetMessage(messageObject):
    kik.send_messages([
                        TextMessage(
                            to=messageObject.from_user,
                            chat_id=messageObject.chat_id,
                            body="Resetting will clear all previously recorded member data. Do you wish to continue?",
                            keyboards =  [SuggestedResponseKeyboard(
                                             to=messageObject.from_user,
                                             hidden=True,
                                             responses=[TextResponse('YES'),
                                                        TextResponse('NO')]

                                            )]              
                        )
                    ])

    return Response(status=200)

#----------Sends Reset Canceled Mesasge---------
def SendResetCancledMessage(messageObject):
    kik.send_messages([
                        TextMessage(
                            to=messageObject.from_user,
                            chat_id=messageObject.chat_id,
                            body="Reset Canceled",
                            keyboards = SetKeyboard(messageObject.from_user) 
                                        
                        )
                    ])
    return Response(status=200)
#----------Sends Default Message------------
def SendDefaultMessage(messageObject,messageToDelivered):
        kik.send_messages([
                        TextMessage(
                            to=messageObject.from_user,
                            chat_id=messageObject.chat_id,
                            body=messageToDelivered,
                            keyboards =  SetKeyboard(messageObject.from_user)              
                        )
                    ])
        
        return Response(status=200)
        
def isInAdminList(user):
    if user in adminlist:
        return True
    return False

def isInUserList(user):
    if user in userList:
        return True
    return False
    
                       
def SendNonAdminMessage(messageObject):  
    kik.send_messages([
                    TextMessage(
                        to=messageObject.from_user,
                        chat_id=messageObject.chat_id,
                        body="Sorry you dont have rights to use this feature..:P",
                        keyboards =  SetKeyboard(messageObject.from_user)              
                    )
                ])
    
    return Response(status=200)
        
def SendHelpMessage(messageObject):
    Body = '#BenchMarkAnalysis(b),(b details) or (bd): Shows last captured activity for all members.\n'
    Body += '#ProbeAnalysis(p): Shows first occurence of activity since last probe.\n'
    Body += '#InactiveAnalysis(i),(i details) or (id): Shows all members with no captured activity since benchmark date.\n'
    Body += '**Call @kokibot to set probe.\n'
    Body += '**Set probe regulary to keep member data up to date.\n'
    Body += '**Benchmark will auto reset every 2 weeks upon initial activation.''' 

    kik.send_messages([
                    TextMessage(
                        to=messageObject.from_user,
                        chat_id = messageObject.chat_id,
                        body=Body,
                        keyboards =  SetKeyboard(messageObject.from_user)              
                    )
                ])
    
    return Response(status=200)
    
def remove_non_ascii_2(text):
    return re.sub(r'[^\x00-\x7F]',' ', text)
    
def get_participants_list(IdArray):
    return list(map(lambda x: kik.get_user(x).first_name.encode('utf-8','replace')+" "+kik.get_user(x).last_name.encode('utf-8','replace'),IdArray)) 
    
        
    
          
@app.route('/', methods=['POST'])
def incoming():
    if not kik.verify_signature(request.headers.get('X-Kik-Signature'), request.get_data()):
        return Response(status=403)
        
    messages = messages_from_json(request.json['messages'])
    for message in messages:
              
        if MessageHandler.ShouldBenchMarkBeReset(message) == True:
             MessageHandler.ResetBenchMark(message,FullName)
        if isinstance(message, TextMessage):
            FullName = kik.get_user(message.from_user).first_name.encode('utf-8','replace')+" "
            FullName += kik.get_user(message.from_user).last_name.encode('utf-8','replace')
            participants = get_participants_list(message.participants)
            global reset
            global resetUser
            #MessageHandler.UpdateDailyUsers(message)
            DataMessage = ""
            if message.body.upper() =='BENCHMARK ANALYSIS' or message.body.upper() == "B" or message.body.upper() == "B DETAILS"  or message.body.upper() == "BD" :
                if "B DETAILS" not in message.body.upper() and "BD" not in message.body.upper():
                    DataMessage = MessageHandler.BuildBenchMarkAnalysisMessageResults(message,False,participants)
                else:
                    DataMessage = MessageHandler.BuildBenchMarkAnalysisMessageResults(message,True,participants)
            elif message.body.upper() =='PROBE ANALYSIS' or message.body.upper() == "P":                    
                DataMessage = MessageHandler.BuildProbeAnalysisMessageResults(message,participants)
            elif message.body.upper() =='INACTIVE ANALYSIS' or message.body.upper() == "I" or message.body.upper() == "I DETAILS" or message.body.upper() == "ID":                                         
                if "I DETAILS" not in message.body.upper() and "ID" not in message.body.upper():
                    DataMessage = MessageHandler.BuildInactiveAnalysisMessageResults(message,False,participants)
                else:
                    DataMessage = MessageHandler.BuildInactiveAnalysisMessageResults(message,True,participants) 
            elif message.body.upper() =='RESET BENCHMARK' or message.body.upper() == "RB":
                if isInAdminList(FullName):
                    reset = True
                    resetUser = FullName
                    return SendResetMessage(message)
                else:
                    return SendNonAdminMessage(message)
            elif message.body.upper() =='YES' and FullName == resetUser and reset == True:
                DataMessage = MessageHandler.ResetBenchMark(message,FullName)
                reset = False               
            elif message.body.upper() =='NO' and FullName == resetUser and reset == True:
                reset = False
                return SendResetCancledMessage(message)
            elif message.body.upper() == 'HELP':
                return SendHelpMessage(message)
            else:                
                reset = False                
                DataMessage = u'\U0001f604'.encode('utf-8','replace')
                MessageHandler.InsertBotEntry(message)
            if reset == False:
                return SendDefaultMessage(message,DataMessage)
                    
        elif isinstance(message, ReadReceiptMessage):
            FullName = kik.get_user(message.from_user).first_name.encode('utf-8','replace')+" "
            FullName += kik.get_user(message.from_user).last_name.encode('utf-8','replace')
            
            MessageHandler.SaveReceiptData(message,FullName) #hh
            return Response(status=200)
        else:
            DataMessage = 'Use @Kokibot HELP for command list details'
            MessageHandler.InsertBotEntry(message)
            return SendDefaultMessage(message,DataMessage)
        
    
if __name__ == '__main__':
     app.debug = True
     port = int(os.environ.get("PORT", 5000))
     app.run(host='0.0.0.0', port=port)
