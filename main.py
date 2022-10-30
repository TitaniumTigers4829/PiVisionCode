from cscore import CameraServer
import cv2
import numpy as np
from networktables import NetworkTablesInstance

DEBUG = True

ntinst = NetworkTablesInstance.getDefault()
ntinst.startClientTeam(4829)
ntinst.startDSClient()

inst = CameraServer.getInstance()
# inst.enableLogging()
camera = inst.startAutomaticCapture()
camera.setResolution(320, 240)
sink = inst.getVideo()
img = np.zeros(shape=(240, 320, 3), dtype=np.uint8)
blueLow = (95, 86, 6)  # blue
blueHigh = (126, 255, 255)
redLow = (160, 50, 50)
redHigh = (180, 255, 255)
blue = (255, 0, 0)  # B,G,R
red = (0, 0, 255)  # B,G,R

robotCommunication = ntinst.getTable("SmartDashboard")


def find_balls(img, cLow, cHigh):
    """
    Finds cargo in the image

    :param img: CV2 image to find cargo in
    :param cLow:
    :param cHigh:
    :return: a list [(centerX, centerY, diameter),...]
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, cLow, cHigh)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, hierarchy = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ball_list = []

    for contour in contours:
        arclen = cv2.arcLength(contour, True)
        area = cv2.contourArea(contour)
        circularity = 4 * np.pi * area / (arclen ** 2)
        if (circularity > 0.8) & (arclen > 100):
            rect = cv2.boundingRect(contour)
            x, y, w, h = rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            ball_list.append((x + w / 2, y + h / 2, h))
    return ball_list


dashboard = inst.putVideo("camera-vision", 320, 240)
while True:
    time, img = sink.grabFrame(img)
    if time == 0:  # There is an error
        print("error")
        dashboard.notifyError(sink.getError())
    else:
        blueBalls = find_balls(img, blueLow, blueHigh)
        redBalls = find_balls(img, redLow, redHigh)
        if DEBUG:
            print("Blue: " + str(blueBalls))
            print("Red: " + str(redBalls))
        for ball in blueBalls:
            center = [ball[0], ball[1]]
            img = cv2.circle(img, center, ball[2] / 2, blue, 2)  # img, center, radius, color, thickness
        for ball in redBalls:
            center = [ball[0], ball[1]]
            img = cv2.circle(img, center, ball[2] / 2, red, 2)  # img, center, radius, color, thickness
        dashboard.putFrame(img)
        robotCommunication.putNumberArray("Blue Cargo", blueBalls)
        robotCommunication.putNumberArray("Red Cargo", redBalls)
