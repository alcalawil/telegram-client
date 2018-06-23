from telethon import TelegramClient, events

from datetime import datetime, timedelta
import os 
import json
import time
import requests

# Load config file
with open('config.json') as fileConfig:
    config = json.load(fileConfig)
# Load channels file
with open('channels.txt') as fileChannels:
    listChannels = fileChannels.readlines()
    fileChannels.close()
# Connect to Telegram Server
client = TelegramClient(os.path.abspath(
    'session'), config["telegram"]["api_id"], config["telegram"]["api_hash"],proxy=None,
                            update_workers=4,
                            spawn_read_thread=False)
client.start(config["telegram"]["phone"])
print('Welcome ' + client.get_me().first_name)


lastID = {}
def messageIsBuySignal(msg):
    result = False
    try:
    # msg = msg.decode('utf-8') # Not proved
        msg = msg.translate(
            {ord(c): " " for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"}).lower()
        if msg.find("buy") > -1:
            result = True
    except:
        print("Problemas con la codificacion")
    return result

def isListingSignalBinance(msg):
    result = False
    msg= msg.lower()
    if "binance lists" in msg or "binance will list" in msg:
        result = True
    return result

def extractListingCoinBinance(msg):
    coin = 'not found'
    if "(" in msg and ")" in msg:
        pOpen = msg.index("(")
        pClose = msg.index(")")
        coin = msg[ pOpen + 1 : pClose]    
    return coin

def sendRequest(coin,exch):        
    url = config["httpRequest"]["host"]
    resp = requests.post(url=url, json={"token":coin,"refExchange":exch})
    data = resp.json()
    print(data)


def checkForBuySignals():
    hoursBefore = config["hoursBefore"]
    for n, channel in enumerate(listChannels, 1):  
        print ("########################")  
        channel = channel.replace("\n", "")
        print(channel)
        try:
            # first is more recent than last
            response = client.get_messages(channel, limit=500)
            pastDate = datetime.now() - timedelta(hours=hoursBefore)
            print(pastDate)
            if channel in lastID:
                messages = list(filter(lambda msg: msg.date > pastDate and messageIsBuySignal(msg.message)
                                       and msg.id > lastID[channel], response))
            else:
                messages = list(filter(lambda msg: msg.date > pastDate and messageIsBuySignal(msg.message), response))
                lastID[channel] = response[0].id
            if len(messages)>0:
                print(lastID)
                print(len(messages))
                print(messages)
                print(messages[len(messages)-1].date)

                # client.forward_messages(
                #     config["telegram"]["forwardTo"],  # to which entity you are forwarding the messages
                #     messages  # the messages to forward
                # )                
        except Exception as ex:
            print(ex)
            print("Username not found: " + channel)
    
def isListingSignalOkex(msg):
    result = False
    msg= msg.lower()
    if "now listed on OKEx" in msg or "Now Available" in msg:
        result = True
    return result

def extractListingCoinOkex(msg):
    coin = 'not found'
    if "(" in msg and ")" in msg:
        pOpen = msg.index("(")
        pClose = msg.index(")")
        coin = msg[ pOpen + 1 : pClose]    
    return coin

def main():
    # checkForBuySignals()
    print('Old signals were forwarded')
    client.idle()


@client.on(events.NewMessage)
def my_event_handler(event):
    print("New Message")
    if event.is_channel == True:
        event.forward_to('alcalawbot')
    
    channelId = event.message.fwd_from.channel_id
    if channelId == 1146915409: # Binance Annoucement
        message = event.message.message
        print(message)
        if isListingSignalBinance(message) == True:
            print("Message is a listing signal in Binance")
            print("Trying to extract coin")
            coin = extractListingCoinBinance(message)
            print(coin)
            sendRequest(coin,'binance')
        else:
            print('message is not a listing signal in Binance')  
    elif channelId == 1161923966: # OKEx
        if isListingSignalOkex(message) == True:
            print("Message is a listing signal in Okex")
            print("Trying to extract coin")
            coin = extractListingCoinOkex(message)
            print(coin)
            sendRequest(coin,'okex')
        else:
            print('message is not a listing signal in Okex') 



main()
