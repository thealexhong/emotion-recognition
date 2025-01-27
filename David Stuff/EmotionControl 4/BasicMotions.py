from naoqi import ALProxy
from naoqi import ALModule
import vision_definitions
import cv2
import numpy as np
import math
import time
import random

class BasicMotions(ALModule):
    def __init__(self, ip, port, _myBroker):
        self.NAOip = ip
        self.NAOport = port
        #========SETUP FOR MOTION=============
        ALModule.__init__(self, "BasicMotions")
        self.myBroker=_myBroker
        bModulePresent = self.myBroker.isModulePresent("BasicMotions")
        print("BasicMotions module status:", bModulePresent)
        global memory
        memory = ALProxy("ALMemory")
        self.SubscribeAllTouchEvent()
        self.createEyeGroup()
        self.eyeColor={'happy':     0x0000FF00,
                       'sad':       0x00000060,
                       'scared1':   0x00600088,
                       'scared2':   0x00600088,
                       'fear':      0x00600088,
                       'hope':      0x00FFB428,
                       'anger':     0x00FF0000}
        self.eyeShape={'happy': "EyeTop",
                       'sad': "EyeBottom",
                       'scared1': "EyeNone",
                       'scared2': "EyeNone",
                       'fear': "EyeBottom",
                       'hope': "EyeTop",
                       'anger': "EyeTopBottom"}
        self.bScared = False
        #=========SETUP FOR VOICE================
        self.tts = ALProxy("ALTextToSpeech")
        audioProxy = ALProxy("ALAudioDevice")
        audioProxy.setOutputVolume(100)
        #Valid Value:50 to 200
        self.ttsPitch={      'default':   "\\vct=100\\",
                             'happy':     "\\vct=120\\",
                             'sad':       "\\vct=50\\",
                             'scared':    "\\vct=150\\",
                             'fear':      "\\vct=65\\",
                             'hope':      "\\vct=100\\",
                             'anger':     "\\vct=55\\"}
        #Valid Value: 50 to 400"\\
        self.ttsSpeed={      'default':   "\\rspd=100\\",
                             'happy':     "\\rspd=100\\",
                             'sad':       "\\rspd=70\\",
                             'scared':    "\\rspd=130\\",
                             'fear':      "\\rspd=75\\",
                             'hope':      "\\rspd=100\\",
                             'anger':     "\\rspd=110\\"}
        #Valid Value: 0 to 100
        self.ttsVolume={     'default':   "\\vol=050\\",
                             'happy':     "\\vol=060\\",
                             'sad':       "\\vol=035\\",
                             'scared':    "\\vol=070\\",
                             'fear':      "\\vol=050\\",
                             'hope':      "\\vol=050\\",
                             'anger':     "\\vol=060\\"}
        #============SETUP FOR PICKUP DETECTION====================
        self.SubscribePickUpEvent()
        #============SETUP FOR VIDEO====================
        self.camProxy = ALProxy("ALVideoDevice", self.NAOip, self.NAOport)
        self.resolution = vision_definitions.kQVGA
        self.colorSpace = vision_definitions.kBGRColorSpace
        self.fps = 10
        self.cameraId = self.camProxy.subscribe("python_GVM", self.resolution, self.colorSpace, self.fps)
        print "The camera ID is", self.cameraId
        self.camProxy.setActiveCamera(self.cameraId, vision_definitions.kBottomCamera)
        self.voteHoughLines=40
        #============You don't need this====================
        self.createDialog()

    def StiffnessOn(self, proxy):
        pNames = "Body"
        pStiffnessLists = 1.0
        pTimeLists = 0.05
        proxy.stiffnessInterpolation(pNames, pStiffnessLists, pTimeLists)

    def connectToProxy(self, proxyName):
        try:
            proxy = ALProxy(proxyName, self.NAOip, self.NAOport)
        except Exception, e:
            print "Could not create Proxy to ", proxyName
            print "Error was: ", e
        return proxy

    def naoSay(self, text):
        speechProxy = self.connectToProxy("ALTextToSpeech")

        speechProxy.say(text)
        print("------> Said something")

    def naoSit(self):
        self.UnsubscribeAllTouchEvent()
        motionProxy = self.connectToProxy("ALMotion")
        postureProxy = self.connectToProxy("ALRobotPosture")
        self.bScared = False
        motionProxy.wakeUp()
        self.StiffnessOn(motionProxy)
        sitResult = postureProxy.goToPosture("Sit", 0.5)
        if (sitResult):
            print("------> Sat Down")
        else:
            print("------> Did NOT Sit Down...")
        self.SubscribeAllTouchEvent()

    def naoStand(self):
        self.UnsubscribeAllTouchEvent()
        motionProxy = self.connectToProxy("ALMotion")
        postureProxy = self.connectToProxy("ALRobotPosture")

        motionProxy.wakeUp()
        self.StiffnessOn(motionProxy)
        standResult = postureProxy.goToPosture("StandInit", 0.3)
        if (standResult):
            self.bScared = False
            print("------> Stood Up")
        else:
            print("------> Did NOT Stand Up...")
        self.SubscribeAllTouchEvent()

    def naoWalk(self, xpos, ypos):
        self.UnsubscribeAllTouchEvent()
        motionProxy = self.connectToProxy("ALMotion")
        postureProxy = self.connectToProxy("ALRobotPosture")

        motionProxy.wakeUp()
        standResult = postureProxy.goToPosture("StandInit", 0.5)
        motionProxy.setMoveArmsEnabled(True, True)
        motionProxy.setMotionConfig([["ENABLE_FOOT_CONTACT_PROTECTION", True]])
        turnAngle = math.atan2(ypos,xpos)
        walkDist = math.sqrt(xpos*xpos + ypos*ypos)
        try:
            motionProxy.walkTo(0.0,0.0, turnAngle)
            motionProxy.walkTo(walkDist,0.0,0.0)
            self.bScared = False
        except Exception, e:
            print "The Robot could not walk to ", xpos, ", ", ypos
            print "Error was: ", e
        standResult = postureProxy.goToPosture("Stand", 0.5)
        print("------> Walked Somewhere")
        self.SubscribeAllTouchEvent()

    def naoNodHead(self):
        self.UnsubscribeAllTouchEvent()
        motionProxy = self.connectToProxy("ALMotion")
        motionNames = ['HeadYaw', "HeadPitch"]
        times = [[0.7], [0.7]]
        motionProxy.angleInterpolation(motionNames, [0.0,0.0], times, True)
        for i in range(3):
            motionProxy.angleInterpolation(motionNames, [0.0, 1.0], times, True)
            motionProxy.angleInterpolation(motionNames, [0.0, -1.0], times, True)
        motionProxy.angleInterpolation(motionNames, [0.0,0.0], times, True)
        print("------> Nodded")
        self.SubscribeAllTouchEvent()

    def naoShadeHead(self):
        self.UnsubscribeAllTouchEvent()
        motionProxy = self.connectToProxy("ALMotion")
        motionNames = ['HeadYaw', "HeadPitch"]
        times = [[0.7], [0.7]] # time to preform (s)
        # resets the angle of the motions (angle in radians)
        motionProxy.angleInterpolation(motionNames, [0.0,0.0], times, True)
        # shakes the head 3 times, back and forths
        for i in range(3):
            motionProxy.angleInterpolation(motionNames, [1.0, 0.0], times, True)
            motionProxy.angleInterpolation(motionNames, [-1.0, 0.0], times, True)
        motionProxy.angleInterpolation(motionNames, [0.0,0.0], times, True)
        print("------> Nodded")
        self.SubscribeAllTouchEvent()

    def naoWaveRight(self):
        self.UnsubscribeAllTouchEvent()
        motionProxy = self.connectToProxy("ALMotion")
        rArmNames = motionProxy.getBodyNames("RArm")
        print rArmNames
        # set arm to the initial position
        rArmDefaultAngles = [math.radians(84.6), math.radians(-10.7),
                             math.radians(68.2), math.radians(23.3),
                             math.radians(5.8), 0.3]
        defaultTimes = [2,2,2,2,2,2]
        motionProxy.angleInterpolation(rArmNames, rArmDefaultAngles, defaultTimes, True)
        time.sleep(5)
        # wave setup
        waveNames = ["RShoulderPitch", "RShoulderRoll", "RHand"]
        waveTimes = [2, 2, 2]
        waveAngles = [math.radians(-11), math.radians(-40), 0.99]
        motionProxy.angleInterpolation(waveNames, waveAngles, waveTimes, True)
        time.sleep(5)

        for i in range(3):
            motionProxy.angleInterpolation(["RElbowRoll"],  math.radians(88.5), [1], True)
            motionProxy.angleInterpolation(["RElbowRoll"],  math.radians(27), [1], True)

        motionProxy.angleInterpolation(rArmNames, rArmDefaultAngles, defaultTimes, True)
        print("------> Waved Right")
        self.SubscribeAllTouchEvent()

    def naoWaveBoth(self):
        self.UnsubscribeAllTouchEvent()
        motionProxy = self.connectToProxy("ALMotion")

        rArmNames = motionProxy.getBodyNames("RArm")
        # set arm to the initial position
        rArmDefaultAngles = [math.radians(84.6), math.radians(-10.7),
                             math.radians(68.2), math.radians(23.3),
                             math.radians(5.8), 0.3]
        lArmNames = motionProxy.getBodyNames("LArm")
        lArmDefaultAngles = [math.radians(84.6), math.radians(10.7),
                             math.radians(-68.2), math.radians(-23.3),
                             math.radians(5.8), 0.3]
        defaultTimes = [2,2,2,2,2,2]
        motionProxy.angleInterpolation(rArmNames + lArmNames, rArmDefaultAngles + lArmDefaultAngles, defaultTimes + defaultTimes, True)

        # wave setup
        waveNames = ["RShoulderPitch", "RShoulderRoll", "RHand", "LShoulderPitch", "LShoulderRoll", "LHand"]
        waveTimes = [2, 2, 2, 2, 2, 2]
        waveAngles = [math.radians(-11), math.radians(-40), 0.99, math.radians(-11), math.radians(40), 0.99]
        motionProxy.angleInterpolation(waveNames, waveAngles, waveTimes, True)

        for i in range(3):
            waveNames = ["RElbowRoll", "LElbowRoll"]
            waveAngles = [math.radians(88.5), math.radians(-88.5)]
            motionProxy.angleInterpolation(waveNames,  waveAngles, [1,1], True)
            waveAngles = [math.radians(27), math.radians(-27)]
            motionProxy.angleInterpolation(waveNames,  waveAngles, [1,1], True)

        motionProxy.angleInterpolation(rArmNames + lArmNames, rArmDefaultAngles + lArmDefaultAngles, defaultTimes + defaultTimes, True)

        print("------> Waved Both")
        self.SubscribeAllTouchEvent()


### ================================================================================== davids stuff




    def naoRest(self):
        motionProxy = self.connectToProxy("ALMotion")
        motionProxy.rest()
        motionProxy.getSummary()

    def SubscribePickUpEvent(self):
        print("Subcribe Pick Up Events")
        memory.subscribeToEvent("footContactChanged","BasicMotions","onPickUp")

    def UnsubscribePickUpEvent(self):
        print("Unsubcribe Pick Up Events")
        memory.unsubscribeToEvent("footContactChanged", "BasicMotions")

    def onPickUp(self, strVarName, value, subscriberIdentifier):
        self.UnsubscribePickUpEvent()
        print("Pick Up event detected:",  value)
        if value == False:
            self.naoSayScared("Put me down.")
        else:
            self.naoSayHappy("Thank you.")
        self.SubscribePickUpEvent()

    def naoSayHappy(self,str):
        emotion = 'happy'
        sentence= self.ttsPitch[emotion]+  self.ttsVolume[emotion] +  self.ttsSpeed[emotion]
        sentence+=str
        self.tts.post.say(sentence)

    def naoSaySad(self,str):
        emotion = 'sad'
        sentence= self.ttsPitch[emotion]+  self.ttsVolume[emotion] +  self.ttsSpeed[emotion]
        sentence+=str
        self.tts.post.say(sentence)

    def naoSayScared(self,str):
        emotion = 'scared'
        sentence= self.ttsPitch[emotion]+  self.ttsVolume[emotion] +  self.ttsSpeed[emotion]
        sentence+=str
        self.tts.post.say(sentence)

    def naoSayFear(self,str):
        emotion = 'fear'
        sentence= self.ttsPitch[emotion]+  self.ttsVolume[emotion] +  self.ttsSpeed[emotion]
        sentence+=str
        self.tts.post.say(sentence)

    def naoSayHope(self,str):
        emotion = 'fear'
        sentence= self.ttsPitch[emotion]+  self.ttsVolume[emotion] +  self.ttsSpeed[emotion]
        sentence+=str
        self.tts.post.say(sentence)

    def naoSayAnger(self,str):
        emotion = 'anger'
        sentence= self.ttsPitch[emotion]+  self.ttsVolume[emotion] +  self.ttsSpeed[emotion]
        sentence+=str
        self.tts.post.say(sentence)

    def __del__(self):
        print("Quiting BasicMotions Module")
        self.camProxy.unsubscribe(self.cameraId)
        self.exit()
        self.myBroker.shutdown();


    def SubscribeAllTouchEvent(self):
        print("Subcribe Touch Events")
        '''
        memory.subscribeToEvent("RightBumperPressed", "BasicMotions", "onTouched")
        memory.subscribeToEvent("LeftBumperPressed", "BasicMotions", "onTouched")

        memory.subscribeToEvent("FrontTactilTouched", "BasicMotions", "onTouched")
        memory.subscribeToEvent("MiddleTactilTouched", "BasicMotions", "onTouched")
        memory.subscribeToEvent("RearTactilTouched", "BasicMotions", "onTouched")

        memory.subscribeToEvent("HandRightBackTouched", "BasicMotions", "onTouched")
        #memory.subscribeToEvent("HandRightLeftTouched", "BasicMotions", "onTouched")
        #memory.subscribeToEvent("HandRightRightTouched", "BasicMotions", "onTouched")

        memory.subscribeToEvent("HandLeftBackTouched", "BasicMotions", "onTouched")
        #memory.subscribeToEvent("HandLeftLeftTouched", "BasicMotions", "onTouched")
        #memory.subscribeToEvent("HandLeftRightTouched", "BasicMotions", "onTouched")
        '''

    def UnsubscribeAllTouchEvent(self):
        print("Unsubcribe Touch Events")
        '''
        memory.unsubscribeToEvent("RightBumperPressed", "BasicMotions")
        memory.unsubscribeToEvent("LeftBumperPressed", "BasicMotions")

        memory.unsubscribeToEvent("FrontTactilTouched", "BasicMotions")
        memory.unsubscribeToEvent("MiddleTactilTouched", "BasicMotions")
        memory.unsubscribeToEvent("RearTactilTouched", "BasicMotions")

        memory.unsubscribeToEvent("HandRightBackTouched", "BasicMotions")
        #memory.unsubscribeToEvent("HandRightLeftTouched", "BasicMotions")
        #memory.unsubscribeToEvent("HandRightRightTouched", "BasicMotions")

        memory.unsubscribeToEvent("HandLeftBackTouched", "BasicMotions")
        #memory.unsubscribeToEvent("HandLeftLeftTouched", "BasicMotions")
        #memory.unsubscribeToEunvent("HandLeftRightTouched", "BasicMotions")
        '''

    def onTouched(self, strVarName, value):
        #self.UnsubscribeAllTouchEvent()
        print("Touch event detected:",strVarName )
        #self.scaredEmotion1()
        #self.SubscribeAllTouchEvent()

    def createEyeGroup(self):
        ledProxy = self.connectToProxy("ALLeds")
        name1 = ["FaceLedRight6","FaceLedRight2",
                 "FaceLedLeft6", "FaceLedLeft2"]
        ledProxy.createGroup("LedEyeCorner",name1)
        name2 = ["FaceLedRight7","FaceLedRight0","FaceLedRight1",
                 "FaceLedLeft7","FaceLedLeft0","FaceLedLeft1"]
        ledProxy.createGroup("LedEyeTop",name2)
        name3 = ["FaceLedRight5","FaceLedRight4","FaceLedRight3",
                 "FaceLedLeft5","FaceLedLeft4","FaceLedLeft3"]
        ledProxy.createGroup("LedEyeBottom",name3)
        ledProxy.createGroup("LedEyeTopBottom",name2+name3)
        ledProxy.createGroup("LedEye",name1+name2+name3)

    def blinkEyes(self, color, duration, configuration):
        bAnimation= True;
        accu=0;
        rgbList=[]
        timeList=[]
        #Reset eye color to black
        self.setEyeColor(0x00000000,"LedEye")
        self.setEyeColor(color,"LedEyeCorner")
        if configuration == "EyeTop":
            self.setEyeColor(color, "LedEyeTop")
        elif configuration == "EyeBottom":
            self.setEyeColor(color, "LedEyeBottom")
        elif configuration == "EyeTopBottom":
            self.setEyeColor(color, "LedEyeTopBottom")
        else:
            bAnimation = False

        if bAnimation == True:
            while(accu<duration):
                newTimeList=[0.05,random.uniform(0.2, 1.0),0.1,0.05]
                accu+=(0.2+newTimeList[1])
                rgbList.extend([color,color,0x00000000,color])
                timeList.extend(newTimeList)
            try:
                ledProxy = self.connectToProxy("ALLeds")
                if configuration == "EyeTop":
                    ledProxy.post.fadeListRGB("LedEyeTop", rgbList, timeList)

                elif configuration == "EyeBottom":
                    ledProxy.post.fadeListRGB("LedEyeBottom", rgbList, timeList)

                else:
                    ledProxy.post.fadeListRGB("LedEyeTopBottom", rgbList, timeList)
            except BaseException, err:
                print err

    def setEyeColor(self, color ,configuration):
        rgbList=[color]
        timeList=[0.01]
        try:
            ledProxy = self.connectToProxy("ALLeds")
            ledProxy.fadeListRGB(configuration, rgbList, timeList)
        except BaseException, err:
            print err

    def setEyeEmotion(self,emotion):
        configuration = self.eyeShape[emotion]
        color = self.eyeColor[emotion]
        self.setEyeColor(0x00000000,"LedEye")
        self.setEyeColor(color,"LedEyeCorner")
        if configuration == "EyeTop":
            self.setEyeColor(color, "LedEyeTop")
        elif configuration == "EyeBottom":
            self.setEyeColor(color, "LedEyeBottom")
        elif configuration == "EyeTopBottom":
            self.setEyeColor(color, "LedEyeTopBottom")
        #self.setEyeColor(0x00111111, "LedEyeBottom")


    def updateWithBlink(self, names, keys, times, color, configuration):
        self.UnsubscribeAllTouchEvent()  #Already called in OnTouched
        postureProxy = self.connectToProxy("ALRobotPosture")
        standResult = postureProxy.goToPosture("StandInit", 0.3)
        if (standResult):
            print("------> Stood Up")
            try:
                # uncomment the following line and modify the IP if you use this script outside Choregraphe.
                print("Time duration is ")
                print(max(max(times)))
                self.blinkEyes(color,max(max(times))*3, configuration)
                motionProxy = self.connectToProxy("ALMotion")
                motionProxy.angleInterpolation(names, keys, times, True)
                print 'Tasklist: ', motionProxy.getTaskList();
                time.sleep(max(max(times))+0.5)
            except BaseException, err:
                print err
        else:
            print("------> Did NOT Stand Up...")
        self.SubscribeAllTouchEvent()

    def happyEmotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False
        names.append("HeadPitch")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([-0.0138481, -0.0138481, -0.50933, 0.00762796])

        names.append("HeadYaw")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([-0.00924587, -0.00924587, -0.0138481, -0.0138481])

        names.append("LAnklePitch")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([-0.345192, -0.357464, -0.354396, -0.354396])

        names.append("LAnkleRoll")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([0.00157595, 0.00157595, 0.00157595, 0.00157595])

        names.append("LElbowRoll")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([-0.99399, -0.99399, -0.983252, -0.99399])

        names.append("LElbowYaw")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([-1.37297, -1.37297, -1.37297, -1.37297])

        names.append("LHand")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([0.2572, 0.2572, 0.2572, 0.2572])

        names.append("LHipPitch")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([-0.447886, -0.447886, -0.447886, -0.447886])

        names.append("LHipRoll")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([4.19617e-05, 4.19617e-05, 4.19617e-05, 4.19617e-05])

        names.append("LHipYawPitch")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([0.0061779, -0.00455999, -0.00455999, -0.00455999])

        names.append("LKneePitch")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([0.70253, 0.70253, 0.70253, 0.70253])

        names.append("LShoulderPitch")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([1.4097, 1.4097, 1.42044, 1.4097])

        names.append("LShoulderRoll")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([0.291418, 0.291418, 0.28068, 0.291418])

        names.append("LWristYaw")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([-0.0123138, -0.0123138, -0.0123138, -0.0123138])

        names.append("RAnklePitch")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([-0.34971, -0.34971, -0.34971, -0.34971])

        names.append("RAnkleRoll")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([-0.00609398, 0.00464392, 0.00464392, 0.00464392])

        names.append("RElbowRoll")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([1.01555, 1.43893, 0.265424, 1.53251])

        names.append("RElbowYaw")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([1.3913, 1.64287, 1.61679, 1.35755])

        names.append("RHand")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([0.2544, 0.2544, 0.9912, 0.0108])

        names.append("RHipPitch")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([-0.45564, -0.45564, -0.444902, -0.444902])

        names.append("RHipRoll")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([0.00924587, -0.00149202, -0.00149202, -0.00149202])

        names.append("RHipYawPitch")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([0.0061779, -0.00455999, -0.00455999, -0.00455999])

        names.append("RKneePitch")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([0.70108, 0.70108, 0.70108, 0.70108])

        names.append("RShoulderPitch")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([1.41132, 0.535408, -1.0216, 0.842208])

        names.append("RShoulderRoll")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([-0.259288, 0.032172, 0.0444441, 0.202446])

        names.append("RWristYaw")
        times.append([0.8, 1.56, 2.12, 2.72])
        keys.append([0.026036, 1.63213, 1.63213, 1.63213])
        self.updateWithBlink(names, keys, times, self.eyeColor['happy'], self.eyeShape['happy'])
        #self.updateWithBlink(names, keys, times, 0x0000FF00, "EyeTop")

    def sadEmotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False
        names.append("HeadPitch")
        times.append([0.8, 1.36])
        keys.append([-0.0107799, 0.500042])

        names.append("HeadYaw")
        times.append([0.8, 1.36])
        keys.append([-0.00617791, 0.0383082])

        names.append("LAnklePitch")
        times.append([0.8, 1.36])
        keys.append([-0.34826, -0.254685])

        names.append("LAnkleRoll")
        times.append([0.8, 1.36])
        keys.append([-0.00609397, -0.0260359])

        names.append("LElbowRoll")
        times.append([0.8, 1.36])
        keys.append([-0.977116, -0.0383082])

        names.append("LElbowYaw")
        times.append([0.8, 1.36])
        keys.append([-1.37144, -1.37757])

        names.append("LHand")
        times.append([0.8, 1.36])
        keys.append([0.2592, 0.2588])

        names.append("LHipPitch")
        times.append([0.8, 1.36])
        keys.append([-0.446352, -0.639635])

        names.append("LHipRoll")
        times.append([0.8, 1.36])
        keys.append([0.00157595, 4.19617e-05])

        names.append("LHipYawPitch")
        times.append([0.8, 1.36])
        keys.append([-0.00455999, 0.0874801])

        names.append("LKneePitch")
        times.append([0.8, 1.36])
        keys.append([0.70253, 0.699462])

        names.append("LShoulderPitch")
        times.append([0.8, 1.36])
        keys.append([1.44038, 1.01853])

        names.append("LShoulderRoll")
        times.append([0.8, 1.36])
        keys.append([0.27301, -0.153442])

        names.append("LWristYaw")
        times.append([0.8, 1.36])
        keys.append([0.0152981, 1.29772])

        names.append("RAnklePitch")
        times.append([0.8, 1.36])
        keys.append([-0.34971, -0.271475])

        names.append("RAnkleRoll")
        times.append([0.8, 1.36])
        keys.append([0.00310993, -0.00762796])

        names.append("RElbowRoll")
        times.append([0.8, 1.36])
        keys.append([0.978734, 0.038392])

        names.append("RElbowYaw")
        times.append([0.8, 1.36])
        keys.append([1.36982, 0.519984])

        names.append("RHand")
        times.append([0.8, 1.36])
        keys.append([0.2672, 0.2612])

        names.append("RHipPitch")
        times.append([0.8, 1.36])
        keys.append([-0.454105, -0.651992])

        names.append("RHipRoll")
        times.append([0.8, 1.36])
        keys.append([4.19617e-05, -0.00762796])

        names.append("RHipYawPitch")
        times.append([0.8, 1.36])
        keys.append([-0.00455999, 0.0874801])

        names.append("RKneePitch")
        times.append([0.8, 1.36])
        keys.append([0.704148, 0.737896])

        names.append("RShoulderPitch")
        times.append([0.8, 1.36])
        keys.append([1.42973, 1.04623])

        names.append("RShoulderRoll")
        times.append([0.8, 1.36])
        keys.append([-0.25622, 0.113474])

        names.append("RWristYaw")
        times.append([0.8, 1.36])
        keys.append([0.032172, -0.12583])
        self.updateWithBlink(names, keys, times, self.eyeColor['sad'], self.eyeShape['sad'])
        #self.updateWithBlink(names, keys, times, 0x00600088, "EyeBottom")

    def scaredEmotion1(self):
        names = list()
        times = list()
        keys = list()

        names.append("HeadPitch")
        times.append([0.8, 2.36])
        keys.append([-0.0537319, -0.498592])

        names.append("HeadYaw")
        times.append([0.8, 2.36])
        keys.append([0.0183661, -0.852946])

        names.append("LAnklePitch")
        times.append([0.8, 2.36])
        keys.append([-0.34826, 0.208583])

        names.append("LAnkleRoll")
        times.append([0.8, 2.36])
        keys.append([-0.00609397, -0.0873961])

        names.append("LElbowRoll")
        times.append([0.8, 2.36])
        keys.append([-0.989389, -1.46186])

        names.append("LElbowYaw")
        times.append([0.8, 2.36])
        keys.append([-1.3699, -0.895898])

        names.append("LHand")
        times.append([0.8, 2.36])
        keys.append([0.262, 0.9908])

        names.append("LHipPitch")
        times.append([0.8, 2.36])
        keys.append([-0.440216, -0.15796])

        names.append("LHipRoll")
        times.append([0.8, 2.36])
        keys.append([0.00157595, 0.113558])

        names.append("LHipYawPitch")
        times.append([0.8, 2.36])
        keys.append([0.00464392, -0.527655])

        names.append("LKneePitch")
        times.append([0.8, 2.36])
        keys.append([0.707132, 0.36505])

        names.append("LShoulderPitch")
        times.append([0.8, 2.36])
        keys.append([1.45419, 0.343573])

        names.append("LShoulderRoll")
        times.append([0.8, 2.36])
        keys.append([0.299088, -0.259288])

        names.append("LWristYaw")
        times.append([0.8, 2.36])
        keys.append([0.0137641, 1.26091])

        names.append("RAnklePitch")
        times.append([0.8, 2.36])
        keys.append([-0.352778, -0.542995])

        names.append("RAnkleRoll")
        times.append([0.8, 2.36])
        keys.append([0.00771189, 0.165714])

        names.append("RElbowRoll")
        times.append([0.8, 2.36])
        keys.append([0.981802, 1.33769])

        names.append("RElbowYaw")
        times.append([0.8, 2.36])
        keys.append([1.36829, 1.37135])

        names.append("RHand")
        times.append([0.8, 2.36])
        keys.append([0.2644, 0.9912])

        names.append("RHipPitch")
        times.append([0.8, 2.36])
        keys.append([-0.449504, 0.078192])

        names.append("RHipRoll")
        times.append([0.8, 2.36])
        keys.append([-0.00609397, -0.283749])

        names.append("RHipYawPitch")
        times.append([0.8, 2.36])
        keys.append([0.00464392, -0.527655])

        names.append("RKneePitch")
        times.append([0.8, 2.36])
        keys.append([0.70108, 0.859083])

        names.append("RShoulderPitch")
        times.append([0.8, 2.36])
        keys.append([1.45581, 0.33292])

        names.append("RShoulderRoll")
        times.append([0.8, 2.36])
        keys.append([-0.276162, 0.0628521])

        names.append("RWristYaw")
        times.append([0.8, 2.36])
        keys.append([0.0168321, -1.21037])
        if self.bScared == False:
            self.updateWithBlink(names, keys, times, self.eyeColor['scared1'], self.eyeShape['scared1'])
            self.bScared = True

        #self.updateWithBlink(names, keys, times, 0x00000060,"EyeNone")

    def scaredEmotion2(self):
        names = list()
        times = list()
        keys = list()

        names.append("HeadPitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.00310993, -0.019984, -0.019984, -0.270025, -0.0153821])

        names.append("HeadYaw")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.00617791, 0.0106959, -0.00157595, -0.495523, -0.605971])

        names.append("LAnklePitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.343659, -0.276162, -0.131966, 0.245399, 0.383458])

        names.append("LAnkleRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.00464392, 0.185656, 0.230143, 0.176453, 0.0951499])

        names.append("LElbowRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.981718, -0.992455, -0.981718, -0.774628, -1.50174])

        names.append("LElbowYaw")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-1.37144, -1.36837, -1.36837, -1.13827, -1.14287])

        names.append("LHand")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.2572, 0.246, 0.246, 0.264, 0.9864])

        names.append("LHipPitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.450955, -0.444818, -0.616627, -0.791502, -0.521518])

        names.append("LHipRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.00464392, -0.141086, -0.199378, -0.15796, -0.13495])

        names.append("LHipYawPitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.00157595, 0.0153821, -0.0735901, -0.164096, -0.162562])

        names.append("LKneePitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.696393, 0.651908, 0.659577, 0.438682, 0.440216])

        names.append("LShoulderPitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([1.41737, 1.4097, 1.42198, 1.03541, 0.622761])

        names.append("LShoulderRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.27301, 0.277612, 0.266875, -0.0828778, -0.176453])

        names.append("LWristYaw")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.0152981, 0.0137641, 0.0137641, 0.061318, 1.80701])

        names.append("RAnklePitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.36505, -0.406468, -0.619695, -0.538392, -0.998592])

        names.append("RAnkleRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.00609397, 0.162646, 0.142704, 0.22554, -0.06592])

        names.append("RElbowRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.977199, 0.975665, 0.963394, 0.928112, 1.48035])

        names.append("RElbowYaw")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([1.38209, 1.36982, 1.36829, 1.48487, 1.23023])

        names.append("RHand")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.2476, 0.2332, 0.2464, 0.2488, 0.98])

        names.append("RHipPitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.461776, -0.276162, -0.04913, 0.328234, 0.248467])

        names.append("RHipRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.00617791, -0.124212, -0.15029, -0.196309, -0.032172])

        names.append("RHipYawPitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.00157595, 0.0153821, -0.0735901, -0.164096, -0.162562])

        names.append("RKneePitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.702614, 0.567621, 0.573758, 0.075208, 1.01862])

        names.append("RShoulderPitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([1.41286, 1.40212, 1.42513, 1.01555, 0.423426])

        names.append("RShoulderRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.27923, -0.259288, -0.248551, 0.0689882, 0.231591])

        names.append("RWristYaw")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.0138481, -0.0138481, 0.0429101, -0.0107799, -1.56012])

        self.updateWithBlink(names, keys, times, self.eyeColor['scared2'], self.eyeShape['scared2'])



        #self.updateWithBlink(names, keys, times, 0x00000060, "EyeNone")

    def fear1Emotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False
        names.append("HeadPitch")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([-0.0123138, 0.50311, 0.421347, 0.46597, 0.449239, 0.50311])

        names.append("HeadYaw")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([0, -0.108956, -0.484786, 0.260738, -0.343659, -0.108956])

        names.append("LAnklePitch")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([-0.354396, -0.744032, -0.744032, -0.744032, -0.744032, -0.744032])

        names.append("LAnkleRoll")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([-0.00455999, -0.12728, -0.12728, -0.12728, -0.12728, -0.12728])

        names.append("LElbowRoll")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([-0.984786, -1.50021, -1.48947, -1.48947, -1.48947, -1.50021])

        names.append("LElbowYaw")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([-1.37144, -1.2932, -1.2932, -1.2932, -1.2932, -1.2932])

        names.append("LHand")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([0.2592, 0.2592, 0.2592, 0.2592, 0.2592, 0.2592])

        names.append("LHipPitch")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([-0.443284, -1.3192, -1.3192, -1.3192, -1.3192, -1.3192])

        names.append("LHipRoll")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([4.19617e-05, 0.0353239, 0.0353239, 0.0353239, 0.0353239, 0.0353239])

        names.append("LHipYawPitch")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([-0.00762796, 0.00924586, 0.00924586, 0.00924586, 0.00924586, 0.00924586])

        names.append("LKneePitch")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([0.710201, 1.83769, 1.83769, 1.83769, 1.83769, 1.83769])

        names.append("LShoulderPitch")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([1.44345, 0.243864, 0.243864, 0.243864, 0.243864, 0.243864])

        names.append("LShoulderRoll")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([0.262272, -0.277696, -0.277696, -0.277696, -0.277696, -0.277696])

        names.append("LWristYaw")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([0.0183661, -0.47865, -0.47865, -0.47865, -0.47865, -0.47865])

        names.append("RAnklePitch")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([-0.34971, -0.892746, -0.892746, -0.892746, -0.892746, -0.892746])

        names.append("RAnkleRoll")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([0.00310993, 0.00310993, 0.00310993, 0.00310993, 0.00310993, 0.00310993])

        names.append("RElbowRoll")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([0.977199, 1.45581, 1.45581, 1.45581, 1.45581, 1.45581])

        names.append("RElbowYaw")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([1.36982, 1.11978, 1.13052, 1.13052, 1.14586, 1.11978])

        names.append("RHand")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([0.2692, 0.2692, 0.2692, 0.2692, 0.2692, 0.2692])

        names.append("RHipPitch")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([-0.451038, -1.35456, -1.35456, -1.35456, -1.35456, -1.35456])

        names.append("RHipRoll")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([-0.00762796, -0.128814, -0.128814, -0.128814, -0.128814, -0.128814])

        names.append("RHipYawPitch")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([-0.00762796, 0.00924586, 0.00924586, 0.00924586, 0.00924586, 0.00924586])

        names.append("RKneePitch")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([0.704148, 1.95896, 1.95896, 1.95896, 1.95896, 1.95896])

        names.append("RShoulderPitch")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([1.4328, 0.124296, 0.124296, 0.124296, 0.124296, 0.124296])

        names.append("RShoulderRoll")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([-0.25622, 0.208583, 0.208583, 0.208583, 0.197844, 0.208583])

        names.append("RWristYaw")
        times.append([0.8, 2.2, 2.48, 2.72, 2.96, 3.2])
        keys.append([0.0413762, 0.697927, 0.697927, 0.697927, 0.697927, 0.697927])
        self.updateWithBlink(names, keys, times, self.eyeColor['fear'], self.eyeShape['fear'])
        #self.updateWithBlink(names, keys, times, 0x00000060,"EyeTopBottom")

    def fear2Emotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False
        # Choregraphe simplified export in Python.

        names.append("HeadPitch")
        times.append([0.8, 1.28, 1.76, 2.28, 2.8, 3.32])
        keys.append([0.00302601, 0.260738, 0.260738, 0.260738, 0.260738, 0.00302602])

        names.append("HeadYaw")
        times.append([0.8, 1.28, 1.76, 2.28, 2.8, 3.32])
        keys.append([-0.0107799, -0.372804, 0.363516, -0.372804, 0.363515, -0.0107799])

        names.append("LAnklePitch")
        times.append([0.8, 3.32])
        keys.append([-0.351328, -0.351328])

        names.append("LAnkleRoll")
        times.append([0.8, 3.32])
        keys.append([-0.00916195, -0.00916195])

        names.append("LElbowRoll")
        times.append([0.8, 3.32])
        keys.append([-0.98632, -0.98632])

        names.append("LElbowYaw")
        times.append([0.8, 3.32])
        keys.append([-1.37297, -1.37297])

        names.append("LHand")
        times.append([0.8, 3.32])
        keys.append([0.2616, 0.2616])

        names.append("LHipPitch")
        times.append([0.8, 3.32])
        keys.append([-0.450954, -0.450955])

        names.append("LHipRoll")
        times.append([0.8, 3.32])
        keys.append([0.016916, 0.016916])

        names.append("LHipYawPitch")
        times.append([0.8, 3.32])
        keys.append([-0.00455999, -0.00455999])

        names.append("LKneePitch")
        times.append([0.8, 3.32])
        keys.append([0.705598, 0.705598])

        names.append("LShoulderPitch")
        times.append([0.8, 3.32])
        keys.append([1.42658, 1.42658])

        names.append("LShoulderRoll")
        times.append([0.8, 3.32])
        keys.append([0.269942, 0.269941])

        names.append("LWristYaw")
        times.append([0.8, 3.32])
        keys.append([0.0168321, 0.0168321])

        names.append("RAnklePitch")
        times.append([0.8, 3.32])
        keys.append([-0.361982, -0.361981])

        names.append("RAnkleRoll")
        times.append([0.8, 3.32])
        keys.append([0.00771189, 0.00771189])

        names.append("RElbowRoll")
        times.append([0.8, 3.32])
        keys.append([0.963394, 0.963394])

        names.append("RElbowYaw")
        times.append([0.8, 3.32])
        keys.append([1.37289, 1.37289])

        names.append("RHand")
        times.append([0.8, 3.32])
        keys.append([0.2648, 0.2648])

        names.append("RHipPitch")
        times.append([0.8, 3.32])
        keys.append([-0.458708, -0.458707])

        names.append("RHipRoll")
        times.append([0.8, 3.32])
        keys.append([-0.029104, -0.0291041])

        names.append("RHipYawPitch")
        times.append([0.8, 3.32])
        keys.append([-0.00455999, -0.00455999])

        names.append("RKneePitch")
        times.append([0.8, 3.32])
        keys.append([0.70108, 0.70108])

        names.append("RShoulderPitch")
        times.append([0.8, 3.32])
        keys.append([1.42666, 1.42666])

        names.append("RShoulderRoll")
        times.append([0.8, 3.32])
        keys.append([-0.262356, -0.262356])

        names.append("RWristYaw")
        times.append([0.8, 3.32])
        keys.append([0.0383081, 0.0383082])

        self.updateWithBlink(names, keys, times, self.eyeColor['fear'], self.eyeShape['fear'])


    def hope1Emotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False
        names.append("HeadPitch")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([0.00762796, -0.158044, -0.6704, -0.667332, -0.6704, -0.667332, -0.6704])

        names.append("HeadYaw")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([-0.00464392, -0.00464392, -0.019984, -0.01845, -0.019984, -0.01845, -0.019984])

        names.append("LAnklePitch")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([-0.357464, 0.0827939, 0.0873961, 0.0873961, 0.0873961, 0.0873961, 0.0873961])

        names.append("LAnkleRoll")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([-0.00762796, -0.121144, -0.110406, -0.118076, -0.110406, -0.118076, -0.110406])

        names.append("LElbowRoll")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([-0.974047, -0.776162, -1.49714, -1.21489, -1.49714, -1.21489, -1.49714])

        names.append("LElbowYaw")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([-1.37144, -1.17509, -0.823801, -0.86215, -0.823801, -0.862151, -0.823801])

        names.append("LHand")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([0.2684, 0.2904, 0.9692, 0.9712, 0.9692, 0.9712, 0.9692])

        names.append("LHipPitch")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([-0.449421, 0.127364, 0.122762, 0.116626, 0.122762, 0.116626, 0.122762])

        names.append("LHipRoll")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([0.00464392, 0.092082, 0.093616, 0.0997519, 0.093616, 0.099752, 0.093616])

        names.append("LHipYawPitch")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([-0.00762796, -0.170232, -0.167164, -0.162562, -0.167164, -0.162562, -0.167164])

        names.append("LKneePitch")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([0.700996, -0.090548, -0.0923279, -0.0923279, -0.0923279, -0.0923279, -0.0923279])

        names.append("LShoulderPitch")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([1.44345, 1.01547, 0.671851, 0.857464, 0.671851, 0.857465, 0.671851])

        names.append("LShoulderRoll")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([0.262272, -0.181053, 0.0674542, -0.0307219, 0.0674542, -0.030722, 0.0674542])

        names.append("LWristYaw")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([0.0183661, -0.0107799, 0.236194, -0.023052, 0.236194, -0.023052, 0.236194])

        names.append("RAnklePitch")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([-0.358915, 0.0874801, 0.092082, 0.090548, 0.092082, 0.090548, 0.092082])

        names.append("RAnkleRoll")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([0.00464392, 0.130432, 0.127364, 0.135034, 0.127364, 0.135034, 0.127364])

        names.append("RElbowRoll")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([0.975665, 1.08458, 1.43433, 1.24105, 1.43433, 1.24105, 1.43433])

        names.append("RElbowYaw")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([1.36675, 1.26397, 0.897349, 0.9403, 0.897349, 0.9403, 0.897349])

        names.append("RHand")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([0.2696, 0.2852, 0.952, 0.9548, 0.952, 0.9548, 0.952])

        names.append("RHipPitch")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([-0.455641, 0.130348, 0.121144, 0.121144, 0.121144, 0.121144, 0.121144])

        names.append("RHipRoll")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([-0.00762796, -0.091998, -0.107338, -0.10427, -0.107338, -0.10427, -0.107338])

        names.append("RHipYawPitch")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([-0.00762796, -0.170232, -0.167164, -0.162562, -0.167164, -0.162562, -0.167164])

        names.append("RKneePitch")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([0.702614, -0.0843279, -0.0858622, -0.0923279, -0.0858622, -0.0923279, -0.0858622])

        names.append("RShoulderPitch")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([1.43587, 1.26099, 0.673468, 0.921976, 0.673468, 0.921975, 0.673468])

        names.append("RShoulderRoll")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([-0.257754, 0.032172, 0.115008, 0.0352399, 0.115008, 0.0352399, 0.115008])

        names.append("RWristYaw")
        times.append([0.8, 1.6, 2, 2.2, 2.4, 2.6, 2.8])
        keys.append([0.033706, 0.621227, -0.145772, -0.121228, -0.145772, -0.121228, -0.145772])
        self.updateWithBlink(names, keys, times, self.eyeColor['hope'], self.eyeShape['hope'])
        #self.updateWithBlink(names, keys, times, 0x00FFB428, "EyeTop")

    def hope2Emotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False
        # Choregraphe simplified export in Python.

        names.append("HeadPitch")
        times.append([1, 1.6, 2.2, 2.8, 3.36, 3.92])
        keys.append([-0.00310993, 0.177901, -0.222472, 0.177901, -0.222472, -0.00310993])

        names.append("HeadYaw")
        times.append([1, 1.6, 2.2, 2.8, 3.36, 3.92])
        keys.append([0.00455999, -0.023052, -0.0337899, -0.023052, -0.0337899, 0.00455999])

        names.append("LAnklePitch")
        times.append([1, 3.92])
        keys.append([-0.352862, -0.352862])

        names.append("LAnkleRoll")
        times.append([1, 3.92])
        keys.append([-0.00609397, -0.00609397])

        names.append("LElbowRoll")
        times.append([1, 3.92])
        keys.append([-0.983252, -0.983252])

        names.append("LElbowYaw")
        times.append([1, 3.92])
        keys.append([-1.3699, -1.3699])

        names.append("LHand")
        times.append([1, 3.92])
        keys.append([0.2596, 0.2596])

        names.append("LHipPitch")
        times.append([1, 3.92])
        keys.append([-0.450955, -0.450955])

        names.append("LHipRoll")
        times.append([1, 3.92])
        keys.append([0.019984, 0.019984])

        names.append("LHipYawPitch")
        times.append([1, 3.92])
        keys.append([-0.00149202, -0.00149202])

        names.append("LKneePitch")
        times.append([1, 3.92])
        keys.append([0.713267, 0.713267])

        names.append("LShoulderPitch")
        times.append([1, 3.92])
        keys.append([1.43118, 1.43118])

        names.append("LShoulderRoll")
        times.append([1, 3.92])
        keys.append([0.271475, 0.271475])

        names.append("LWristYaw")
        times.append([1, 3.92])
        keys.append([0.0168321, 0.0168321])

        names.append("RAnklePitch")
        times.append([1, 3.92])
        keys.append([-0.361981, -0.361981])

        names.append("RAnkleRoll")
        times.append([1, 3.92])
        keys.append([0.00310993, 0.00310993])

        names.append("RElbowRoll")
        times.append([1, 3.92])
        keys.append([0.96953, 0.96953])

        names.append("RElbowYaw")
        times.append([1, 3.92])
        keys.append([1.36829, 1.36829])

        names.append("RHand")
        times.append([1, 3.92])
        keys.append([0.2608, 0.2608])

        names.append("RHipPitch")
        times.append([1, 3.92])
        keys.append([-0.44797, -0.44797])

        names.append("RHipRoll")
        times.append([1, 3.92])
        keys.append([-0.032172, -0.032172])

        names.append("RHipYawPitch")
        times.append([1, 3.92])
        keys.append([-0.00149202, -0.00149202])

        names.append("RKneePitch")
        times.append([1, 3.92])
        keys.append([0.699545, 0.699545])

        names.append("RShoulderPitch")
        times.append([1, 3.92])
        keys.append([1.4282, 1.4282])

        names.append("RShoulderRoll")
        times.append([1, 3.92])
        keys.append([-0.260822, -0.260822])

        names.append("RWristYaw")
        times.append([1, 3.92])
        keys.append([0.032172, 0.032172])
        self.updateWithBlink(names, keys, times, self.eyeColor['hope'], self.eyeShape['hope'])

    def angerEmotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False
        names.append("HeadPitch")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([-0.0153821, -0.073674, -0.046062, -0.046062, -0.046062, -0.046062])

        names.append("HeadYaw")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([0.00302602, -0.00617791, -0.395814, 0.283749, -0.563021, -0.10282])

        names.append("LAnklePitch")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([-0.35593, -0.563021, -0.556884, -0.556884, -0.556884, -0.556884])

        names.append("LAnkleRoll")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([-0.0106959, -0.00455999, -0.00455999, -0.00455999, -0.00455999, -0.00455999])

        names.append("LElbowRoll")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([-0.977116, -1.46953, -1.44499, -1.44499, -1.44499, -1.44499])

        names.append("LElbowYaw")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([-1.37297, -0.227074, -0.260822, -0.260822, -0.260822, -0.260822])

        names.append("LHand")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([0.2608, 0.25, 0.25, 0.25, 0.25, 0.25])

        names.append("LHipPitch")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([-0.452487, -0.691793, -0.682588, -0.682588, -0.682588, -0.682588])

        names.append("LHipRoll")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([0.00464392, 0.00464392, 0.00464392, 0.00464392, 0.00464392, 0.00464392])

        names.append("LHipYawPitch")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([-0.00916195, -0.00455999, -0.00455999, -0.00455999, -0.00455999, -0.00455999])

        names.append("LKneePitch")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([0.705598, 1.11364, 1.11211, 1.11211, 1.11211, 1.11211])

        names.append("LShoulderPitch")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([1.44345, 1.33607, 1.32533, 1.32533, 1.32533, 1.32533])

        names.append("LShoulderRoll")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([0.268407, 0.74088, 0.734743, 0.734743, 0.734743, 0.734743])

        names.append("LWristYaw")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([0.0152981, 0.06592, 0.05058, 0.05058, 0.05058, 0.05058])

        names.append("RAnklePitch")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([-0.361981, -0.592082, -0.582879, -0.593616, -0.593616, -0.593616])

        names.append("RAnkleRoll")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([0.00157595, 0.00771189, 0.00771189, 0.00771189, 0.00771189, 0.00771189])

        names.append("RElbowRoll")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([0.971065, 1.42513, 1.39138, 1.39138, 1.39138, 1.39138])

        names.append("RElbowYaw")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([1.36982, -0.14117, -0.121228, -0.121228, -0.121228, -0.121228])

        names.append("RHand")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([0.2624, 0.2556, 0.2556, 0.2556, 0.2556, 0.2556])

        names.append("RHipPitch")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([-0.449504, -0.68574, -0.679603, -0.679603, -0.679603, -0.679603])

        names.append("RHipRoll")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([-0.00455999, -0.0122299, -0.0122299, -0.0122299, -0.0122299, -0.0122299])

        names.append("RHipYawPitch")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([-0.00916195, -0.00455999, -0.00455999, -0.00455999, -0.00455999, -0.00455999])

        names.append("RKneePitch")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([0.691876, 1.12446, 1.12446, 1.12446, 1.12446, 1.12446])

        names.append("RShoulderPitch")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([1.4328, 1.06771, 1.05083, 1.05083, 1.05083, 1.05083])

        names.append("RShoulderRoll")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([-0.260822, -0.713353, -0.693411, -0.693411, -0.693411, -0.693411])

        names.append("RWristYaw")
        times.append([0.8, 2.12, 2.36, 2.56, 2.76, 2.96])
        keys.append([0.030638, -4.19617e-05, 0.0106959, 0.0106959, 0.0106959, 0.0106959])
        self.updateWithBlink(names, keys, times, self.eyeColor['anger'], self.eyeShape['anger'])
        #self.updateWithBlink(names, keys, times, 0x00FF0000, "EyeTopBottom")


    def createDialog(self):
        self.HriDialogEOD={ '1'         : "Hello again Bob, how was the rest of your day?",
                            '1good'     : "Awesome, I knew it would be a good day",
                            '1bad'      : "Oh, I am sorry to hear that. There is always tomorrow to look forward to.",
                            '2'         : "Do! you! have! any! big! plans! you! are! looking! forward! to! later! during! the! week! or! over! the! weekend?",
                            '2yes'      : "That's great, that sounds like fun.",
                            '2no'       : "It. would. be. greate. if. you. could. plan. something. active.",
                            '31'        : "Did you have the meal suggested for breakfast this morning?",
                            '31yes'     : "That's great, break fast is the most important meal of the day. Having a healthy breakfast in the morning can help you to fight viruses and reduce your risk of disease. Do you think you could have this regularly for breakfast?",
                            '31yesyes'  : "Wonderful, I will suggest this again to you. A consistent healthy breakfast can improve your energy levels and reduce hunger throughout the day.",
                            '31no'      : "Did you at lest least have any breakfast this morning?",
                            '31noyes'   : "That's good at least, but I would recommend you have the suggested meal whenever possible. That way you can ensure you are always getting a healthy start to your day.",
                            '31nono'    : "Breakfast is the most important meal of the day. Skipping breakfast often leads to unhealthy habits and overeating later in the day. Please try to have at least something for breakfast in the future, and even better if you have something like the suggested meal"
                            }

    def EdgeDistance2D(self, x1, y1, x2, y2, centerX, centerY):
        a=y1-y2
        b=x2-x1
        c=y2*(x1-x2)-x2*(y1-y2)
        return (abs(a*centerX+b*centerY+c)/math.sqrt(a*a+b*b))

    def EdgeDistance3D(self, dist2d,maxX,maxY):
        height = 45.19+102.9+100+85+165.5+17.74
        viewAngle=np.radians(90-39.7)
        hfov=np.radians(60.9)
        vfov=np.radians(47.6)
        distFeetToCenter=292.1
        dist3d=distFeetToCenter/(maxY/2)*dist2d
        return dist3d

    def ShortestIntersection(self, x1,y1,x2,y2, centerX, centerY):
        a=y1-y2
        b=x2-x1
        c=y2*(x1-x2)-x2*(y1-y2)
        m=a*centerY-b*centerX
        den=a*a+b*b
        x=(-b*m-c*a)/den
        y=(a*m-b*c)/den
        return x,y

    def RhoThetaToBoundary(self, rho, theta, maxX, maxY):
        xTop = -1
        yLeft = -1
        xBottom = -1
        yRight = -1
        if math.sin(theta)<0.001:
            if rho>0:
                yLeft = rho
                yRight = rho
            elif rho<0:
                print "Error 07: Unexpected Line! Press any key to continue"
                cv2.waitKey(0)
        elif theta<(np.pi/2):
            if rho>0:
                yLeft=rho/math.sin(theta)
                if yLeft <= maxY:
                    xBottom = -1
                else:
                    xBottom= (yLeft-maxY)*math.tan(theta)
                    yLeft = -1
                xTop = rho/math.cos(theta)
                if xTop < maxX:
                    yRight = -1
                else:
                    yRight = (xTop-maxX)/math.tan(theta)
                    xTop = -1
            elif rho < 0:
                    print "Error 01: Unexpected Line! Press any key to continue"
                    cv2.waitKey(0)
            else:
                    print "Error 02: Impossible case. Not implemented!"
                    cv2.waitKey(0)
        elif theta>(np.pi/2) and theta<(np.pi):
            if rho>0:
                yLeft=rho/math.cos(theta-np.pi/2)
                if yLeft > maxY:
                    yLeft = -1
                    print "Error 03: Unexpected Line! Press any key to continue"
                    cv2.waitKey(0)
                else:
                    xBottom = (maxY - yLeft)/math.tan(theta-np.pi/2)
                    if xBottom > maxX:
                        yRight = maxY - (xBottom-maxX)*math.tan(theta-np.pi/2)
                        xBottom= - 1
            elif rho < 0:
                xTop = -rho/math.sin(theta-np.pi/2)
                if xTop > maxX:
                    print "Error 04: Unexpected Line! Press any key to continue"
                    cv2.waitKey(0)
                else:
                    yRight=(maxX-xTop)*math.tan(theta-np.pi/2)
                    if yRight > maxY:
                        xBottom=maxX - (yRight-maxY)/math.tan(theta-np.pi/2)
                        yRight=-1
        elif theta>np.pi:
            print "Error 05: Unexpected Angle! Press any key to continue"
            cv2.waitKey(0)
        if xTop>maxX or xBottom > maxX or yLeft> maxY or yRight> maxY:
            print "Error 06: Out of Range! Press any key to continue"
            print rho,theta
            print xTop, yLeft, xBottom, yRight
            cv2.waitKey(0)
        return xTop,yLeft,xBottom,yRight

    def RhoThetaX1Y1X2Y2(self, rho,theta):
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        x1 = int(x0 + 1000*(-b))
        y1 = int(y0 + 1000*(a))
        x2 = int(x0 - 1000*(-b))
        y2 = int(y0 - 1000*(a))
        return x1,y1,x2,y2

    def dotProduct(self,x1,y1,x2,y2,X1,Y1,X2,Y2):
        return (x2-x1)*(X2-X1)+(y2-y1)*(Y2-Y1)

    def measureDistance(self, resX, resY, originalFrame):
        maxX = resX #320
        maxY = resY #240
        seedX = resX/2
        seedY = resY*7/8
        centerX = resX/2
        centerY = resY

        kernel = np.ones((5,5),np.uint8)
        blur_bgr = cv2.bilateralFilter(originalFrame, 9, 75, 75)
        cv2.circle(originalFrame, (seedX, seedY), 5, (0, 0, 0xFF), -1)
        edge_bgr = cv2.Canny(blur_bgr, 10, 220, True)
        closing = cv2.morphologyEx(edge_bgr, cv2.MORPH_CLOSE, kernel)
        replicate_bgr = cv2.copyMakeBorder(closing,1,1,1,1,cv2.BORDER_REPLICATE)
        cv2.floodFill(blur_bgr,replicate_bgr,(seedX,seedY),(0,0xFF,0), (5,10,10), (5,10,10), 8 | ( 125 << 8 ) | cv2.FLOODFILL_MASK_ONLY )
        FloodFill = cv2.inRange(replicate_bgr,125,125)
        TableRegion = cv2.dilate(FloodFill,kernel,iterations=1)
        TableEdges = cv2.Canny(TableRegion, 1, 255, apertureSize=5)
        houghImage = np.zeros((maxY, maxX, 3), np.uint8)
        lines = cv2.HoughLines(TableEdges,1,np.pi/180,self.voteHoughLines)
        numberOfLines = 0
        Rho1=0
        Theta1=0
        Rho2=1
        Theta2=1
        if lines is None:
            self.voteHoughLines-=1;
            if self.voteHoughLines<=0:
                self.voteHoughLines=1
        else:

            for rho,theta in lines[0]:
                x1,y1,x2,y2 = self.RhoThetaX1Y1X2Y2(rho, theta)
                cv2.line(houghImage, (x1, y1), (x2, y2), (0, 0, 0xFF), 2)

            lineArrayDimension = lines.shape
            if lineArrayDimension[1]>2:
                if lineArrayDimension[1]>4:
                    self.voteHoughLines+=1;
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 5, 1.0)
                flags = cv2.KMEANS_RANDOM_CENTERS
                compactness,labels,centers = cv2.kmeans(lines,2,criteria,10,flags)
                Diff=abs(centers[0][1]-centers[1][1])
                if Diff>np.pi/4:
                    Rho1=centers[0][0]
                    Theta1=centers[0][1]
                    Rho2=centers[1][0]
                    Theta2=centers[1][1]
                    numberOfLines=2
                else:
                    Rho1=(lines[0][0][0]+lines[0][1][0])*0.5
                    Theta1=(lines[0][0][1]+lines[0][1][1])*0.5
                    numberOfLines=1
            elif lineArrayDimension[1] == 2:
                Diff=abs(lines[0][0][1]-lines[0][1][1])
                if Diff > np.pi/4:
                    Rho1=lines[0][0][0]
                    Theta1=lines[0][0][1]
                    Rho2=lines[0][1][0]
                    Theta2=lines[0][1][1]
                    numberOfLines=2
                else:
                    Rho1=(lines[0][0][0]+lines[0][1][0])*0.5
                    Theta1=(lines[0][0][1]+lines[0][1][1])*0.5
                    numberOfLines=1
            elif lineArrayDimension[1] == 1:
                Rho1=lines[0][0][0]
                Theta1=lines[0][0][1]
                numberOfLines=1

        distance3D=-1

        if numberOfLines==1:
            xTop,yLeft,xBottom,yRight = self.RhoThetaToBoundary(Rho1, Theta1,maxX,maxY)
            x1,y1,x2,y2=self.RhoThetaX1Y1X2Y2(Rho1, Theta1)
            x,y=self.ShortestIntersection(float(x1),float(y1),float(x2),float(y2), centerX, centerY)
            distance=self.EdgeDistance2D(x1, y1, x2, y2, centerX, centerY)
            distance3D=self.EdgeDistance3D(distance,maxX,maxY)
            cv2.circle(originalFrame, (int(x), int(y)), 5, (0xFF, 0, 0), -1)
            cv2.line(originalFrame, (x1, y1), (x2, y2), (0, 0xFF, 0), 2)
            cv2.line(originalFrame, (int(x), int(y)), (int(centerX), int(centerY)), (0, 0, 0xFF), 1)
            if xTop >= 0:
                cv2.circle(originalFrame, (int(xTop), 0), 5, (0xFF, 0, 0), -1)
            if yLeft >= 0:
                cv2.circle(originalFrame, (0, int(yLeft)), 5, (0xFF, 0, 0), -1)
            if xBottom >= 0:
                cv2.circle(originalFrame, (int(xBottom), maxY), 5, (0xFF, 0, 0), -1)
            if yRight >= 0:
                cv2.circle(originalFrame, (maxX, int(yRight)), 5, (0xFF, 0, 0), -1)
        elif numberOfLines==2:
            line1Pt=[]
            line2Pt=[]

            xTop1, yLeft1, xBottom1, yRight1 = self.RhoThetaToBoundary(Rho1, Theta1, maxX, maxY)
            xTop2, yLeft2, xBottom2, yRight2 = self.RhoThetaToBoundary(Rho2, Theta2, maxX, maxY)

            if xTop1>=0:
                line1Pt.append([xTop1, 0])
            if xTop2>=0:
                line2Pt.append([xTop2, 0])
            if yLeft1 >= 0:
                line1Pt.append([0, yLeft1])
            if yLeft2 >= 0:
                line2Pt.append([0, yLeft2])
            if xBottom1 >= 0:
                line1Pt.append([xBottom1, maxY])
            if xBottom2 >= 0:
                line2Pt.append([xBottom2, maxY])
            if yRight1 >= 0:
                line1Pt.append([maxX, yRight1])
            if yRight2 >= 0:
                line2Pt.append([maxX, yRight2])

            xIntersectNum = -line2Pt[1][0]*line2Pt[0][1]*line1Pt[0][0]\
                            +line2Pt[1][0]*line2Pt[0][1]*line1Pt[1][0]\
                            +line2Pt[0][0]*line1Pt[1][0]*line1Pt[0][1]\
                            -line2Pt[1][0]*line1Pt[1][0]*line1Pt[0][1]\
                            +line2Pt[1][0]*line1Pt[1][1]*line1Pt[0][0]\
                            -line2Pt[0][0]*line2Pt[1][1]*line1Pt[1][0]\
                            +line2Pt[0][0]*line2Pt[1][1]*line1Pt[0][0]\
                            -line2Pt[0][0]*line1Pt[1][1]*line1Pt[0][0]

            Denum = -line2Pt[0][1]*line1Pt[0][0]\
                    +line2Pt[0][1]*line1Pt[1][0]\
                    +line2Pt[1][1]*line1Pt[0][0]\
                    -line2Pt[1][1]*line1Pt[1][0]\
                    +line1Pt[0][1]*line2Pt[0][0]\
                    -line1Pt[0][1]*line2Pt[1][0]\
                    -line1Pt[1][1]*line2Pt[0][0]\
                    +line1Pt[1][1]*line2Pt[1][0]

            yIntersectNum = -line1Pt[1][1]*line2Pt[1][1]*line2Pt[0][0]\
                            -line2Pt[0][1]*line1Pt[1][1]*line1Pt[0][0]\
                            +line2Pt[0][1]*line1Pt[1][0]*line1Pt[0][1]\
                            +line2Pt[1][1]*line1Pt[1][1]*line1Pt[0][0]\
                            -line2Pt[1][1]*line1Pt[1][0]*line1Pt[0][1]\
                            +line1Pt[0][1]*line2Pt[1][1]*line2Pt[0][0]\
                            -line1Pt[0][1]*line2Pt[1][0]*line2Pt[0][1]\
                            +line1Pt[1][1]*line2Pt[1][0]*line2Pt[0][1]

            xIntersect = xIntersectNum/Denum
            yIntersect = yIntersectNum/Denum
            line1Pt=[]
            line2Pt=[]
            if xIntersect < maxX and xIntersect > 0 and yIntersect < maxY and yIntersect > 0:
                if Theta1<np.pi/2:
                    if yLeft1 >= 0:
                        #print "case 1"
                        line1Pt.append([0, yLeft1])
                        cv2.line(originalFrame, (0, int(yLeft1)), (int(xIntersect), int(yIntersect)), (0, 255, 0), 2)
                        cv2.circle(originalFrame, (0, int(yLeft1)), 5, (0xFF, 0, 0), -1)
                    elif xBottom1 >= 0:
                        #print "case 2"
                        line1Pt.append([xBottom1, maxY])
                        cv2.line(originalFrame, (int(xBottom1), int(maxY)), (int(xIntersect), int(yIntersect)), (0, 255, 0), 2)
                        cv2.circle(originalFrame, (int(xBottom1), int(maxY)), 5, (0xFF, 0, 0), -1)
                elif Theta1>np.pi/2:
                    if yRight1 >= 0:
                        #print "case 3"
                        line1Pt.append([maxX, yRight1])
                        cv2.line(originalFrame, (int(maxX), int(yRight1)), (int(xIntersect), int(yIntersect)), (0, 255, 0), 2)
                        cv2.circle(originalFrame, (int(maxX), int(yRight1)), 5, (0xFF, 0, 0), -1)
                    elif xBottom1 >= 0:
                        #print "case 4"
                        line1Pt.append([xBottom1, maxY])
                        cv2.line(originalFrame, (int(xBottom1), int(maxY)), (int(xIntersect), int(yIntersect)), (0, 255, 0), 2)
                        cv2.circle(originalFrame, (int(xBottom1), int(maxY)), 5, (0xFF, 0, 0), -1)

                if Theta2<np.pi/2:
                    if yLeft2 >= 0:
                        #print "case 5"
                        line2Pt.append([0,yLeft2])
                        cv2.line(originalFrame, (0, int(yLeft2)), (int(xIntersect), int(yIntersect)), (0, 255, 0), 2)
                        cv2.circle(originalFrame, (0, int(yLeft2)), 5, (0xFF, 0, 0), -1)
                    elif xBottom2 >= 0:
                        #print "case 6"
                        line2Pt.append([xBottom2,maxY])
                        cv2.line(originalFrame, (int(xBottom2), int(maxY)), (int(xIntersect), int(yIntersect)), (0, 255, 0), 2)
                        cv2.circle(originalFrame,  (int(xBottom2), int(maxY)), 5, (0xFF, 0, 0), -1)
                elif Theta2>np.pi/2:
                    if yRight2 >= 0:
                        #print "case 7"
                        line2Pt.append([maxX,yRight2])
                        cv2.line(originalFrame, (int(maxX), int(yRight2)), (int(xIntersect), int(yIntersect)), (0, 255, 0), 2)
                        cv2.circle(originalFrame, (int(maxX), int(yRight2)), 5, (0xFF, 0, 0), -1)
                    elif xBottom2 >= 0:
                        #print "case 8"
                        line2Pt.append([xBottom2,maxY])
                        cv2.line(originalFrame, (int(xBottom2), int(maxY)), (int(xIntersect), int(yIntersect)), (0, 255, 0), 2)
                        cv2.circle(originalFrame, (int(xBottom2), int(maxY)), 5, (0xFF, 0, 0), -1)
                cv2.circle(originalFrame, (int(xIntersect), int(yIntersect)), 10, (0xFF, 0xFF, 0), -1)
                distance1=self.EdgeDistance2D(line1Pt[0][0], line1Pt[0][1], xIntersect, yIntersect, centerX, centerY)
                distance2=self.EdgeDistance2D(line2Pt[0][0], line2Pt[0][1], xIntersect, yIntersect, centerX, centerY)
                if distance1 < distance2:
                    distance3D=self.EdgeDistance3D(distance1,maxX,maxY)
                    x,y = self.ShortestIntersection(line1Pt[0][0],line1Pt[0][1],xIntersect,yIntersect, centerX, centerY)
                    cv2.circle(originalFrame, (int(x), int(y)), 5, (0xFF, 0, 0), -1)
                    cv2.line(originalFrame, (int(x), int(y)), (int(centerX), int(centerY)), (0, 0, 0xFF), 1)
                else:
                    distance3D=self.EdgeDistance3D(distance2,maxX,maxY)
                    x,y = self.ShortestIntersection(line2Pt[0][0],line2Pt[0][1],xIntersect,yIntersect, centerX, centerY)
                    cv2.circle(originalFrame, (int(x), int(y)), 5, (0xFF, 0, 0), -1)
                    cv2.line(originalFrame, (int(x), int(y)), (int(centerX), int(centerY)), (0, 0, 0xFF), 1)

        font = cv2.FONT_HERSHEY_SIMPLEX
        dist3dStr=str(int(distance3D/10))
        cv2.putText(originalFrame,"Distance:" + dist3dStr + " cm",(10,maxY-10), font, 1,(0,0xFF,0),2,cv2.CV_AA)

        return dist3dStr,replicate_bgr

    def img(self):
        self.UnsubscribeAllTouchEvent()
        motionProxy = self.connectToProxy("ALMotion")
        motionNames = ['HeadYaw', "HeadPitch"]
        times = [[0.7], [0.7]] # time to preform (s)

        motionProxy.angleInterpolation(motionNames, [0.0,0.0], times, True)
        motionProxy.angleInterpolation(motionNames, [0.0,0.2], times, True)
        self.SubscribeAllTouchEvent()

        while True:
            naoImage = self.camProxy.getImageRemote(self.cameraId)
            frame = (np.reshape(np.frombuffer(naoImage[6], dtype = '%iuint8' % naoImage[2]), (naoImage[1], naoImage[0], naoImage[2])))
            #print "Image resolution is",naoImage[0], naoImage[1]
            dist,debugFrame = self.measureDistance(naoImage[0],naoImage[1],frame)
            self.camProxy.releaseImage(self.cameraId)
            cv2.imshow('Original', frame)
            cv2.imshow('Debug', debugFrame)
            k = cv2.waitKey(1)
            if k == 27:
                break
        cv2.destroyAllWindows()

    '''
    def checkEdgeDist(self):

        # set nao position
        # get edge stuff
        return distINcm

    '''