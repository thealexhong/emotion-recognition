from naoqi import ALModule
from naoqi import ALProxy
from naoqi import ALBroker
from GenUtil import GenUtil
import time
import sys


class NAOReactionChecker(ALModule):
    def __init__(self, genUtil, ip = "luke.local", port = 9559):
        self.name ="naoReactionChecker"
        ALModule.__init__(self, self.name)
        
        self.genUtil = genUtil

        global subscribed
        subscribed = False
        
        global memory
        memory = ALProxy("ALMemory")
        SubscribeAllEvents()
        
    def __del__(self):
        UnsubscribeAllEvents()
        self.exit()
        
    def onTouched(self, strVarName, value):
        if self.genUtil.naoIsSafe:
            UnsubscribeAllEvents()
            self.genUtil.naoWasTouched(strVarName)
            SubscribeAllEvents()
        else:
            print "NAO is already scared"

    def onPickUp(self, strVarName, value, subscriberIdentifier):
        if self.genUtil.naoIsSafe:
            UnsubscribeAllEvents()
            print("Pick Up event detected:",  value)
            if value == False:
                self.genUtil.naoWasPickedUp()
            else:
                self.naoSayHappy("Thank you.")
            SubscribeAllEvents()
        else:
            print "NAO is already scared"

def SubscribeAllEvents():
    global subscribed
    if not subscribed:
        SubscribeAllTouchEvent()
        SubscribePickUpEvent()
        subscribed = True

def UnsubscribeAllEvents():
    global subscribed
    if subscribed:
        subscribed = False
        UnsubscribeAllTouchEvent()
        UnsubscribePickUpEvent()

def SubscribeAllTouchEvent():
    print "Subscribe Touch Events"
    name = "naoReactionChecker"
    onTouch = "onTouched"
    sensors = ["RightBumperPressed", "LeftBumperPressed",
               "FrontTactilTouched", "MiddleTactilTouched",
               "RearTactilTouched", "HandRightBackTouched", "HandRightLeftTouched", "HandRightRightTouched",
               "HandLeftBackTouched", "HandLeftLeftTouched", "HandLeftRightTouched"]
    for sensor in sensors:
        memory.subscribeToEvent(sensor, name, onTouch)

def UnsubscribeAllTouchEvent():
    name = "naoReactionChecker"
    sensors = ["RightBumperPressed", "LeftBumperPressed",
               "FrontTactilTouched", "MiddleTactilTouched",
               "RearTactilTouched", "HandRightBackTouched", "HandRightLeftTouched", "HandRightRightTouched",
               "HandLeftBackTouched", "HandLeftLeftTouched", "HandLeftRightTouched"]
    for sensor in sensors:
        memory.unsubscribeToEvent(sensor, name)
    print "Unsubscribe Touch Events"

def SubscribePickUpEvent():
    print "Subscribe Pick Up Events"
    memory.subscribeToEvent("footContactChanged","naoReactionChecker","onPickUp")

def UnsubscribePickUpEvent():
    memory.unsubscribeToEvent("footContactChanged", "naoReactionChecker")
    print "Unsubscribe Pick Up Events"


# NAOip = "luke.local"
# NAOport = 9559
# myBroker = ALBroker("myBroker", "0.0.0.0", 0, NAOip, NAOport)
# global naoTouchChecker
# naoTouchChecker = NAOTouchChecker()
#
# print "Is it present?: ", myBroker.isModulePresent("NAOTouchChecker")
#
# try:
#     while True:
#         print "Waiting..."
#         time.sleep(10)
# except KeyboardInterrupt:
#     print
#     print "Ending"
#     myBroker.shutdown()
#     sys.exit(0)


