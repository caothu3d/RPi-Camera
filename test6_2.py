# coding: utf-8

import cv2
import cv2.cv as cv
import PIL.Image as Image
import StringIO
import socket
import threading
import time
import serial

capture = cv2.VideoCapture(0)
capture.set(cv.CV_CAP_PROP_FRAME_WIDTH, 320)
capture.set(cv.CV_CAP_PROP_FRAME_HEIGHT, 240)

frame = 0
lastframe = 0
newimg = 0


ser = serial.Serial("/dev/ttyAMA0", 115200)
ser.bytesize = 8
ser.stopbits = 1


class Listener8080(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', 8080))
        self.sock.listen(0)

    def run(self):
        while True:
            client = self.sock.accept()
            sender = Sender8080(client[0])
            sender.setDaemon(True)
            sender.start()


class Sender8080(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client
        global frame
        frame += 1

    def run(self):
        global newimg
        while newimg == 0:
            time.sleep(0.001)
        newimg = 0
        self.client.sendall(jpeg)
        self.client.close()


class Listener8090(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', 8090))
        self.sock.listen(0)

    def run(self):
        while True:
            client = self.sock.accept()
            reader = Reader8090(client[0])
            reader.setDaemon(True)
            reader.start()
            sender = Sender8090(client[0])
            sender.setDaemon(True)
            sender.start()


class Reader8090(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client

    def run(self):
        while True:
            data = self.client.recv(1024)
            if data:
                ser.write(data)
                print data


class Sender8090(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client

    def run(self):
        while True:
            data = ser.read(1)
            if data != "":
                self.client.write(data)


listener = Listener8080()
listener.setDaemon(True)
listener.start()

listener2 = Listener8090()
listener2.setDaemon(True)
listener2.start()


def displayfps():
    while True:
        global frame, lastframe
        print "FPS:", frame - lastframe
        lastframe = frame
        time.sleep(1)

fpsthread = threading.Thread(target=displayfps)
fpsthread.setDaemon(True)
fpsthread.start()

while True:
    ret, img = capture.read()  # 从摄像头读取图片
    # cv2.imshow('Video', img)  # 显示图片
    key = cv2.waitKey(30) & 0xFF
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 将图片从BGR转为RGB
    image = Image.fromarray(img)  # 将图片转为Image对象
    buf = StringIO.StringIO()  # 生成StringIO对象
    image.save(buf, format="JPEG")  # 将图片以JPEG格式写入StringIO
    jpeg = buf.getvalue()  # 获取JPEG图片内容
    buf.close()  # 关闭StringIO
    newimg = 1
    if key == 27:  # ESC
        break
    elif key == 32:  # Space
        print 'File Size:', len(jpeg) / 1024, 'KB'
        f = open('a.jpg', 'w')
        f.write(jpeg)
        f.close()

capture.release()
