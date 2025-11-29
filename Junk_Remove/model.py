import cv2 as cv
import numpy as np
from threading import Thread, Lock
import time

class ImageProcessor:
    # threading properties
    stopped = True
    lock = None
    coor = [] # fk this wasting my time for 2 hrs

    W = 0
    H = 0
    w,h = 0,0
    net = None
    ln = None
    classes = {}
    screenshot = None
    colors = []
    debug=None

    # preprocess parameters
    kernel_d = np.ones((10, 10), np.uint8)
    kernel_e = np.ones((10, 10), np.uint8)

    lower = np.array([0, 128, 152])
    upper = np.array([179, 255, 255])

    dilation_iterations = 1
    erosion_iterations = 1

    canny_low_threshold = 0
    canny_high_threshold = 0

    #crop properties
    #x_start, y_start, width, height = 400, 150,600,150

    def __init__(self,debug, img_size, cfg_file, weights_file):
        # create a thread lock object
        self.lock = Lock()

        #Load the model
        np.random.seed(42)
        self.net = cv.dnn.readNetFromDarknet(cfg_file, weights_file)
        self.net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
        self.ln = self.net.getLayerNames()
        self.ln = [self.ln[i-1] for i in self.net.getUnconnectedOutLayers()]
        self.W = img_size[0]
        self.H = img_size[1]
        self.debug = debug
        
        with open('yolov4-tiny/obj.names', 'r') as file:
            lines = file.readlines()
        for i, line in enumerate(lines):
            self.classes[i] = line.strip()

        # If you plan to utilize more than six classes, please include additional colors in this list.
        self.colors = [
            (0, 0, 255),    # Red
            (0, 255, 0),    # Green
            (255, 0, 0),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (128, 0, 128),  # Purple
            (128, 128, 0),  # Olive
        ] 

    def preprocess(self,img):
        if img is not None:
            hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

            # Apply the thresholds
            mask = cv.inRange(hsv, self.lower, self.upper)
            result = cv.bitwise_and(hsv, hsv, mask=mask)  

            blurred = cv.GaussianBlur(result, (1, 1), 0)
            edges = cv.Canny(blurred, self.canny_low_threshold, self.canny_high_threshold)

            dilated = cv.dilate(edges, self.kernel_d, self.dilation_iterations)
            eroded = cv.erode(dilated, self.kernel_e, self.erosion_iterations)

            return eroded
        
    def process_image(self, img):
        if not img is None :
            #print('here i am')
            # Convert the image to grayscale

            preprocessed_img = self.preprocess(img)
            #cv.imshow('dark',preprocessed_img)
            #cv.waitKey(1)
            preprocessed_img = cv.merge([preprocessed_img] * 3)

            blob = cv.dnn.blobFromImage(preprocessed_img, 1/255.0, (416, 416), swapRB=True, crop=False)
            
            self.net.setInput(blob)
            outputs = self.net.forward(self.ln)
            outputs = np.vstack(outputs)
            #print(outputs)
            
            coordinates = self.get_coordinates(outputs, 0.3) # tunable

            ## Use for debugging / check if object detection work well
            #self.draw_identified_objects(img, coordinates)
            #cv.imshow('gray_scale',img)
            #cv.waitKey(1)
            if self.debug == True:
                if img is None:
                    return 'NO IMAGE PASSED'
                
                for coordinate in coordinates:
                    x = coordinate['x']
                    y = coordinate['y']
                    w = coordinate['w']
                    h = coordinate['h']
                    classID = coordinate['class']
                    
                    color = self.colors[classID]
                    
                    cv.rectangle(preprocessed_img, (x,y), (x + w, y + h), color, 2)
                    cv.putText(preprocessed_img, self.classes[classID], (x, y - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                #cv.imshow('Arrow',preprocessed_img)
                #cv.waitKey(1)
            return coordinates
        else:
            print('img is None')

    def get_coordinates(self, outputs, conf):

        boxes = []
        confidences = []
        classIDs = []

        for output in outputs:
            scores = output[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]
            
            #detect player, monster, rune
            if confidence > conf: 
                x, y, w, h = output[:4] * np.array([self.W, self.H, self.W, self.H])
                p0 = int(x - w//2), int(y - h//2)
                boxes.append([*p0, int(w), int(h)])
                confidences.append(float(confidence))
                classIDs.append(classID)

        indices = cv.dnn.NMSBoxes(boxes, confidences, conf, conf-0.1)

        if len(indices) == 0:
            return []

        coordinates = []
        for i in indices.flatten():
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            coordinates.append({'x': x, 'y': y, 'w': w, 'h': h, 'class': classIDs[i], 'class_name': self.classes[classIDs[i]]})
        return coordinates

    def draw_rectangles(self, img, coordinates):
        if img is None:
            return 'NO IMAGE PASSED'
        
        for coordinate in coordinates:
            x = coordinate['x']
            y = coordinate['y']
            w = coordinate['w']
            h = coordinate['h']
            classID = coordinate['class']
            
            color = self.colors[classID]
            
            cv.rectangle(img, (x,y), (x + w, y + h), color, 2)
            cv.putText(img, self.classes[classID], (x, y - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        return img

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
        cv.destroyAllWindows()

    def run(self):
        # TODO: you can write your own time/iterations calculation to determine how fast this is
        while not self.stopped:
            try:
                if not self.screenshot is None:
                    # do object detection
                    coordinates = self.process_image(self.screenshot)
                    # lock the thread while updating the results
                    self.lock.acquire()
                    self.coor = coordinates
                    self.lock.release()
                    time.sleep(0.01)  
            except Exception as e:
                print(f"Error in run method: {e}")

            