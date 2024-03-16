import cv2
import numpy as np
import keyboard
import time
import os
from windowcapture import WindowCapture #capture screenshots
from vision import Vision   # TODO - Change the content to apply filter

print("start - s")
print("quit - q")
time.sleep(2)
keyboard.wait('s')

window_name = 'MapleStory'

#WindowCapture.list_window_names()
wincap = WindowCapture(window_name)
filter = Vision()
filter.init_control_gui()

DEBUG = True
#initialize the filter values
#hsv_filter = filter(0, 180, 129, 15, 229, 243, 143, 0, 67, 0)

loop_time = time.time()
while (True):
    ### Main operations happen here
    
    # take snapshot
    screenshot = wincap.get_screenshot()
    filtered_image = filter.apply_filter(screenshot)

    # Display Result
    if DEBUG: # display image to debug/visualize
        cv2.imshow("original",screenshot)
        #cv2.imshow("filtered_image",filtered_image)
    key = cv2.waitKey(1)

    ### print the time taken for each loop
    print('FPS {}'.format(1 / (time.time() - loop_time)))
    loop_time=time.time()

    if key==ord('q'):
        cv2.destroyAllWindows()
        break

    if key ==ord('g'):
        print('take ss now')
        wincap.generate_dataset()   

    # Save filtered image when 'a' is pressed
    if key == ord('a'):
        print('Saving filtered image...')
        cv2.imwrite('images/train/{}.jpg'.format(len(os.listdir('images/train'))), filtered_image)


print("done")


