import threading
import time
import random
import serial  # 引用pySerial模組

#settings
PORT = 'COM3'
detect = 0

def listen(PORT):
    global detect
    print('Thread start listening')
    print('Initial serial port......')    
    COM_PORT = PORT    # 指定通訊埠名稱
    BAUD_RATES = 9600    # 設定傳輸速率
    ser = serial.Serial(COM_PORT, BAUD_RATES)   # 初始化序列通訊
    time.sleep(2)
    ser.write(b'reset\n')
    print('Done')
    time.sleep(1)

    #倒數準備開始
    for i in range (5,-1,-1):
        time.sleep(1)
        print(i)  

    print('Thread : first back to player')
    ser.write(b'turn back\n')

    try:
        while True:
            data = ''
            while ser.in_waiting:          # 若收到序列資料…
                data_raw = ser.readline()  # 讀取一行
                data = data_raw.decode().strip()   # 用預設的UTF-8解碼 去除句尾換行
                #print('接收到的原始資料：', data_raw)
                print('接收到的資料：', data)
                
                if data == 'Arduino : finish turn back':
                    #time.sleep(random.randint(1,3)) #隨機1~3秒轉回面向玩家
                    print('Thread : face to player')
                    #ser.write(b'turn front\n')

                if data == 'Arduino : finish turn front':
                    detect = 1
                    #time.sleep(random.randint(1,5))
                    time.sleep(3) #等三秒恢復背對玩家
                    detect = 0
                    print('Thread : back to player')
                    ser.write(b'turn back\n')        
    except KeyboardInterrupt:
        ser.close()    # 清除序列通訊物件
        print('Exit！')

def main():    
    t = threading.Thread(target = listen, args=(PORT,))
    t.setDaemon(True)
    t.start()

    global detect

    while True:
        # Object Detection     
        if detect:
            print('main : start detecting')
            time.sleep(0.5)

if __name__ == '__main__':
    main()