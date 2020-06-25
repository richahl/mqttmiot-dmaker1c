import sys
import time
import socket
import json
from multiprocessing import Queue
import paho.mqtt.client as paho
import miio

# Constants
mqtt_username="YOUR USERNAME"
mqtt_password="YOUR PASSWORD"
mqtt_prefix="MQTTPREFIX"
mqtt_broker="MQTTBROKERIP"
miot_broker="MIOT-FAN-IP"
miot_port=54321
miot_len_max=1480
miot_did=u"MY DID";
miot_token="MY TOKEN";

q = Queue(maxsize=100)



#define callback
def on_message(client, userdata, message):
	global q

	print("received message =",str(message.payload.decode("utf-8"))," on: ",message.topic)
	item=message.topic[len(mqtt_prefix):]
	print("Item: "+item)
	command=str(message.payload.decode("utf-8"))
	if item == "power":
		if command.upper() == "ON":
			q.put([ "power","set_properties", [{"did":miot_did,"siid":2,"piid":1,"value": True}]])
		else:
			q.put([ "power","set_properties", [{"did": miot_did,"siid":2,"piid":1,"value": False}]])
		q.put([ "power","get_properties", [{"did":miot_did,"siid":2,"piid":1}]])

	if item == "fanspeed":
		if command.upper() == "LOW":
			q.put([ "fanspeed","set_properties", [{"did":miot_did,"siid":2,"piid":2,"value":1}]])
		if command.upper() == "MEDIUM":
			q.put([ "fanspeed","set_properties", [{"did":miot_did,"siid":2,"piid":2,"value":2}]])
		if command.upper() == "HIGH":
			q.put([ "fanspeed","set_properties", [{"did":miot_did,"siid":2,"piid":2,"value":3}]])
		q.put([ "fanspeed","get_properties", [{"did":miot_did,"siid":2,"piid":2}]])
		
	if item == "mode":
		if command.upper() == "AUTO":
			q.put([ "mode","set_properties", [{"did":miot_did,"siid":2,"piid":7,"value":0}]])
		if command.upper() == "SLEEP":
			q.put([ "mode","set_properties", [{"did":miot_did,"siid":2,"piid":7,"value":1}]])
		q.put([ "mode","get_properties", [{"did":miot_did,"siid":2,"piid":7}]])
		
	if item == "rotate":
		if command.upper() == "ON":
			q.put([ "rotate","set_properties", [{"did":miot_did,"siid":2,"piid":3,"value": True}]])
		else:
			q.put([ "rotate","set_properties", [{"did":miot_did,"siid":2,"piid":3,"value": False}]])
		q.put([ "rotate","get_properties", [{"did":miot_did,"siid":2,"piid":3}]])
		
	if item == "childlock":
		if command.upper() == "ON":
			q.put([ "childlock","set_properties", [{"did":miot_did,"siid":3,"piid":1,"value": True}]])
		else:
			q.put([ "childlock","set_properties", [{"did": miot_did,"siid":3,"piid":1,"value": False}]])
		q.put([ "childlock","get_properties", [{"did":miot_did,"siid":3,"piid":1}]])

	if item == "sound":
		if command.upper() == "ON":
			q.put([ "sound","set_properties", [{"did":miot_did,"siid":2,"piid":11,"value": True}]])
		else:
			q.put([ "sound","set_properties", [{"did":miot_did,"siid":2,"piid":11,"value": False}]])
		q.put([ "sound","get_properties", [{"did":miot_did,"siid":2,"piid":11}]])

	if item == "indicator":
		if command.upper() == "ON":
			q.put([ "indicator","set_properties", [{"did":miot_did,"siid":2,"piid":12,"value": True}]])
		else:
			q.put([ "indicator","set_properties", [{"did":miot_did,"siid":2,"piid":12,"value": False}]])
		q.put([ "indicator","get_properties", [{"did":miot_did,"siid":2,"piid":12}]])
		

client= paho.Client("mqttmiot-001") #create client object client1.on_publish = on_publish #assign function to callback client1.connect(broker,port) #establish connection client1.publish("house/bulb1","on")
client.username_pw_set(mqtt_username, mqtt_password)
######Bind function to callback
client.on_message=on_message
#####
print("connecting to broker ",mqtt_broker)
client.connect(mqtt_broker)#connect
client.loop_start() #start loop to process received messages
client.subscribe(mqtt_prefix+"power")#subscribe
client.subscribe(mqtt_prefix+"mode")#subscribe
client.subscribe(mqtt_prefix+"fanspeed")#subscribe
client.subscribe(mqtt_prefix+"rotate")#subscribe
client.subscribe(mqtt_prefix+"sound")#subscribe
client.subscribe(mqtt_prefix+"childlock")#subscribe
client.subscribe(mqtt_prefix+"indicator")#subscribe

count_idle_messages=0
count_interval_messages=0
interval_messages=10

ap=miio.Device(ip=miot_broker, token=miot_token)


while True:
	while not q.empty() and count_interval_messages==0:
		print("Something in the queue")
		# req : topic , miio_msg
		req=q.get();
		print("Sending: "+str(req[1])+ " - "+str(req[2]))
		try:
			ret=ap.raw_command(req[1], req[2]);
			ret=ret[0]
			if req[1]=="get_properties":
				val=ret["value"]
				if req[0]=="fanspeed":
					if val==1:
						val="LOW"
					if val==2:
						val="MEDIUM"
					if val==3:
						val="HIGH"
				if req[0]=="delay":
					val="{:d}".format(val);
				if req[0]=="mode":
					if val==0:
						val="AUTO"
					if val==1:
						val="SLEEP"
				if req[0]=="power" or req[0]=="childlock" or req[0]=="rotate" or req[0]=="sound" or req[0]=="indicator":
					if val==1 or val==True or val=="True" or val=="true" or val=="TRUE":
						val="ON"
					else:
						val="OFF"
				client.publish(mqtt_prefix+req[0]+"/state",val)
				print("Publishing: "+mqtt_prefix+req[0]+"/state",val)
			if req[1]=="set_properties":
				client.publish(mqtt_prefix+req[0]+"/result",ret["code"])
				print("Publishing: "+mqtt_prefix+req[0]+"/return",ret["code"])
			count_interval_messages=interval_messages
		except Exception as e:
			print("No valid reply! Bad request?")
#	print("Waiting...")
	time.sleep(0.100);
	count_idle_messages=count_idle_messages+1;
	if count_interval_messages>0:
		count_interval_messages=count_interval_messages-1
	if count_idle_messages>0:
			# Every minute + 19s
			if (count_idle_messages%790)==0:
				q.put([ "sound","get_properties", [{"did":miot_did,"siid":2,"piid":11}]])
			if (count_idle_messages%530)==0:
				q.put([ "mode","get_properties", [{"did":miot_did,"siid":2,"piid":7}]])
			if (count_idle_messages%850)==0:
				q.put([ "power","get_properties", [{"did":miot_did,"siid":2,"piid":1}]])
			if (count_idle_messages%630)==0:
				q.put([ "fanspeed","get_properties", [{"did":miot_did,"siid":2,"piid":2}]])
			if (count_idle_messages%960)==0:
				q.put([ "rotate","get_properties", [{"did":miot_did,"siid":2,"piid":3}]])
			# Every 5 minutes
			if (count_idle_messages%3000)==0:
				q.put([ "delay","get_properties", [{"did":miot_did,"siid":2,"piid":10}]])
			if (count_idle_messages%3100)==0:
				q.put([ "indicator","get_properties", [{"did":miot_did,"siid":2,"piid":12}]])
			if count_idle_messages>864000:
				count_idle_messages=0
		
		
client.disconnect() #disconnect
client.loop_stop() #stop loop

