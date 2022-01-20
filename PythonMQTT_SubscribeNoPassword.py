import paho.mqtt.client as mqtt
mqtt_topic = "Nano/player/IMU"
mqtt_broker_ip = "140.113.213.21"
mqtt_topic_pulish = "Server/player/ANS"

client = mqtt.Client()
player_flag = [0, 0, 0]
player_list = ["player001", "player002", "player003"]

def on_connect(client, userdata, flags, rc):
    print("Connected!", str(rc))
    client.subscribe(mqtt_topic)
    
def on_message(client, userdata, msg):
    global flag
    get_message = str(msg.payload)
    get_message = get_message.split("'")[1]
    get_list = get_message.split(", ")
    # print("Topic: ", msg.topic + "\nMessage: " + get_message)
    try:
        if float(get_list[3]) > 1: # 這裡可以換成判斷玩家在動的標準
            who = player_list.index(get_list[0])
            if player_flag[who] == 0:
                client.publish(mqtt_topic_pulish,str(who+1))
                print(get_list[0] + " move !")
                player_flag[who] = 1
                print(player_flag)
    except:
        pass

client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_broker_ip, 1883)
client.loop_forever()
client.disconnect()
