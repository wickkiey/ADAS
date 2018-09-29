import numpy as np
import cv2 as cv
from matplotlib import  pyplot as plt
#Extract white/yellow lines
def extract_wy(image,sensitivity=50):
    lower_white = np.array([0, 0, 255 - sensitivity])
    upper_white = np.array([255, sensitivity, 255])
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    maskw = cv.inRange(hsv.copy(), lower_white, upper_white)

    lower_yellow = np.array([10,100,100])
    upper_yellow = np.array([30, 255, 255])
    masky = cv.inRange(hsv.copy(), lower_yellow, upper_yellow)
    return cv.bitwise_or(maskw, masky)

#Trasform (perspective) image to get top view (birds view)
def transform(image):
    #Transform
    rows,cols = image.shape[:2]
    srcpt = np.float32([(580, 460), (205, 720), (1110, 720), (703, 460)])
    dstpt = np.float32([(320, 0), (320, 720), (960, 720), (960, 0)])
    M = cv.getPerspectiveTransform(srcpt,dstpt)
    p_trans = cv.warpPerspective(image,M,(cols,rows))
    #show_img(p_trans)
    return  p_trans

def rev_transform(image):
    #Transform
    rows,cols = image.shape[:2]
    srcpt = np.float32([(580, 460), (205, 720), (1110, 720), (703, 460)])
    dstpt = np.float32([(320, 0), (320, 720), (960, 720), (960, 0)])
    M = cv.getPerspectiveTransform(dstpt,srcpt)
    p_trans = cv.warpPerspective(image,M,(cols,rows))
    #show_img(p_trans)
    return  p_trans

#Extract vertical lines (considering as road lines)
#problem - can't able to extract curved line -
def extract_strtline(image):
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (2, 15))
    erode = cv.erode(image, kernel, iterations=1)
    dilute = cv.dilate(erode, kernel, iterations=2)
    return dilute

def extract_byfilter(image):
    slidewin = (20, 30)
    # Build kernel
    pweights = np.ones(slidewin, np.uint8)
    nweights = -1 * np.ones(slidewin, np.uint8)
    kernel = np.concatenate((nweights, pweights, nweights), axis=1)
    return (cv.filter2D(image, cv.CV_8U, kernel))

#Find center point from given rectangle
#hardcoded values are related to rectangle -predefined - need to generalize
def find_center(img):
    cnts = cv.findContours(img.copy(), cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)
    if(np.sum(cnts[0])>3):
        M = cv.moments(cnts[0])
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        #cv.circle(img.copy,(cx,cy),5,255,-1)
        return (cx,cy)
    else:
        return (30,0)

#Path finder
def find_path(image):
    colmeans = cv.reduce(image, 0, cv.REDUCE_AVG)
    left_lane = np.argmax(colmeans[0:640])
    right_lane = np.argmax(colmeans[0, 640:]) + 640

    # Custom filter
    kernel = np.array([[1, 0, -1]])
    fd = cv.filter2D(image, -1, kernel)

    rows, cols = image.shape[:2]
    win_size = (80, 120)
    llane_points = []
    rlane_points = []
    mask = np.zeros((rows, cols, 3),np.uint8)
    for r in range(rows, 0, -win_size[0]):
        lcenter = find_center(fd[r - 80:r, left_lane - 60:left_lane + 60])
        cv.circle(mask,(lcenter[0]+(left_lane-60),r-40),15,(0,0,255),7)
        llane_points.append([lcenter[0] + (left_lane - 60), r - 40])
        rcenter = find_center(fd[r - 80:r, right_lane - 60:right_lane + 60])
        cv.circle(mask,(rcenter[0]+(right_lane-60),r-40),15,(255,0,0),7)
        rlane_points.append([lcenter[0] + (right_lane - 60), r - 40])

    #return  llane_points,rlane_points
    # return image
    return rev_transform(mask)


cap = cv.VideoCapture('rsrc/pv.mp4')
while(cap.isOpened()):
    ret, frame = cap.read()
    if(ret==True):
        transformed = transform(frame)
        bw = extract_wy(transformed,80)
        rev_trans = rev_transform(transformed)
        #lines =extract_strtline(bw)
        fin = extract_byfilter(bw)
        path = find_path(fin)
        cv.imshow("transformed",transformed)
        cv.imshow("bw",bw)
        cv.imshow("reverse",rev_trans)
        cv.imshow('frame',fin)
        cv.imshow('path',path)
        #combine result
        final = cv.addWeighted(frame,0.4,path,.6,0.0)
        cv.imshow("result",final)
        if cv.waitKey(1) & 0xFF == ord('q'):
            cv.imwrite("fin.jpg",fin)
            break
    else:
        print("frame on end")
        break

cap.release()
cv.destroyAllWindows()

