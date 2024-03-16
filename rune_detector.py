import cv2 as cv
import numpy as np
from threading import Thread, Lock
import time




class Detector:
    # threading properties
    lock = None
    coor = [] # fk this wasting my time for 2 hrs
    classes = {}

    img=None
    template=None
    DEBUG=None
    threshold = 0
    w,h =0,0
    locations = None
    key=None

    def __init__(self,DEBUG,template,threshold,color):
        # create a thread lock object
        self.lock = Lock()
        
        #properties
        self.template = template
        self.DEBUG = DEBUG
        self.color = color
        self.threshold=threshold

        with open('images/classes.txt', 'r') as file:
            lines = file.readlines()
        for i, line in enumerate(lines):
            self.classes[i] = line.strip()
    
    def process_image(self,template_path,img):

        template = cv.imread(template_path,0)
        self.img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        w,h = template.shape[::-1]

        result = cv.matchTemplate(self.img,template,cv.TM_CCOEFF_NORMED)
        locations = np.where(result >= self.threshold)
        #print('did i enter here')
        if self.DEBUG: # display image to debug/visualize
            #print("DEBUG:True")
            self.rp_detector(img,w,h,locations)
            cv.imshow("CV",img)
        cv.waitKey(1)

        return w,h,locations

    def rp_detector (self,img,w,h,locations):
        # Check if locations is an iterable (tuple, list, etc.)
        if isinstance(locations, (tuple, list)):
            for pt in zip(*locations[::-1]):
                cv.rectangle(img, pt, (pt[0] + w, pt[1] + h), self.color, 2)
        else:
            print("Invalid locations format:", locations)

        return img
    
    def get_coordinate(self, w,h,locations):
        if isinstance(locations, (tuple, list)):
            if len(locations) == 0:
                return []
            else:
                coordinates = []
                for pt, w, h in zip(zip(*locations[::-1]), [w] * len(locations[0]), [h] * len(locations[0])):
                    center_x = pt[0] + w // 2
                    center_y = pt[1] + h // 2
                    coordinates.append({'x': pt[0], 'y': pt[1], 'w': w, 'h': h, 'center_x': center_x, 'center_y': center_y})
                return coordinates
        
        else:
            print("Invalid locations format:", locations)
            
    #Threading funcitons#

    def update(self, screenshot):
        self.lock.acquire()
        self.screenshot = screenshot
        self.lock.release()

    def start(self):
        self.stopped = False
        t = Thread(target=self.run)
        t.start()

    def stop(self):
        self.stopped = True

    def run(self):
        # TODO: you can write your own time/iterations calculation to determine how fast this is
        while not self.stopped:
            try:
                if not self.screenshot is None:
                    # do object detection
                    self.w,self.h,self.locations = self.process_image(self.template,self.screenshot)
                    # lock the thread while updating the results
                    self.lock.acquire()
                    self.coor = self.get_coordinate(self.w,self.h,self.locations)
                    self.lock.release()
                    time.sleep(0.01)  
            except Exception as e:
                print(f"Error in run method: {e}")

            

