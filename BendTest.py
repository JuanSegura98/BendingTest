import cv2
import numpy as np
import math
import datetime
import sys

CAMERA = 0 # 1 If there is a webcam, 0 if there is not
if len( sys.argv ) > 1:
    CAMERA = sys.argv[1]



font = cv2.FONT_HERSHEY_COMPLEX
from Calibration import calibrate

GREEN_CAB_FILE = 'calibration/green.txt'
YELLOW_CAB_FILE = 'calibration/yellow.txt'


first_point = []
end_point = []

def getDistancePX(first_point, end_point):
    return math.sqrt((first_point[0]-end_point[0])*(first_point[0]-end_point[0]) + (first_point[1]-end_point[1])*(first_point[1]-end_point[1]))


class Target():
    init_pos = []
    last_pos = []
    fix_pos = []

    def __init__(self, init_pos):
        self.init_pos = init_pos
        self.last_pos = init_pos

    def distanceIncrement(self, new_pos):
        return getDistancePX(self.last_pos, new_pos)

    def setPos(self, position):
        self.last_pos = position

    def getPos(self):
        return self.last_pos

    def getInitialPos(self):
        return self.init_pos

    def fixPos(self, position):
        self.fix_pos = position

    def getFixPos(self):
        return self.fix_pos

    def getDisplacement(self):
        if(len(self.init_pos) == 0 or len(self.last_pos) == 0):
            return 0
        if(len(self.fix_pos) > 0):
            print(self.fix_pos)
            return getDistancePX(self.init_pos, self.fix_pos)
        else:
            return getDistancePX(self.init_pos, self.last_pos)


def loadHSV(file):
    try:
        with open(file, "r") as f:
            lines = f.read().split('\n')
            for line in lines:
                if("L_H" in line):
                    l_h = int(line.split(' ')[1])
                if("L_S" in line):
                    l_s = int(line.split(' ')[1])
                if("L_V" in line):
                    l_v = int(line.split(' ')[1])
                if("W_H" in line):
                    w_h = int(line.split(' ')[1])
                if("W_S" in line):
                    w_s = int(line.split(' ')[1])
                if("W_V" in line):
                    w_v = int(line.split(' ')[1])

    except:
        l_h, l_s, l_v, w_h, w_s, w_v = calibrate(file_name = file)

    return [l_h, l_s, l_v, w_h, w_s, w_v]



# Color ranges
green_hsv = loadHSV(GREEN_CAB_FILE)
lower_green = np.array(green_hsv[0:3])
upper_green = np.array(green_hsv[3:6])

yellow_hsv = loadHSV(YELLOW_CAB_FILE)
lower_yellow = np.array(yellow_hsv[0:3])
upper_yellow = np.array(yellow_hsv[3:6])



cap = cv2.VideoCapture(CAMERA) # For the integrated webcam
cap.set(3, 4416)
cap.set(4, 1242)

control_targets = []
measure_targets = []
PIXEL_THRESHOLD = 30

while (1):
    _, frame = cap.read()
    ## This code is because originally, a stereoscopic camera was used and only half of the image was needed
    # height, width = frame.shape[:2]
    # start_row, start_col = int(0), int(0)
    # end_row, end_col = int(height), int(width*0.5)
    # frame = frame[start_row:end_row , start_col:end_col]    # Get the left half of the image (Stereo Camera)
    ##

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)        # We cast to HSV: Hue, Saturation, Value. It is better since "color" (hue) is continuous, unlike in RGB.

    green_mask = cv2.inRange(hsv, lower_green, upper_green)       # We create a mask with the color range we defined
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)


    # green_contours detection
    if int(cv2.__version__[0]) > 3:
        # Opencv 4.x.x
        green_contours, _ = cv2.findContours(green_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        yellow_contours, _ = cv2.findContours(yellow_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    else:
        # Opencv 3.x.x
        _, green_contours, _ = cv2.findContours(green_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        _, yellow_contours = cv2.findContours(yellow_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    
    for cnt in green_contours:
        area = cv2.contourArea(cnt)
        if(area > 1000):
            cv2.drawContours(frame, cnt, -1, (100,0,0), 3)
            M = cv2.moments(cnt)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            if(len(control_targets) == 0):
                control_targets.append(Target([cX,cY]))
            else:
                target_registered = False
                for target in control_targets:
                    if(getDistancePX(target.getPos(), [cX, cY]) < PIXEL_THRESHOLD):
                        target_registered = True
                        target.setPos([cX, cY]) # Update position
                if(not target_registered):
                    control_targets.append(Target([cX,cY]))

    for cnt in yellow_contours:
        area = cv2.contourArea(cnt)
        if(area > 1000):
            cv2.drawContours(frame, cnt, -1, (0, 69, 255), 3)
            M = cv2.moments(cnt)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            if(len(measure_targets) == 0):
                measure_targets.append(Target([cX,cY]))
            else:
                target_registered = False
                for target in measure_targets:
                    if(getDistancePX(target.getPos(), [cX, cY]) < PIXEL_THRESHOLD):
                        target_registered = True
                        target.setPos([cX, cY]) #Update position
                if(not target_registered):
                    measure_targets.append(Target([cX,cY]))

    px2mm = 0
    if(len(control_targets) == 2):
        cv2.line(frame, (control_targets[0].getPos()[0], control_targets[0].getPos()[1]), (control_targets[1].getPos()[0], control_targets[1].getPos()[1]), (100, 0, 0), 5 )
        cv2.putText(frame,'50mm',(int((control_targets[0].getPos()[0] + control_targets[1].getPos()[0])/2) + 10 ,int((control_targets[0].getPos()[1] + control_targets[1].getPos()[1])/2)), cv2.FONT_HERSHEY_SIMPLEX, 1,(100,0,0),2)
        px2mm = 50/getDistancePX(control_targets[0].getPos(), control_targets[1].getPos())

    for target in control_targets:
        cv2.circle(frame, (target.getInitialPos()[0], target.getInitialPos()[1]), 5, (100, 0, 0), -1 )
        cv2.line(frame, (target.getInitialPos()[0], target.getInitialPos()[1]), (target.getPos()[0], target.getPos()[1]), (100, 0, 0), 5)
        display_text = str(round(target.getDisplacement()*px2mm, 3)) + "mm"
        cv2.putText(frame,display_text,(int((target.getInitialPos()[0] + target.getPos()[0])/2) + 10 ,int((target.getInitialPos()[1] + target.getPos()[1])/2)), cv2.FONT_HERSHEY_SIMPLEX, 1,(100,0,0),2)
        cv2.circle(frame, (target.getPos()[0], target.getPos()[1]), 5, (100, 0, 0), -1)

    for target in measure_targets:
        cv2.circle(frame, (target.getInitialPos()[0], target.getInitialPos()[1]), 5, (0, 69, 255), -1 )
        cv2.line(frame, (target.getInitialPos()[0], target.getInitialPos()[1]), (target.getPos()[0], target.getPos()[1]), (0, 69, 255), 5)
        display_text = str(round(target.getDisplacement()*px2mm, 3)) + "mm"
        cv2.putText(frame,display_text,(int((target.getInitialPos()[0] + target.getPos()[0])/2) + 10 ,int((target.getInitialPos()[1] + target.getPos()[1])/2)), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,69,255),2)
        cv2.circle(frame, (target.getPos()[0], target.getPos()[1]), 5, (0, 69, 255), -1)

    cv2.imshow('frame', frame)

    # Terminal output
    print('\033[2J')    # Clear screen
    print("Instructions:")
    print("\tPress C to calibrate the camera")
    print("\tPress R to reset the points")
    print("\tPress ESPACE to save measurements to a file")
    print("\tPress ESC to exit\n")
    print("Resolution: {} mm/px".format(round(px2mm, 3)))

    # Key handling
    k = cv2.waitKey(1) & 0xFF

    if k == 27: # If ESC is pressed, exit
        break
    if k == ord(' '):   # If SPACE is pressed, mark points
        with open("measurements.txt", 'a') as m:
            m.write("## Date: " + str(datetime.datetime.now()) + ", Resolution: " + str(round(px2mm, 3)) + "mm/px" + "##" + '\n')
            measure_targets.sort(key=lambda x: x.getInitialPos()[0])    # Sort targets by initial x position
            for target in measure_targets:
                m.write(str(measure_targets.index(target)) + ": " + str(target.getDisplacement()*px2mm) +"mm;\n")
            m.write("##########\n")

    if k == ord('r'):   # If r is pressed, erase points
        control_targets = []
        measure_targets = []

    if k == ord('c'):   # If c is pressed, re-calibrate
        cv2.destroyAllWindows()
        cap.release()
        green_hsv = calibrate(GREEN_CAB_FILE, green_hsv[0], green_hsv[1], green_hsv[2], green_hsv[3], green_hsv[4], green_hsv[5])
        lower_green = np.array(green_hsv[0:3])
        upper_green = np.array(green_hsv[3:6])

        yellow_hsv = calibrate(YELLOW_CAB_FILE, yellow_hsv[0], yellow_hsv[1], yellow_hsv[2], yellow_hsv[3], yellow_hsv[4], yellow_hsv[5])
        lower_yellow = np.array(yellow_hsv[0:3])
        upper_yellow = np.array(yellow_hsv[3:6])
        cap = cv2.VideoCapture(CAMERA) # For the integrated webcam
        cap.set(3, 4416)
        cap.set(4, 1242)


cv2.destroyAllWindows()
cap.release()