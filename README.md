# AI_Redlight_Greenlight_Game



## Motivation
Inspired from the fist game of squid game, Redlight Greenlight Game, we design a game in real world to simulate the view of the doll and using vision and IMU sensors to detect if the player are moving or not.

Therefore, we design a system intergrating both the vision and sensor data with Arduino and PC to detect the human movement.
We can provided around 3 palyers palying in our game due to the vision limitation.

## Hardware
- Arduino 33 IOT * 2
- Web Camera
- Speaker
- Servomotor
- DFplayer (Mini MP3)

![](https://i.imgur.com/HyoY9Pe.jpg)

# Software architechture
![](https://i.imgur.com/rPAYBr7.png)
![](https://i.imgur.com/Mhu13Dz.png)

We applied MQTT and wifi-module for the wireless data transfer.
Besides, we use Yolov4 for human bounding box detection and tracking and using the moving average(OpenCV) algorithm to calculate the IoU for human movement detection.


## Futrue work
- Improve the vision-based algorithm to increase and stablize the FPS
- Add human tracking for more complex scences e.g., occlusion, interaction
- Add more sensors to detect movement more accurately, but suffer from synchronization problem
- Use laser sensor and positioning IR camera sensor to add some atmosphere to the game
