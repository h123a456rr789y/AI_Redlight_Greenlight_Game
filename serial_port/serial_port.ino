#include <Servo.h>
#include <SoftwareSerial.h>
#include <DFMiniMp3.h>

class Mp3Notify
{
public:
  static void PrintlnSourceAction(DfMp3_PlaySources source, const char* action)
  {
    if (source & DfMp3_PlaySources_Sd) 
    {
        Serial.print("SD Card, ");
    }
    if (source & DfMp3_PlaySources_Usb) 
    {
        Serial.print("USB Disk, ");
    }
    if (source & DfMp3_PlaySources_Flash) 
    {
        Serial.print("Flash, ");
    }
    Serial.println(action);
  }
  static void OnError(uint16_t errorCode)
  {
    // see DfMp3_Error for code meaning
    Serial.println();
    Serial.print("Com Error ");
    Serial.println(errorCode);
  }
  static void OnPlayFinished(DfMp3_PlaySources source, uint16_t track)
  {
    Serial.print("Play finished for #");
    Serial.println(track);  
  }
  static void OnPlaySourceOnline(DfMp3_PlaySources source)
  {
    PrintlnSourceAction(source, "online");
  }
  static void OnPlaySourceInserted(DfMp3_PlaySources source)
  {
    PrintlnSourceAction(source, "inserted");
  }
  static void OnPlaySourceRemoved(DfMp3_PlaySources source)
  {
    PrintlnSourceAction(source, "removed");
  }
};

SoftwareSerial secondarySerial(10, 11); // RX, TX
DFMiniMp3<SoftwareSerial, Mp3Notify> mp3(secondarySerial);
Servo myservo;
int pos = 180; //180:面對玩家, 0:背對玩家
String str;
int rotate_speed;
int flag = 0;
 
void setup() {
  Serial.begin(9600);
  myservo.attach(9);
  randomSeed(analogRead(0));

  mp3.begin();
  mp3.setVolume(30);
  
}
 
void loop() {
  //rotate_speed = random(5, 15);
  rotate_speed = 15;
  
  str = Serial.readStringUntil('\n');
  if(str == "start") flag = 1;
  if(flag){
    Serial.write("Arduino : start turn back\n");    
    for(pos = 180; pos >=0; pos-=rotate_speed){    
      myservo.write(pos);
      delay(10);   
    }   
    
    int track_num = random(1,4);      
    mp3.playMp3FolderTrack(track_num);
    if(track_num == 1)
      delay(5500);
    else if(track_num == 2)
      delay(2700);
    else if(track_num == 3)
      delay(1500); 

    for(pos = 0; pos <=180; pos+=rotate_speed){
      myservo.write(pos);
      delay(10);
    }
    Serial.write("Arduino : finish turn front\n");
    delay(5000);   
  }  
  else if(str == "reset"){
    flag = 0;
    myservo.write(180);
  }  
}
