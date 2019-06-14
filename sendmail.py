#!/usr/bin/python3.5
import smtplib
import time
import threading
import xml.dom.minidom
import urllib.request
import packet_pb2
import socket

from xml.dom.minidom import parse
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

#用户信息对象
class userobj:
    name = ""
    email = ""
    local = ""
    time = []
    def __init__(self,name,email,local,time):
        self.name = name
        self.email = email
        self.local = local
        self.time = time



#服务器信息对象
class serverobj:
    hostname=""#smtp 服务器hostname
    port=""#smtp 端口 默认25
    sslport=""#ssl port 默认465
    user=""
    passwd=""
    loghost=""#日志服务器host
    logport=""#日志服务器端口
    def __init__(self,hostname,port,sslport,user,passwd,loghost,logport):
        self.hostname = hostname
        self.port = port
        self.sslport = sslport
        self.user = user
        self.passwd = passwd
        self.loghost = loghost
        self.logport = logport



#打印日志到 logserver
def to_log(message):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    host = server.loghost 
    port = server.logport

    s.connect((host,int(port)))

    packet = packet_pb2.Packet()
    packet.command = 3

    loginfo = packet_pb2.LogInfo()
    loginfo.server = bytes("smtp send server".encode('utf-8'))
    loginfo.reason = bytes(message.encode('utf-8'))
    packet.serialized =loginfo.SerializeToString()

    str_packet = packet.SerializeToString()
    len_packet = len(str_packet)

    s.send(len_packet.to_bytes(4,byteorder='big'))
    s.send(str_packet)
    s.close()



#计算到配置时间的秒数
def get_timer_value(atTime):
    int_time_S = int(time.strftime("%S",time.localtime()))
    int_time_M = int(time.strftime("%M",time.localtime()))
    int_time_H = int(time.strftime("%H",time.localtime()))
    
    at = atTime.split(':')
    int_stime_S = int(at[2])
    int_stime_M = int(at[1])
    int_stime_H = int(at[0])

    timer_value = 0
    now_value = int_time_S + int_time_M*60+int_time_H*3600
    s_value = int_stime_S + int_stime_M*60+int_stime_H*3600

    if now_value <s_value:
        timer_value = s_value-now_value
    elif now_value > s_value:
        timer_value = 86400-(now_value-s_value)
    else:
        timer_value = 86400
    return timer_value




#定时器回调函数
def timer_func(server,user,local_map):
    message = packet_message(user,local_map)
    send_mail(server.hostname,server.sslport,server.user,server.passwd,server.user,user.email,message)

    timer = threading.Timer(86400,timer_func,[server,user,local_map])
    timer_list.append(timer)
    timer_list[len(timer_list)-1].start()
    to_log("new timer start "+"86400"+"seconds will call")



#构造发送信息的包装函数
def packet_message(userobj,local_map):
    wether_message= get_wether_info(local_map[userobj.local])
    wether_message="今天的天气信息是:"+wether_message+"</br>"
    welcome_message="</br><h1>"+"这里是妹抖酱每天的定时天气推送~~~~~"+" 祝你有快乐美好的一天:"+userobj.name+"</h1></br>"
    message = MIMEMultipart('related')
    content_message = '<html><body><img src="cid:imageid" alt="imageid">'+welcome_message+wether_message+'</body></html>'
    content = MIMEText(content_message,'html','utf-8')
    title = '来自黄金的魔女的问候' 

    message['From'] = sender
    message['To'] = userobj.email 
    message['Subject'] = title

    message.attach(content)

    file=open("./emoj/normal.png",'rb')
    img_data = file.read()
    file.close()

    img=MIMEImage(img_data)
    img.add_header('Content-ID','imageid')
    message.attach(img)
    return message



#发送邮件的包装函数
def send_mail(mail_host,mail_sslport,mail_user,mail_pass,sender,receivers,message):
    try:
        smtpObj = smtplib.SMTP_SSL(mail_host,int(mail_sslport))  
        smtpObj.login(mail_user, mail_pass)  
        smtpObj.sendmail(sender, receivers, message.as_string()) 
        to_log("mail has been send successfully.")
        to_log("***********************")
        to_log(time.strftime("%H:%M:%S",time.localtime()))
        to_log("send mail to"+receivers)
        to_log("***********************")
    except smtplib.SMTPException as e:
        to_log(e)



#城市配置文件映射解析函数
def get_localurl_map():
    DOMTree_local = xml.dom.minidom.parse("localurl.xml")
    localurl = DOMTree_local.documentElement
    locals = localurl.getElementsByTagName("local")
    local_map = {}
    for local in locals:
        local_name = ""
        local_url = ""
        if local.hasAttribute("name"):
            local_name = local.getAttribute("name")
        local_url = local.childNodes[0].data
        local_map[local_name]=local_url
    return local_map



#获取天气信息
def get_wether_info(weburl):
    response = urllib.request.urlopen(weburl)
    oripage = response.read().decode('utf8')
    index = oripage.find("hidden_title")
    htmlpage = oripage[index:]
    index0 = htmlpage.find('=')
    htmlpage = htmlpage[index0+2:]
    index1 = htmlpage.find('>')
    htmlpage = htmlpage[:index1]
    index2 = htmlpage.find('"')
    message = htmlpage[:index2]
    return message



#解析服务器配置文件
def get_smtpserver_config():
    DOMTree_smtp = xml.dom.minidom.parse("./smtpserver.xml")
    smtpserver = DOMTree_smtp.documentElement
    hostname = smtpserver.getElementsByTagName("hostname")[0]
    mail_host = hostname.childNodes[0].data
    port     = smtpserver.getElementsByTagName("port")[0]
    mail_port = port.childNodes[0].data
    sslport  = smtpserver.getElementsByTagName("sslport")[0]
    mail_sslport = sslport.childNodes[0].data
    user = smtpserver.getElementsByTagName("user")[0]
    mail_user = user.childNodes[0].data
    passwd = smtpserver.getElementsByTagName("pass")[0]
    mail_pass = passwd.childNodes[0].data

    loghost = smtpserver.getElementsByTagName("loghost")[0]
    mail_loghost = loghost.childNodes[0].data
    logport = smtpserver.getElementsByTagName("logport")[0]
    mail_logport = logport.childNodes[0].data
    server = serverobj(mail_host,mail_port,mail_sslport,mail_user,mail_pass,mail_loghost,mail_logport)
    return server



#解析用户配置文件
def get_userlist_config():
    DOMTree_user= xml.dom.minidom.parse("./userlist.xml")
    userlist = DOMTree_user.documentElement
    users = userlist.getElementsByTagName("user")
    user_list = []

    for xml_user in users:

        username = xml_user.getElementsByTagName('name')[0]
        user_name = username.childNodes[0].data 

        email = xml_user.getElementsByTagName('email')[0]
        user_email = email.childNodes[0].data
        
        local = xml_user.getElementsByTagName('local')[0]
        user_local = local.childNodes[0].data
        
        times = xml_user.getElementsByTagName("time")
        user_time =[]
        for xml_time in times:
           user_time.append(xml_time.childNodes[0].data) 
        newuser = userobj(user_name,user_email,user_local,user_time)
        user_list.append(newuser)
    return user_list



#解析图片路径配置文件
def get_emoj_config():
    emoj_map= {}
    DOMTree_emoj = xml.dom.minidom.parse("./emoj.xml")
    emoj_list = DOMTree_emoj.documentElement 

    happy_node = emoj_list.getElementsByTagName('happy')[0]
    emoj_map['happy']=happy_node.childNodes[0].data

    sad_node = emoj_list.getElementsByTagName('sad')[0]
    emoj_map['sad']=sad_node.childNodes[0].data
    return emoj_map 



#服务器信息文件解析
server = get_smtpserver_config()
to_log("smtpserver info :")
to_log(server.hostname)
to_log(server.port)
to_log(server.sslport)
to_log(server.user)
to_log(server.passwd)
sender = server.user



#城市配置文件解析
local_url = get_localurl_map()
to_log("init userlist.xml config")



#用户配置文件解析
user_list = get_userlist_config()

for x in user_list:
    to_log(str(x.time))



#图片配置文件解析
emoj_map= get_emoj_config()
to_log("init emoj.xml config")



for x in emoj_map:
    to_log(emoj_map[x])
timer_list = []

for x_user in user_list:
    for x_timer in x_user.time:
        to_log(str(x_timer))
        to_log(str(get_timer_value(x_timer)))
        to_log(x_user.email)
        timer = threading.Timer(get_timer_value(x_timer),timer_func,[server,x_user,local_url])
        timer_list.append(timer)

for x in timer_list:
    x.start()

