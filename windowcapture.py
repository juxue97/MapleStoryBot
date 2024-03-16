import win32gui
import win32ui
import win32con
import numpy as np
import os
import time
import cv2
import keyboard
from threading import Thread, Lock

class WindowCapture:
    # Add Threading Properties
    stopped = True
    lock = None
    screenshot = None
    
    #properties
    #initialize
    w = 0  
    h = 0
    hwnd = None
    cropped_x=0
    cropped_y=0
    offset_x = 0
    offset_y = 0

    def __init__(self, window_name=None):
        # create a thread lock object
        self.lock = Lock()
        self.window_name = window_name

        if window_name is None:
            self.hwnd = win32gui.GetDesktopWindow()
        #find the window
        self.hwnd = win32gui.FindWindow(None, window_name)
        if not self.hwnd:
            raise Exception('Window not found: {}'.format(window_name))

        #define the monitor width and height
        #self.w=1920
        #self.h=1080

        #get the window size
        window_rect = win32gui.GetWindowRect(self.hwnd)
        print(window_rect)
        #(left,top,right,bottom)
        self.w = window_rect[2]-window_rect[0]
        self.h = window_rect[3]-window_rect[1]
        #print(self.w)
        #print(self.h)
        
        #remove the window_border
        #border_pixels=13
        #titlebar_pixels=47
        border_pixels = 8
        titlebar_pixels = 30
        self.w = self.w - (border_pixels * 2)
        self.h = self.h - titlebar_pixels - border_pixels
        self.cropped_x = border_pixels
        self.cropped_y = titlebar_pixels

        # set the cropped coordinates offset so we can translate screenshot
        # images into actual screen positions
        self.offset_x = window_rect[0] + self.cropped_x
        self.offset_y = window_rect[1] + self.cropped_y

    def track_window(self):
        try:
            self.hwnd = win32gui.FindWindow(None, self.window_name)
            
            if not self.hwnd:
                return True
            
            return False
        
        except Exception as e:
            return True
            #print ('Window not found: {}'.format(self.window_name))
        
        

    def get_screenshot(self):

        #bmpfilenamename = "out.bmp" #set this
        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj=win32ui.CreateDCFromHandle(wDC)
        cDC=dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0,0),(self.w, self.h),dcObj,(self.cropped_x,self.cropped_y), win32con.SRCCOPY)
        #save
        #dataBitMap.SaveBitmapFile(cDC, 'debug.bmp')

        #for more speed
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (self.h,self.w,4)

        # Free Resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        #drop the alpha channel
        img = img[...,:3]
        img = np.ascontiguousarray(img)

        return img

    #get name of windows
    @staticmethod
    def list_window_names():
        def winEnumHandler(hwnd,ctx):
            if win32gui.IsWindowVisible(hwnd):
                print (hex(hwnd), win32gui.GetWindowText(hwnd))
        win32gui.EnumWindows( winEnumHandler, None )

    #set offset
    def get_screen_position(self, pos):
        return (pos[0] + self.offset_x, pos[1] + self.offset_y)
    
    #generate dataset
    def generate_dataset(self,filtered_image=None):
        # 0 - color
        # 1 - hsv filter
        if not os.path.exists('images/train'):
            os.mkdir('images/train')
        while True:
            img = self.get_screenshot()
            cv2.imwrite('images/train/{}.jpg'.format(len(os.listdir('images/train'))),img)
            time.sleep(0.3)

            if keyboard.is_pressed('d'):
               print('collection done')
               break

    #return window size
    def get_window_size(self):
        return (self.w, self.h)
    
    # threading methods

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
                screenshot = self.get_screenshot()
                self.lock.acquire()
                self.screenshot = screenshot
                self.lock.release()
                time.sleep(0.01)
            except Exception as e:
                print(f"Error in run method: {e}")


