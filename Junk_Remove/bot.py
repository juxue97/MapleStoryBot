import pydirectinput,pyautogui
from threading import Thread, Lock
import time
import random

from model import ImageProcessor


class BotState:
    INITIALIZING = 0
    REPLACEMENT = 1
    REPETITIVE = 2
    LOOT = 3

class AutoBot:
    # threading properties
    stopped = True
    lock = None
    
    initializing_timing = 5
    speed = 13.81703
    offset = 0.1
    mode=None
    state=None
    timestamp=None
    pc,rc,gb=[],[],[]

    Rune = False #flag for rune
    rune_flag = False

    def __init__(self):
        self.lock = Lock()

        self.state = BotState.INITIALIZING
        self.timestamp = time.time()

    def random_num(self,lb,ub):
        random_number = random.uniform(lb,ub)
        #print(random_number)
        return format(random_number, '.3f')

    def replacement(self,option):
        if option == 'df':
            pydirectinput.press('home')     #place dark flare
            time.sleep(0.89)
    
        elif option == 'sv':
            pydirectinput.press('pageup')   #place veil
            time.sleep(0.69)
    
        elif option == 'es':
            with pyautogui.hold('down'):
                pydirectinput.press('2')       # place erda shower
                time.sleep(0.943)

    # Attack Rotation Function
                
    def attack(self,mode):
        if mode == 1: #setup from beginning
            with pyautogui.hold('right'):
                pydirectinput.press(['space','space','v','f','f','f'],interval=self.random_num(0.102,0.123),presses=2)
                time.sleep(0.05)
                pydirectinput.press(['space','v','f','f'],interval=self.random_num(0.102,0.122))
            pydirectinput.press('altleft')
            time.sleep(1.78)

            self.replacement(option = 'es')  # erda

            with pyautogui.hold('down'):
                pydirectinput.press(['space','5','f','f','f'],interval=self.random_num(0.15,0.20))
            time.sleep(0.1)

            with pyautogui.hold('left'):
                pydirectinput.press(['space','space','v','f','f','f'],interval=self.random_num(0.12,0.14))
                pydirectinput.press(['space','v','f','f','f'],interval=self.random_num(0.10,0.12))
            time.sleep(0.1)

            pydirectinput.press('altleft')
            time.sleep(1.62)

            self.replacement(option='df')   # df

        elif mode == 2:
            pydirectinput.keyDown('down')
            pydirectinput.keyDown('left')
            pydirectinput.press('space')
            pydirectinput.press('h')
            pydirectinput.keyUp('down')
            pydirectinput.keyUp('left')
            time.sleep(0.1)

            # repetitive whack after placement
            for i in range(4):
                with pyautogui.hold('right'):
                    pydirectinput.press(['space','space','v','f','f'],presses=3,interval=self.random_num(0.16,0.20))
                time.sleep(0.05)
                with pyautogui.hold('left'):
                    pydirectinput.press(['space','space','v','f','f'],presses=3,interval=self.random_num(0.16,0.20))
                time.sleep(0.05)

            self.replacement('sv')
    
        elif mode == 3:
            # go loot after the loop done
            # return to initial state
            pydirectinput.press('altleft')
            time.sleep(1.58)
            with pyautogui.hold('right'):
                pydirectinput.press(['space','space','v','f','f','f'],interval=self.random_num(0.16,0.18),presses=2)
            time.sleep(0.1)
            pydirectinput.press('b')
            time.sleep(float(self.random_num(0.5,1.5)))
            with pyautogui.hold('down'):
                pydirectinput.press(['space','v','f','f','f'],interval=self.random_num(0.16,0.18))
            #time.sleep(0.1)  
                
            with pyautogui.hold('left'):
                pydirectinput.press(['space','space','v','f','f','f'],interval=self.random_num(0.16,0.20))
            time.sleep(0.1)

        elif mode == 4:
            with pyautogui.hold('left'):
                pydirectinput.press(['space','space','v','f','f','f'],interval=self.random_num(0.16,0.20),presses=3)

    def reset(self):
        with pyautogui.hold('left'):
            pydirectinput.press(['space','space','v','f','f','f'],interval=self.random_num(0.16,0.20),presses=2)

    
    def press_time(self,x):
        #time = dist / speed
        print('diff = ', x)
        if x > 0.1:
            time = round(x / self.speed,3) - self.offset #player at right of rune
            print('moving left with', time, 's')
            direction='left'
            return time,direction
        
        elif x<-0.1:
            time = round(abs(x) / self.speed,3)-self.offset #player at left of rune
            print('moving right with', time, 's')
            direction='right'
            return time,direction
        
        elif x==0:
            time = x + 0.01
            print('not really moving for', time, 's')
            direction='left' # any direction
            return time,direction

    def movement_calculation(self):
        #horizonatal measurement
        xp=self.pc[0]['x']
        xr=self.rc[0]['x']
        t,dir=self.press_time(xp-xr)

        #vertical measurement
        yp=self.pc[0]['y']
        yr=self.rc[0]['y']
        print('yp=',yp,'yr=',yr)
        y_diff = yp-yr
        print(abs(y_diff))

        return t,dir,yp,yr
    
    def rune_action(self):
        time.sleep(0.1)
        print(self.pc,self.rc,len(self.gb))
        self.rune_flag = True
        while True:
            try :
                if self.rc == [] and len(self.gb) == 0:
                    time.sleep(2)
                    pydirectinput.press('\\')
                    time.sleep(0.5)
                    time.sleep(4)
                    break

                elif self.pc and self.rc and len(self.gb) == 0:
                    # Check if the rune already on same spot

                    print('measuring t,dir,yp,yr')
                    detected_rune = True
                    
                    t,dir,yp,yr = self.movement_calculation()

                else:
                    detected_rune=False
                    time.sleep(6)
                    #wait few secs so that the arrow solver do their work

                    break

            except Exception as e:
                print(f"Error in run method: {e}")      
            try:
                if detected_rune:
                    #horizontal movement
                    if t>0:
                        pydirectinput.keyDown(dir)
                        time.sleep(t)
                        pydirectinput.keyUp(dir)
                    yp=self.pc[0]['y']
                    #yr=self.rc[0]['y']
                    print('pos after moving hori:',yp)
                    time.sleep(2) #pause for sometime
                    
                    #vertical movement
                    if abs(yp-yr)<8:               # player is same lane as rune
                        time.sleep(2)
                        #pydirectinput.press('\\')
                        #time.sleep(0.5)

                    elif yp>yr and abs(yp-yr)>8:      # player is below rune
                        print('move up')
                        pydirectinput.press('altleft')
                        time.sleep(3)
                        #pydirectinput.press('\\')
                        #time.sleep(0.5)

                    elif yp<yr and abs(yp-yr)>8:     # yp<yr player above rune
                        print('move down')
                        with pyautogui.hold('down'):\
                            pydirectinput.press('space')
                        time.sleep(2)
                        #pydirectinput.press('\\')
                        #time.sleep(0.5)

                    detected_rune=False
            except Exception as e:
                print(f"Error in run method: {e}") 
        self.reset()
        self.state = BotState.REPLACEMENT
        self.Rune = False

    # Threading functions

    def update(self,pc,rc,gb=None):
        if len(self.pc) > 0 and len(self.rc) > 0 and len(self.gb) == 0 :
            self.Rune = True

        self.lock.acquire()
        self.pc=pc
        self.rc=rc
        self.gb=gb
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
                if self.state==BotState.INITIALIZING:
                    #wait for sometime to initialize the rotation
                    if time.time() > self.timestamp + self.initializing_timing:
                        self.lock.acquire()
                        self.state = BotState.REPLACEMENT
                        self.lock.release()

                elif self.state==BotState.REPLACEMENT:
                    self.attack(mode=1)

                    if self.Rune:
                        print("Rune Detected")
                        self.rune_action()
                        continue 

                    self.lock.acquire()
                    self.state = BotState.REPETITIVE
                    self.lock.release()

                elif self.state==BotState.REPETITIVE:
                    self.attack(mode=2)

                    self.lock.acquire()
                    self.state = BotState.LOOT
                    self.lock.release()

                elif self.state==BotState.LOOT:
                    self.attack(mode=3)

                    if self.Rune:
                        print("Rune Detected")
                        self.rune_action()
                        continue 
                    self.attack(mode=4)

                    self.lock.acquire()
                    self.state = BotState.REPLACEMENT
                    self.lock.release()

            except Exception as e:
                print(f"Error in run method: {e}")