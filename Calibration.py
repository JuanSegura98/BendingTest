import cv2
import numpy as np
import sys
font = cv2.FONT_HERSHEY_COMPLEX

CAMERA = 0 # 1 If there is a webcam, 0 if there is not
if len( sys.argv ) > 1:
    CAMERA = sys.argv[1]

def nothing(self):
    pass

def calibrate(file_name = 'calibration.txt', l_h = 0, l_s = 0, l_v = 0, w_h = 180, w_s = 255, w_v = 255):
	cap = cv2.VideoCapture(CAMERA)   # For the main camera
	cap.set(3, 4416)
	cap.set(4, 1242)

	cv2.namedWindow("Trackbars")
	cv2.createTrackbar("L-H", "Trackbars", l_h, 180, nothing)
	cv2.createTrackbar("L-S", "Trackbars", l_s, 255, nothing)
	cv2.createTrackbar("L-V", "Trackbars", l_v, 250, nothing)
	cv2.createTrackbar("W-H", "Trackbars", w_h, 180, nothing)
	cv2.createTrackbar("W-S", "Trackbars", w_s, 255, nothing)
	cv2.createTrackbar("W-V", "Trackbars", w_v, 255, nothing)

	while (1):
	    _, frame = cap.read()
	    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)        # We cast to HSV: Hue, Saturation, Value. It is better since "color" (hue) is continuous, unlike in RGB.

	    l_h = cv2.getTrackbarPos("L-H", "Trackbars")
	    l_s = cv2.getTrackbarPos("L-S", "Trackbars")
	    l_v = cv2.getTrackbarPos("L-V", "Trackbars")
	    w_h = cv2.getTrackbarPos("W-H", "Trackbars")
	    w_s = cv2.getTrackbarPos("W-S", "Trackbars")
	    w_v = cv2.getTrackbarPos("W-V", "Trackbars")



	    lower_blue = np.array([l_h, l_s, l_v])                 # We define the color ranges
	    upper_blue = np.array([w_h, w_s, w_v])

	    mask = cv2.inRange(hsv, lower_blue, upper_blue)       # We create a mask with the color range we defined
	    res = cv2.bitwise_and(frame, frame, mask=mask)      # Logical and between mask and frame

		#Contour detection
	    if int(cv2.__version__[0]) > 3:
	        # Opencv 4.x.x
	        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	    else:
	        # Opencv 3.x.x
	        _, contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	    for cnt in contours:
	        area = cv2.contourArea(cnt)
	        if(area > 1000):
	            cv2.drawContours(res, cnt, -1, (0,0,255), 3)

	    # cv2.imshow('frame', frame)
	    # cv2.imshow('mask', mask)
	    cv2.namedWindow(file_name,cv2.WINDOW_NORMAL)
	    cv2.imshow(file_name, res)

	    # Check ESC key to exit
	    k = cv2.waitKey(5) & 0xFF
	    if k == 27:
	    	with open(file_name, 'w') as f:
	    		f.write("L_H: {}\n".format(l_h))
	    		f.write("L_S: {}\n".format(l_s))
	    		f.write("L_V: {}\n".format(l_v))
	    		f.write("W_H: {}\n".format(w_h))
	    		f.write("W_S: {}\n".format(w_s))
	    		f.write("W_V: {}\n".format(w_v))
	    		cv2.destroyAllWindows()
	    		cap.release()
	    	return [l_h, l_s, l_v, w_h, w_s, w_v]

if __name__ == "__main__":
	print(calibrate())