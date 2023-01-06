from cscore import CameraServer
import cv2
import numpy as np
from networktables import NetworkTablesInstance
from time import sleep

DEBUG = True

ntinst = NetworkTablesInstance.getDefault()
ntinst.startClientTeam(4829)
ntinst.startDSClient()

inst = CameraServer.getInstance()
# inst.enableLogging()
camera = inst.startAutomaticCapture()
camera.setResolution(1920, 1080)
sink = inst.getVideo()
img = np.zeros(shape=(1920, 1080, 3), dtype=np.uint8)
blueLow = (95, 86, 6)
blueHigh = (126, 255, 255)
redLow = (130, 20, 20)  # bgr? 160/50/50
redHigh = (200, 255, 255) # 180/255/255
blue = (255, 0, 0)  # B,G,R
red = (0, 0, 255)  # B,G,R

# 27 inches
cam_height = 0.69  # nice
cam_angle = 30  # from horizontal

robotCommunication = ntinst.getTable("SmartDashboard")


def find_balls(img, cLow, cHigh):

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
            ball_list.append([(x + w / 2)-860, h])
    return ball_list

def get_big(balls):
    if len(balls)>0:
        maxi=0
        maxh=0
        for i in range(len(balls)):
            b=balls[i]
            if b[1]>maxh:
                maxh=b[1]
                maxi=i
        return balls[maxi]
    else:
        return [-1.0, -1.0]

def find_position(ball):
    # java distance formula:     return ((ShooterConstants.targetHeight - ShooterConstants.cameraHeight) / Math.tan((
    # ShooterConstants.cameraAngle + getTargetOffsetY()) * (Math.PI / 180)));
    # ballheight - cameraheight
    # -------------------------
    # tan(radians(camAngle + ball))
    # 
    # ball = [centerx, centery, h]
    offset = ball[0]
    height = ball[1]

#dashboard = inst.putVideo("camera-vision", 1920, 1080)
while True:
    time, img = sink.grabFrame(img)
    if time == 0:  # There is an error
        print("error")
        dashboard.notifyError(sink.getError())
    else:
        blueBalls = find_balls(img, blueLow, blueHigh)
        redBalls = find_balls(img, redLow, redHigh)

        bigblue = get_big(blueBalls)
        bigred = get_big(redBalls)

        if DEBUG:
            print("Blue: " + str(blueBalls))
            print("Red: " + str(redBalls))
        """for ball in blueBalls:
            center = [ball[0], ball[1]]
            img = cv2.circle(img, center, int(ball[2] / 2), blue, 2)  # img, center, radius, color, thickness"""
        # for ball in redBalls:
        #     center = [ball[0], ball[1]]
        #     img = cv2.circle(img, center, int(ball[2] / 2), red, 2)  # img, center, radius, color, thickness
#        dashboard.putFrame(img)
        robotCommunication.putNumber("Cargo offset", bigblue[0])
        robotCommunication.putNumber("Cargo height", bigblue[1])
        robotCommunication.putNumber("Cargo offset red", bigred[0])
        robotCommunication.putNumber("Cargo height red", bigred[1])

        # dunno why thids fixes it lol
        # without this it freezes
        print("blue offset: " + str(robotCommunication.getNumber("Cargo offset", -1)))
        print("blue height: " + str(robotCommunication.getNumber("Cargo height", -1)))
        print("red offset: " + str(robotCommunication.getNumber("Cargo offset red", -1)))
        print("red height: " + str(robotCommunication.getNumber("Cargo height red", -1)))
        
