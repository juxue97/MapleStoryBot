import cv2
import numpy as np
import keyboard
import time
import pydirectinput,pyautogui

from windowcapture import WindowCapture #capture screenshots
#from vision import Vision   #just for debug
from model import ImageProcessor    #arrow detection model
from rune_detector import Detector  #rune detecor
from bot import BotState, AutoBot   #controller

def arrow_solver(directions):
    print(directions)
    time.sleep(0.2)
    pydirectinput.press(directions,interval=0.1)
    time.sleep(1.0)  
    pydirectinput.press(['f2'], presses=9,interval=0.3) 
    time.sleep(0.5)  
    pydirectinput.press(['f2'], presses=9,interval=0.3) 
    time.sleep(0.5)
    pydirectinput.press(['ctrlleft'], presses=2,interval=0.2)
    time.sleep(0.5)

#print("start - s")
print("quit - q") 
time.sleep(2) 

window_name = 'MapleStory' 
cfg_mob = 'yolov4-tiny/yolov4-tiny-custom.cfg'  
weights_mob = 'yolov4-tiny-custom_last.weights' 

#WindowCapture.list_window_names() 
wincap = WindowCapture(window_name)  
Rune = Detector(DEBUG=False,template='images/rune.jpg',threshold=0.95,color=(0,255,0)) 
Player = Detector(DEBUG=False,template='images/player.jpg',threshold=0.8 ,color=(255,0,0))  
Grey_buff = Detector(DEBUG=False,template='images/grey_buff.jpg',threshold=0.85,color=(0,0,255)) 

bot = AutoBot() 

Obj_detect = ImageProcessor(debug=True, img_size=wincap.get_window_size(), cfg_file=cfg_mob, weights_file=weights_mob) 
#print(wincap.get_window_size() h)
#(1366, 769) 

# Start the thread
wincap.start()
time.sleep(0.1)  

Rune.start() 
Player.start()
Grey_buff.start()  
time.sleep(0.1) 

bot.start() 
time.sleep(0.1) 

Obj_detect.start()  
time.sleep(0.1)

DEBUG = False 
loop_time = time.time()
while (True): 
    ### Main operations happen here 
    # if None, go next loop 
    if wincap.screenshot is None: 
        print('no detected image') 
        continue 
  
    # Get the Screenshot of that window -> THREAD 1  vff  vff  vfff  vfff  vffff  vfff  vfff vfff
    ss=wincap.screenshot
    
    # Detect Runes, player
    Rune.update(ss)
    Player.update(ss)
    Grey_buff.update(ss)
    #print(Player.coor,Rune.coor)
    
    # AutoBoting 
    #bot.update()
    # update the bot with the data it needs right now
    if bot.state == BotState.INITIALIZING:
        #print(bot.state)
        pass

    elif bot.state == BotState.REPLACEMENT:
        bot.update(Player.coor,Rune.coor,Grey_buff.coor)
        #print(bot.state)

    elif bot.state == BotState.REPETITIVE:
        #print(bot.state)
        pass
    
    elif bot.state == BotState.LOOT:
        bot.update(Player.coor,Rune.coor,Grey_buff.coor)
        #print(bot.state)
    
    # Arrow Detector
    Obj_detect.update(ss)
    if len(Obj_detect.coor) == 4: 
        results = []
        objs = Obj_detect.coor
        sorted_results = sorted(objs, key=lambda x: x['x'])

        for obj in sorted_results:
            results.append(obj['class_name'])

        arrow_solver(results)

      

    # Display Result - Draw rectangle
    if DEBUG: # display image to debug/visualize
        cv2.imshow("CV",ss)
        
    key = cv2.waitKey(1)

    ### print the time taken for each loop
    '''
    try:
        print('FPS {}'.format(1/(time.time() - loop_time)))
    except Exception as e:
        print(f"Error in run method: {e}")

    loop_time=time.time()
    '''
    #if key==ord('q'):
    #if keyboard.is_pressed('q'):

    #print(wincap.track_window())

    if keyboard.is_pressed('q') or wincap.track_window():

        wincap.stop()

        Rune.stop()
        Player.stop()
        Grey_buff.stop()

        bot.stop()
        Obj_detect.stop()

        if DEBUG:
            cv2.destroyAllWindows()

        break

print("done")

