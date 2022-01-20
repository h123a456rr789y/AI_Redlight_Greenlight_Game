#include <PubSubClient.h> // Allows us to connect to, and publish to the MQTT broker
#include <Arduino_LSM6DS3.h>
#include <WiFiNINA.h>

#include "pitches.h"
int pitches_pin = 7;

int melody[] = {
NOTE_D4, NOTE_D4, NOTE_D4, NOTE_D4, NOTE_D4, NOTE_D4, NOTE_D4, NOTE_D4,  
NOTE_A3, NOTE_C4, NOTE_D4, NOTE_D4, NOTE_D4, NOTE_E4, NOTE_F4, NOTE_F4, 
NOTE_F4, NOTE_G4, NOTE_E4, NOTE_E4, NOTE_D4, NOTE_C4, NOTE_C4, NOTE_D4,
0, NOTE_A3, NOTE_C4, NOTE_B3, NOTE_D4, NOTE_B3, NOTE_E4, NOTE_F4,
NOTE_F4, NOTE_C4, NOTE_C4, NOTE_C4, NOTE_C4, NOTE_D4, NOTE_C4,
NOTE_D4, 0, 0, NOTE_A3, NOTE_C4, NOTE_D4, NOTE_D4, NOTE_D4, NOTE_F4,
NOTE_G4, NOTE_G4, NOTE_G4, NOTE_A4, NOTE_A4, NOTE_A4, NOTE_A4, NOTE_G4,
NOTE_A4, NOTE_D4, 0, NOTE_D4, NOTE_E3, NOTE_F4, NOTE_F4, NOTE_G4, NOTE_A4, 
NOTE_D4, 0, NOTE_D4, NOTE_F4, NOTE_E4, NOTE_E4, NOTE_F4, NOTE_D4
};
int noteDurations[] = {
8,8,4,8,4,8,
4,8,8,8,8,4,4,8,8,4,4,8,8,4,4,8,8,
8,4,8,8,8,4,4,8,8,4,4,8,8,4,4,8,4,
4,8,8,8,8,4,4,8,8,4,4,8,8,4,4,8,8,
8,4,8,8,8,4,4,4,8,4,8,8,8,4,4,8,8
};

// WIFI
const char* ssid = "hscc-demo";
const char* wifi_password = "tRUfEC3o";

// MQTT
const char* mqtt_server = "140.113.213.21";
const char* mqtt_topic = "Nano/player/IMU";
const char* mqtt_topic_subscribe = "Server/player/ANS";
const char* clientID = "player001";
const char client_num = '1';

// payload
String Nano_info, sending_data;
int count = 0;

WiFiClient wifiClient;
PubSubClient client(mqtt_server, 1883, wifiClient);

void ReceivedMessage(char* topic, byte* payload, unsigned int length) {
  Serial.println((char)payload[0]);
  count++;
  Serial.println(count);
  if((char)payload[0] == client_num)
  {
    Serial.println("Turn");
    play_music();
    Serial.println("Over");
  }
}

void setup() {
  
  pinMode(pitches_pin, OUTPUT);
  Serial.begin(115200);
  Serial.print("Connecting to ");
  Serial.println(ssid);

  // Connect to the WiFi
  WiFi.begin(ssid, wifi_password);

  // Wait until the connection has been confirmed before continuing
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  // Debugging - Output the IP Address of the Nano
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Connect to MQTT Broker
  // client.connect returns a boolean value to let us know if the connection was successful.
  if (client.connect(clientID)) {
    Serial.println("Connected to MQTT Broker!");
  }
  else {
    Serial.println("Connection to MQTT Broker failed...");
  }

  if(!IMU.begin())
  {
    Serial.println("Failed to initialize IMU ! ");
    while(true);// halt program
  }
  Serial.println("IMU initialized");

  sending_data = String();
  Nano_info = String();

  client.subscribe(mqtt_topic_subscribe);
  client.setCallback(ReceivedMessage);
}

void loop()
{
  float aX, aY, aZ;
  float gX, gY, gZ;
  const char * spacer = ", ";
  if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable())
  {      
    IMU.readAcceleration(aX, aY, aZ);
    IMU.readGyroscope(gX, gY, gZ);
    Serial.print(aX); Serial.print(spacer);
    Serial.print(aY); Serial.print(spacer);
    Serial.print(aZ); Serial.print(spacer);
    Serial.print(gX); Serial.print(spacer);
    Serial.print(gY); Serial.print(spacer);
    Serial.println(gZ);
  }

  sending_data = String();
  Nano_info = String(clientID);
  sending_data = Nano_info + spacer + aX + spacer + aY + spacer + aZ + spacer + gX + spacer + gY + spacer + gZ;
  char sending_char[50];
  sending_data.toCharArray(sending_char, 50);
  
  if (client.publish(mqtt_topic, sending_char))
  {
    Serial.println("message sent!");
    delay(30);
  }
  else
  {
    Serial.println("Message failed to send. Reconnecting to MQTT Broker and trying again");
    client.connect(clientID);
    delay(10);
    client.publish(mqtt_topic, sending_char);
  }
  
  client.loop();
}

void play_music()
{
  for (int thisNote = 0; thisNote < 5; thisNote++)
  {
    int noteDuration = 1000 / noteDurations[thisNote];
    tone(pitches_pin, melody[thisNote], noteDuration);
    int pauseBetweenNotes = noteDuration * 1.30;
    delay(pauseBetweenNotes);
    noTone(pitches_pin);
  }
}
    
  
