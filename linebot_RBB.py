# -*- coding: utf-8
from flask import Flask, request, abort, render_template

from linebot import (
    LineBotApi, WebhookHandler
)

from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import *
import json
import sys, os, time
import mimetypes
import configparser
import paho.mqtt.client as mqtt

def loadINI():
    cupspath = os.path.dirname(os.path.realpath(__file__))
    cfgpath = os.path.join(cupspath, 'linebot_RBBCar.conf')
    # 創建對象
    config = configparser.ConfigParser()
   # 讀取INI
    config.read(cfgpath, encoding='utf-8')     
    # 取得所有sections
    sections = config.sections()
    # 取得某section之所有items，返回格式為list
    linebot_access_token = config.get('common', 'linebot_access_token')
    linebot_secret = config.get('common', 'linebot_secret')
    device_list_str = config['common']['RBBCar_id_list']
    MQTT_Broker_url = config.get('MQTT_broker', 'url')
    MQTT_Broker_port = int(config.get('MQTT_broker', 'port'))
    return ([linebot_access_token , linebot_secret, device_list_str, MQTT_Broker_url, MQTT_Broker_port])

#目前所在絕對路徑
basepath = os.path.dirname(__file__)
print(basepath)
userid = ""
iniContent = loadINI()
print(iniContent)

app = Flask(__name__)

@app.route('/',methods=['GET','POST'])    
def control():
  if request.method=='GET':
    return render_template('index.html')
  else:        
    receive_json_obj = request.get_json() # 取得 json 資料物件 
    ctrl_msg = receive_json_obj['ctrl']
    print('ctrl_msg', ctrl_msg)
    client.publish("RBBCar/control/RBBCar0001", ctrl_msg, qos=1)
    return ctrl_msg # 回傳 json 資料字串
 
@app.route('/register',methods=['GET','POST'])    
def register(): 
   global userid
   cupspath = os.path.dirname(os.path.realpath(__file__))
   cfgpath = os.path.join(cupspath, 'linebot_cups.conf')
   # 創建對象
   config = configparser.ConfigParser()
   # 讀取INI
   config.read(cfgpath, encoding='utf-8')  
   if request.method=='GET':
      return render_template('register.html')
   else:
     device_input=request.form['deviceid']
     #userid=request.form['userid']  
     device_list_str = iniContent[2]
     device_list = device_list_str.split(",") 
     print(device_list)
     
     device_opts_list = config.options("device")
     print('device_opts_list', device_opts_list)     
     #device_num = config.get('device', 'cups_id')
     for item in device_list:
      if item == device_input:
       print(item,device_input)
       result = '註冊成功....'       
       config.set('device', userid, device_input)      
       config.write(open(cfgpath, "w"))
       break 
      else:
       result = 'RBBCar 裝置不存在....'               
     return render_template("register.html", data = result)       

@app.route('/goal',methods=['GET','POST'])    
def goal():
   return render_template("goal.html")
   
#Channel Access Token
line_bot_api = LineBotApi(iniContent[0])
# Channel Secret
handler = WebhookHandler(iniContent[1]) 

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
   global userid
   cupspath = os.path.dirname(os.path.realpath(__file__))
   cfgpath = os.path.join(cupspath, 'linebot_RBBCar.conf')
     # 創建對象
   config = configparser.ConfigParser()
     # 讀取INI
   config.read(cfgpath, encoding='utf-8') 
   userid = event.source.user_id
   print('userid', userid )
   if config.has_option('device',userid): 
     device_num = config.get('device', userid)
   else:
     config.set('device', userid, " ")
     config.write(open("linebot_cups.conf", "w"))
     device_num = config.get('device', userid)  
   if event.message.text == 'register': 
     message = TextSendMessage(text = '請點選 https://liff.line.me/1654118646-kzqdwpx0')     
   elif event.message.text == 'w':         
     if device_num == '':
       message = TextSendMessage(text = '未註冊列印裝置....')
     else:  
       message = printer_template()     
   elif event.message.text == 'page':
      if device_num == '':
        message = TextSendMessage(text = '未註冊列印裝置....')
      else:
        message = TextSendMessage(text = 'https://liff.line.me/1654118646-GYvYL8WQ')      
   else:
     message = TextSendMessage(text = '我不懂你的意思...')
   line_bot_api.reply_message(event.reply_token, message)

# paho callbacks
def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))

def on_message(client, userdata, msg): # 收到訂閱訊息的處理    
  print(msg.topic + " " + msg.payload.decode())       
  if msg.payload.decode() == 'finish': 
    print("receive finish message")      
    return render_template("index.html", data = "檔案列印完成....")  

if __name__ == "__main__": 
 client = mqtt.Client()  
 client.on_connect = on_connect  
 client.on_message = on_message  
 client.connect(iniContent[3], iniContent[4]) 
 client.loop_start()   
 app.run(debug=True, use_reloader=False, host='0.0.0.0',port=8080)
 
     