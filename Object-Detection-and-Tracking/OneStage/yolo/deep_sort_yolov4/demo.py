#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import sys
#sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
import os
import datetime
from timeit import time
import warnings
import cv2
import numpy as np
import argparse
from PIL import Image
from yolo import YOLO

from deep_sort import preprocessing
from deep_sort import nn_matching
from deep_sort.detection import Detection
from deep_sort.tracker import Tracker
from tools import generate_detections as gdet
from deep_sort.detection import Detection as ddet
from collections import deque
from keras import backend
import tensorflow as tf
from tensorflow.compat.v1 import InteractiveSession

#module for serial listening
import threading
import time
import random
import serial

# module for mqtt
import paho.mqtt.client as mqtt
from math import sqrt

config = tf.ConfigProto()
config.gpu_options.allow_growth = True
session = InteractiveSession(config=config)

#serial listening settings
PORT = '/dev/ttyUSB0'
detect = 0

#mqtt setting
mqtt_topic = "Nano/player/IMU"
mqtt_broker_ip = "140.113.213.21"
mqtt_topic_pulish = "Server/player/ANS"

client = mqtt.Client()
player_flag = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
# player_camera_move =  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
# player_list = ["player001", "player002", "player003", "player001", "player002", "player003","player001", "player002", "player003","player001", "player002", "player003","player001", "player002", "player003" ]

#player_flag = [0, 0, 0]
player_camera_move =  [0, 0, 0]
player_list = ["player001", "player002", "player003"]


ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input",help="path to input video", default = "./test_video/TownCentreXVID.avi")
ap.add_argument("-c", "--class",help="name of class", default = "person")
args = vars(ap.parse_args())

pts = [deque(maxlen=30) for _ in range(9999)]
warnings.filterwarnings('ignore')

# initialize a list of colors to represent each possible class label
np.random.seed(100)
COLORS = np.random.randint(0, 255, size=(200, 3),
	dtype="uint8")
#list = [[] for _ in range(100)]

def get_iou(bbox_ai, bbox_gt):
    iou_x = max(bbox_ai[0], bbox_gt[0]) # x
    iou_y = max(bbox_ai[1], bbox_gt[1]) # y
    iou_w = min(bbox_ai[2]+bbox_ai[0], bbox_gt[2]+bbox_gt[0]) - iou_x # w
    iou_w = max(iou_w, 0)
    iou_h = min(bbox_ai[3]+bbox_ai[1], bbox_gt[3]+bbox_gt[1]) - iou_y # h
    iou_h = max(iou_h, 0)

    iou_area = iou_w * iou_h
    all_area = bbox_ai[2]*bbox_ai[3] + bbox_gt[2]*bbox_gt[3] - iou_area

    return max(iou_area/all_area, 0)

def listen(PORT):
    global detect
    print('Thread start listening')
    print('Initial serial port......')    
    COM_PORT = PORT    # ?????????????????????
    BAUD_RATES = 9600    # ??????????????????
    ser = serial.Serial(COM_PORT, BAUD_RATES)   # ?????????????????????
    time.sleep(2)
    ser.write(b'reset\n')
    print('Done')
    time.sleep(1)

    #??????????????????
    for i in range (3,-1,-1):
        time.sleep(1)
        print(i)  

    print('Thread : first back to player')
    ser.write(b'start\n')

    try:
        while True:
            data = ''
            while ser.in_waiting:          # ????????????????????????
                data_raw = ser.readline()  # ????????????
                data = data_raw.decode().strip()   # ????????????UTF-8?????? ??????????????????
                #print('???????????????????????????', data_raw)
                #print('??????????????????:', data)
                
                if data == 'Arduino : start turn back':
                    detect = 0
                    print('Thread : back to player')
                if data == 'Arduino : finish turn front':
                    detect = 1
                    print('Thread : face to player')
       
    except KeyboardInterrupt:
        ser.close()    # ????????????????????????
        print('Exit!')

def readSensor():
    global detect,client
    def on_connect(client, userdata, flags, rc):
        print("Connected!", str(rc))
        client.subscribe(mqtt_topic)
    
    def on_message(client, userdata, msg):
        global flag
        get_message = str(msg.payload)
        get_message = get_message.split("'")[1]
        get_list = get_message.split(", ")
        #print("Topic: ", msg.topic + "\nMessage: " + get_message)
        #print(get_list)
        total = sqrt(float(get_list[1])**2 + float(get_list[2])**2 + float(get_list[3])**2)
        try:
            if total > 1.1: # ?????????????????????????????????????????????
                who = player_list.index(get_list[0])
                if player_flag[who] == 0 and detect == 1:
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

def main(yolo):
    global player_flag

    start = time.time()
    max_cosine_distance = 0.3
    nn_budget = None
    nms_max_overlap = 1.0

    counter = []
    #deep_sort
    model_filename = 'model_data/market1501.pb'
    encoder = gdet.create_box_encoder(model_filename,batch_size=1)

    find_objects = ['person']
    metric = nn_matching.NearestNeighborDistanceMetric("cosine", max_cosine_distance, nn_budget)
    tracker = Tracker(metric)

    frame_index = -1
    video_capture = cv2.VideoCapture(0)

    ###########
    # initialize frame for movement detector
    ret, frame = video_capture.read()
    avg = cv2.blur(frame, (4, 4))
    avg_float = np.float32(avg)
    ###########

    ###########
    # create thread to read serial input from arduino
    t = threading.Thread(target = listen, args=(PORT,))
    t.setDaemon(True)
    t.start()
    global detect

    #create thread to read sensor data
    t2 = threading.Thread(target = readSensor)
    t2.setDaemon(True)
    t2.start()
    global client
    ###########


    fps = 0.0

    while True:

        ret, frame = video_capture.read()  # frame shape 640*480*3
        if ret != True:
            break
        t1 = time.time()

        ######################
        # movement detector
        # ????????????
        blur = cv2.blur(frame, (4, 4))
        # ?????????????????????????????????????????????
        diff = cv2.absdiff(avg, blur)
        # ?????????????????????
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        # ?????????????????????????????????????????????
        ret, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
        # ????????????????????????????????????
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        # ???????????????
        contours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        moving_boxes = []
        for c in contours:
            # ?????????????????????
            if cv2.contourArea(c) < 1000:
                continue
            # ???????????????????????????????????????????????????????????????...

            # ??????????????????????????????
            (x, y, w, h) = cv2.boundingRect(c)
            moving_boxes.append((x,y,w,h))
            # ????????????
            #cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # ??????????????????????????????
            cv2.drawContours(frame, contours, -1, (0, 255, 255), 2)
        ######################
        

        #image = Image.fromarray(frame)
        image = Image.fromarray(frame[...,::-1]) #bgr to rgb
        boxs, confidence, class_names = yolo.detect_image(image)
        features = encoder(frame,boxs)
        # score to 1.0 here).
        detections = [Detection(bbox, 1.0, feature) for bbox, feature in zip(boxs, features)]
        # Run non-maxima suppression.
        boxes = np.array([d.tlwh for d in detections])
        scores = np.array([d.confidence for d in detections])
        indices = preprocessing.non_max_suppression(boxes, nms_max_overlap, scores)
        detections = [detections[i] for i in indices]

        # Call the tracker
        tracker.predict()
        tracker.update(detections)

        i = int(0)
        indexIDs = []
        c = []
        boxes = []

        #yolo bounding box
        for det in detections:
            bbox = det.to_tlbr()
            cv2.rectangle(frame,(int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])),(255,255,255), 2)
            #print(class_names)
            #print(class_names[p])

        #deep sort bounding box
        #sort bounding box's order by the x coordinate in each box
        sort_tracks = sorted(tracker.tracks, key = lambda x: x.to_tlbr()[0])
        moving_record = []
        for track in sort_tracks:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue
            #boxes.append([track[0], track[1], track[2], track[3]])
            indexIDs.append(int(track.track_id))
            counter.append(int(track.track_id))
            bbox = track.to_tlbr()
            color = [int(c) for c in COLORS[indexIDs[i] % len(COLORS)]]
            #print(frame_index)
            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])),(color), 3)
            b0 = bbox[0]#.split('.')[0] + '.' + str(bbox[0]).split('.')[0][:1]
            b1 = bbox[1]#.split('.')[0] + '.' + str(bbox[1]).split('.')[0][:1]
            b2 = bbox[2]-bbox[0]#.split('.')[0] + '.' + str(bbox[3]).split('.')[0][:1]
            b3 = bbox[3]-bbox[1]

            #calculate each person's moving ratio 
            iou_sum = 0
            for j in moving_boxes:
                iou = get_iou(j,(b0,b1,b2,b3))
                iou_sum += iou
            moving_record.append((track.track_id,iou_sum))

            cv2.putText(frame,str(track.track_id),(int(bbox[0]), int(bbox[1] -50)),0, 5e-3 * 150, (color),2)
            if len(class_names) > 0:
               class_name = class_names[0]
               cv2.putText(frame, str(class_names[0]),(int(bbox[0]), int(bbox[1] -20)),0, 5e-3 * 150, (color),2)

            i += 1
            #bbox_center_point(x,y)
            center = (int(((bbox[0])+(bbox[2]))/2),int(((bbox[1])+(bbox[3]))/2))
            #track_id[center]

            pts[track.track_id].append(center)

            thickness = 5
            #center point
            cv2.circle(frame,  (center), 1, color, thickness)

			# draw motion path
            for j in range(1, len(pts[track.track_id])):
                if pts[track.track_id][j - 1] is None or pts[track.track_id][j] is None:
                   continue
                thickness = int(np.sqrt(64 / float(j + 1)) * 2)
                cv2.line(frame,(pts[track.track_id][j-1]), (pts[track.track_id][j]),(color),thickness)
                #cv2.putText(frame, str(class_names[j]),(int(bbox[0]), int(bbox[1] -20)),0, 5e-3 * 150, (255,255,255),2)

        if detect == 1:
            index = 0
            for person,move in moving_record:
                if move > 0.5 and player_flag[index] == 0:
                    print(f'player{index+1} camera move')
                    player_flag[index] = 1
                    client.publish(mqtt_topic_pulish,str(index+1))
                index += 1

        count = len(set(counter))
        cv2.putText(frame, "Total Pedestrian Counter: "+str(count),(int(20), int(120)),0, 5e-3 * 200, (0,255,0),2)
        cv2.putText(frame, "Current Pedestrian Counter: "+str(i),(int(20), int(80)),0, 5e-3 * 200, (0,255,0),2)
        cv2.putText(frame, "FPS: %f"%(fps),(int(20), int(40)),0, 5e-3 * 200, (0,255,0),3)
        cv2.namedWindow("YOLO4_Deep_SORT", 0)
        cv2.resizeWindow('YOLO4_Deep_SORT', 1024, 768)
        cv2.imshow('YOLO4_Deep_SORT', frame)


        fps  = ( fps + (1./(time.time()-t1)) ) / 2
        frame_index = frame_index + 1

        # Press Q to stop!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        ##############
        #update frame for movement detector, the last argument is updating rate
        cv2.accumulateWeighted(blur, avg_float, 0.2)
        avg = cv2.convertScaleAbs(avg_float)
        #####################


    print(" ")
    print("[Finish]")
    end = time.time()

    if len(pts[track.track_id]) != None:
       print(args["input"][43:57]+": "+ str(count) + " " + str(class_name) +' Found')

    else:
       print("[No Found]")
	#print("[INFO]: model_image_size = (960, 960)")
    video_capture.release()

    cv2.destroyAllWindows()

if __name__ == '__main__':
    main(YOLO())
