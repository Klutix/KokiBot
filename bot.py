from MessageBuilder import MessageBuilder
from flask import Flask, request, Response
from kik import KikApi, Configuration
from kik.messages import messages_from_json, TextMessage, ReceiptMessage, ReadReceiptMessage, SuggestedResponseKeyboard, TextResponse,StartChattingMessage
import os
reset = False
resetUser = ""
MessageHandler = MessageBuilder()
app = Flask(__name__)
kik = KikApi('BOTID', 'API_KEY')

#-------------------------KIK BOT CONFIG------------------------------------------------------

afeatures = {"manuallySendReadReceipts" : False,
            "receiveReadReceipts": True,
            "receiveDeliveryReceipts": False,
            "receiveIsTyping": False}
            
staticKeyboard = SuggestedResponseKeyboard(
                         responses=[TextResponse('BENCHMARK ANALYSIS'),
                                    TextResponse('PROBE ANALYSIS'),
                                    TextResponse('INACTIVE ANALYSIS'),
                                    TextResponse('HELP')]
                          )            
            
kik.set_configuration(Configuration(webhook='WEBHOOK',features = afeatures,static_keyboard = staticKeyboard))

banlist = ""

#list of users to have privadged access to reset benchmark
adminlist ={}


#-----------------Returns Keyboard based on if user in in adminlist or not
def SetKeyboard(user):
    if user in adminlist:
        Keyboard = [SuggestedResponseKeyboard(
            to=user,
            hidden=True,
            responses=[TextResponse('BENCHMARK ANALYSIS'),
                    TextResponse('PROBE ANALYSIS'),
                    TextResponse('INACTIVE ANALYSIS'),
                    TextResponse('RESET BENCHMARK')]
            )]
    else:
        Keyboard = [SuggestedResponseKeyboard(
            to=user,
            hidden=True,
            responses=[TextResponse('BENCHMARK ANALYSIS'),
                    TextResponse('PROBE ANALYSIS'),
                    TextResponse('INACTIVE ANALYSIS')]
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
    else:
        return False

def isInUserList(user):
    if user in userList:
        return True
    else:
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
    Body = '#BenchMarkAnalysis(b),(bd): Shows last captured activity for all members.\n'
    Body += '#ProbeAnalysis(p): Shows first occurence of activity since last probe.\n'
    Body += '#InactiveAnalysis(i),(id): Shows all members with no captured activity since benchmark date.\n'
    Body += '**Call @kokibot to set probe.\n'
    Body += '**Activate probe regulary to keep member data up to date.\n'
    Body += '**Benchmark will auto reset every 2 weeks upon initial activation.''' 

    kik.send_messages([
                    TextMessage(
                        to=messageObject.from_user,
                        body=Body,
                        keyboards =  SetKeyboard(messageObject.from_user)              
                    )
                ])
    
    return Response(status=200)
          
@app.route('/', methods=['POST'])
def incoming():
    if not kik.verify_signature(request.headers.get('X-Kik-Signature'), request.get_data()):
        return Response(status=403)
        
    messages = messages_from_json(request.json['messages'])
    for message in messages:
        #if isInUserList(message.from_user):
        if MessageHandler.ShouldBenchMarkBeReset(message) == True:
             MessageHandler.ResetBenchMark(message)
        if isinstance(message, TextMessage):
                global reset
                global resetUser
                DataMessage = ""
                if message.body =='BENCHMARK ANALYSIS' or message.body.upper() == "B" or message.body.upper() == "BD":
                    if "BD" not in message.body.upper():
                        DataMessage = MessageHandler.BuildBenchMarkAnalysisMessageResults(message)
                    else:
                        DataMessage = MessageHandler.BuildBenchMarkAnalysisMessageResults(message,True)
                elif message.body =='PROBE ANALYSIS' or message.body.upper() == "P":                    
                    DataMessage = MessageHandler.BuildProbeAnalysisMessageResults(message)
                elif message.body =='INACTIVE ANALYSIS' or message.body.upper() == "I" or message.body.upper() == "ID":                                         
                    if "ID" not in message.body.upper():
                        DataMessage = MessageHandler.BuildInactiveAnalysisMessageResults(message)
                    else:
                        DataMessage = MessageHandler.BuildInactiveAnalysisMessageResults(message,True) 
                elif message.body =='RESET BENCHMARK' or message.body.upper == "RB":
                    if isInAdminList(message.from_user):
                        reset = True
                        resetUser = message.from_user
                        return SendResetMessage(message)
                    else:
                        return SendNonAdminMessage(message)
                elif message.body.upper() =='YES' and message.from_user == resetUser and reset == True:
                    DataMessage = MessageHandler.ResetBenchMark(message)
                    reset = False               
                elif message.body.upper() =='NO' and message.from_user == resetUser and reset == True:
                    reset = False
                    return SendResetCancledMessage(message)
                elif message.body.upper() == 'HELP':
                    return SendHelpMessage(message)
                else:                
                    reset = False                
                    DataMessage =  '**Probing for Activity**'
                    MessageHandler.InsertBotEntry(message)
                if reset == False:
                    return SendDefaultMessage(message,DataMessage)
                    
        if isinstance(message, ReadReceiptMessage):            
            MessageHandler.SaveReceiptData(message)
            return Response(status=200)
    
if __name__ == '__main__':
     app.debug = True
     port = int(os.environ.get("PORT", 5000))
     app.run(host='0.0.0.0', port=port)