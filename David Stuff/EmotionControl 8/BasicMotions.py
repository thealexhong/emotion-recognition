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
                       'scared':   0x009F2F00,
                       'worried':      0x00600088,
                       'interested':      0x00FFB428,
                       'anger':     0x00FF0000}
        self.eyeShape={'happy': "EyeTop",
                       'sad': "EyeBottom",
                       'scared': "EyeTopBottom",
                       'worried': "EyeBottom",
                       'interested': "EyeTop",
                       'anger': "EyeTopBottom"}
        self.bScared = False
        #=========SETUP FOR VOICE================
        self.tts = ALProxy("ALTextToSpeech")
        try:
            audioProxy = ALProxy("ALAudioDevice")
            audioProxy.setOutputVolume(70)
        except:
            pass
        #Valid Value:50 to 200
        self.ttsPitch={      'default':   "\\vct=100\\",
                             'happy':     "\\vct=120\\",
                             'sad':       "\\vct=50\\",
                             'scared':    "\\vct=150\\",
                             'worried':      "\\vct=65\\",
                             'interested':      "\\vct=100\\",
                             'anger':     "\\vct=55\\"}
        #Valid Value: 50 to 400"\\
        self.ttsSpeed={      'default':   "\\rspd=100\\",
                             'happy':     "\\rspd=100\\",
                             'sad':       "\\rspd=70\\",
                             'scared':    "\\rspd=130\\",
                             'worried':      "\\rspd=75\\",
                             'interested':      "\\rspd=100\\",
                             'anger':     "\\rspd=110\\"}
        #Valid Value: 0 to 100
        self.ttsVolume={     'default':   "\\vol=050\\",
                             'happy':     "\\vol=060\\",
                             'sad':       "\\vol=035\\",
                             'scared':    "\\vol=070\\",
                             'worried':      "\\vol=050\\",
                             'interested':      "\\vol=050\\",
                             'anger':     "\\vol=060\\"}
        #============SETUP FOR PICKUP DETECTION====================
        self.SubscribePickUpEvent()
        #============SETUP FOR VIDEO====================
        '''
        self.camProxy = ALProxy("ALVideoDevice", self.NAOip, self.NAOport)
        self.resolution = vision_definitions.kQVGA
        self.colorSpace = vision_definitions.kBGRColorSpace
        self.fps = 10
        self.cameraId = self.camProxy.subscribe("python_GVM", self.resolution, self.colorSpace, self.fps)
        print "The camera ID is", self.cameraId
        self.camProxy.setActiveCamera(self.cameraId, vision_definitions.kBottomCamera)
        self.voteHoughLines=40
        '''
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

    def naoStandInit(self):
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

    def naoStand(self):
        self.UnsubscribeAllTouchEvent()
        motionProxy = self.connectToProxy("ALMotion")
        postureProxy = self.connectToProxy("ALRobotPosture")

        motionProxy.wakeUp()
        self.StiffnessOn(motionProxy)
        standResult = postureProxy.goToPosture("Stand", 0.3)
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


    def getJointAngle(self,jointName,useSensor):
        motionProxy = self.connectToProxy("ALMotion")
        return motionProxy.getAngles(jointName,useSensor)


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

    def naoSayWorried(self,str):
        emotion = 'worried'
        sentence= self.ttsPitch[emotion]+  self.ttsVolume[emotion] +  self.ttsSpeed[emotion]
        sentence+=str
        self.tts.post.say(sentence)

    def naoSayInterested(self,str):
        emotion = 'interested'
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
        #self.camProxy.unsubscribe(self.cameraId)
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

    def blinkAlarmingEyes(self, duration, color, configuration):
        bAnimation= True;
        accu=0;
        rgbList=[]
        timeList=[]
        #Reset eye color to black
        self.setEyeColor(0x00000000,"LedEye")
        while(accu<duration):
            newTimeList=[0.01,0.75,0.01]
            accu+=(newTimeList[1])
            rgbList.extend([0x002F1F00,color,0x00000000])
            timeList.extend(newTimeList)
        try:
            ledProxy = self.connectToProxy("ALLeds")
            ledProxy.post.fadeListRGB("LedEye", rgbList, timeList)
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


    def updateWithBlink(self, names, keys, times, color, configuration,bStand=None,bDisableEye=None,bDisableInit=None):
        self.UnsubscribeAllTouchEvent()  #Already called in OnTouched
        postureProxy = self.connectToProxy("ALRobotPosture")
        if bDisableInit is None:
            if bStand is None:
                standResult = postureProxy.goToPosture("StandInit", 0.3)
            elif bStand==True:
                standResult = postureProxy.goToPosture("Stand", 0.3)
        else:
            standResult=True
        if (standResult):
            print("------> Stood Up")
            try:
                # uncomment the following line and modify the IP if you use this script outside Choregraphe.
                print("Time duration is ")
                print(max(max(times)))
                if bDisableEye is None:
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

    def LookAtEdgeEmotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False
        names.append("HeadPitch")
        times.append([1, 1.88])
        keys.append([-0.145772, 0.248466])

        names.append("HeadYaw")
        times.append([1, 1.88])
        keys.append([0.0106959, -0.00771189])

        names.append("LAnklePitch")
        times.append([1, 1.88])
        keys.append([0.0873961, 0.0873961])

        names.append("LAnkleRoll")
        times.append([1, 1.88])
        keys.append([-0.13495, -0.13495])

        names.append("LElbowRoll")
        times.append([1, 1.88])
        keys.append([-0.404934, -0.404934])

        names.append("LElbowYaw")
        times.append([1, 1.88])
        keys.append([-1.17509, -1.17509])

        names.append("LHand")
        times.append([1, 1.88])
        keys.append([0.29, 0.29])

        names.append("LHipPitch")
        times.append([1, 1.88])
        keys.append([0.12583, 0.12583])

        names.append("LHipRoll")
        times.append([1, 1.88])
        keys.append([0.105888, 0.105888])

        names.append("LHipYawPitch")
        times.append([1, 1.88])
        keys.append([-0.16563, -0.16563])

        names.append("LKneePitch")
        times.append([1, 1.88])
        keys.append([-0.090548, -0.090548])

        names.append("LShoulderPitch")
        times.append([1, 1.88])
        keys.append([1.48027, 1.48027])

        names.append("LShoulderRoll")
        times.append([1, 1.88])
        keys.append([0.16563, 0.16563])

        names.append("LWristYaw")
        times.append([1, 1.88])
        keys.append([0.08126, 0.08126])

        names.append("RAnklePitch")
        times.append([1, 1.88])
        keys.append([0.09515, 0.09515])

        names.append("RAnkleRoll")
        times.append([1, 1.88])
        keys.append([0.135034, 0.135034])

        names.append("RElbowRoll")
        times.append([1, 1.88])
        keys.append([0.431096, 0.431096])

        names.append("RElbowYaw")
        times.append([1, 1.88])
        keys.append([1.17807, 1.17807])

        names.append("RHand")
        times.append([1, 1.88])
        keys.append([0.2868, 0.2868])

        names.append("RHipPitch")
        times.append([1, 1.88])
        keys.append([0.12728, 0.12728])

        names.append("RHipRoll")
        times.append([1, 1.88])
        keys.append([-0.105804, -0.105804])

        names.append("RHipYawPitch")
        times.append([1, 1.88])
        keys.append([-0.16563, -0.16563])

        names.append("RKneePitch")
        times.append([1, 1.88])
        keys.append([-0.0873961, -0.0873961])

        names.append("RShoulderPitch")
        times.append([1, 1.88])
        keys.append([1.48035, 1.48035])

        names.append("RShoulderRoll")
        times.append([1, 1.88])
        keys.append([-0.15651, -0.15651])

        names.append("RWristYaw")
        times.append([1, 1.88])
        keys.append([0.078192, 0.078192])

        self.updateWithBlink(names, keys, times, self.eyeColor['interested'], self.eyeShape['interested'],True, True)

    def FoundEdgeEmotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False

        names = list()
        times = list()
        keys = list()

        names.append("HeadPitch")
        times.append([1, 1.72, 2.28])
        keys.append([-0.165714, 0.113474, 0.260738])

        names.append("HeadYaw")
        times.append([1, 1.72, 2.28])
        keys.append([0.00302601, -0.0123138, 0.10427])

        names.append("LAnklePitch")
        times.append([1, 1.72, 2.28])
        keys.append([0.0873961, 0.0935321, 0.0935321])

        names.append("LAnkleRoll")
        times.append([1, 1.72, 2.28])
        keys.append([-0.13495, -0.13495, -0.13495])

        names.append("LElbowRoll")
        times.append([1, 1.72, 2.28])
        keys.append([-0.404934, -1.38823, -1.49868])

        names.append("LElbowYaw")
        times.append([1, 1.72, 2.28])
        keys.append([-1.17509, -1.37144, -1.11679])

        names.append("LHand")
        times.append([1, 1.72, 2.28])
        keys.append([0.29, 0.524, 0.9896])

        names.append("LHipPitch")
        times.append([1, 1.72, 2.28])
        keys.append([0.12583, 0.12583, 0.12583])

        names.append("LHipRoll")
        times.append([1, 1.72, 2.28])
        keys.append([0.105888, 0.108956, 0.108956])

        names.append("LHipYawPitch")
        times.append([1, 1.72, 2.28])
        keys.append([-0.16563, -0.176368, -0.16563])

        names.append("LKneePitch")
        times.append([1, 1.72, 2.28])
        keys.append([-0.090548, -0.090548, -0.090548])

        names.append("LShoulderPitch")
        times.append([1, 1.72, 2.28])
        keys.append([1.48334, 1.07836, 0.417206])

        names.append("LShoulderRoll")
        times.append([1, 1.72, 2.28])
        keys.append([0.1733, 0.0337059, -0.127364])

        names.append("LWristYaw")
        times.append([1, 1.72, 2.28])
        keys.append([0.08126, -1.6675, -1.20423])

        names.append("RAnklePitch")
        times.append([1, 1.72, 2.28])
        keys.append([0.090548, 0.0828779, 0.093616])

        names.append("RAnkleRoll")
        times.append([1, 1.72, 2.28])
        keys.append([0.122762, 0.124296, 0.135034])

        names.append("RElbowRoll")
        times.append([1, 1.72, 2.28])
        keys.append([0.431096, 1.40825, 1.5049])

        names.append("RElbowYaw")
        times.append([1, 1.72, 2.28])
        keys.append([1.17807, 1.59532, 1.15046])

        names.append("RHand")
        times.append([1, 1.72, 2.28])
        keys.append([0.2868, 0.546, 0.7084])

        names.append("RHipPitch")
        times.append([1, 1.72, 2.28])
        keys.append([0.12728, 0.122678, 0.122678])

        names.append("RHipRoll")
        times.append([1, 1.72, 2.28])
        keys.append([-0.0935321, -0.098134, -0.108872])

        names.append("RHipYawPitch")
        times.append([1, 1.72, 2.28])
        keys.append([-0.16563, -0.176368, -0.16563])

        names.append("RKneePitch")
        times.append([1, 1.72, 2.28])
        keys.append([-0.0873961, -0.0873961, -0.0873961])

        names.append("RShoulderPitch")
        times.append([1, 1.72, 2.28])
        keys.append([1.48035, 1.11219, 0.464844])

        names.append("RShoulderRoll")
        times.append([1, 1.72, 2.28])
        keys.append([-0.168782, 0.147222, 0.185572])

        names.append("RWristYaw")
        times.append([1, 1.72, 2.28])
        keys.append([0.078192, 1.27931, 1.27931])


        self.updateWithBlink(names, keys, times, self.eyeColor['scared'], self.eyeShape['scared'],True)

    def happy1Emotion(self):
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


    def happy2Emotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False
        # Choregraphe simplified export in Python.

        names.append("HeadPitch")
        times.append([1, 1.64, 1.96, 2.28, 2.6, 2.92, 3.24, 3.56, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([-4.19617e-05, -4.19617e-05, -4.19617e-05, -4.19617e-05, -4.19617e-05, -4.19617e-05, -4.19617e-05, -4.19617e-05, -4.19617e-05, -4.19617e-05, -4.19617e-05, -4.19617e-05, -4.19617e-05, -4.19617e-05, -4.19617e-05])

        names.append("HeadYaw")
        times.append([1, 1.64, 1.96, 2.28, 2.6, 2.92, 3.24, 3.56, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([-0.0061779, -0.00617791, -0.00617791, -0.00617791, -0.00617791, -0.00617791, -0.00617791, -0.00617791, -0.00617791, -0.0061779, -0.0061779, -0.00617791, -0.00617791, -0.00617791, -0.00617791])

        names.append("LAnklePitch")
        times.append([1, 2.6, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([-0.342124, -0.383541, -0.414222, -0.342124, -0.351328, -0.342125, -0.351328, -0.342125, -0.339056])

        names.append("LAnkleRoll")
        times.append([1, 2.6, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([-0.00149202, -0.141086, 0.101286, -0.00455999, -0.00455999, -0.00455999, -0.00455999, -0.00455999, -0.00455999])

        names.append("LElbowRoll")
        times.append([1, 1.64, 1.96, 2.28, 2.6, 2.92, 3.24, 3.56, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([-0.981718, -1.46186, -1.04921, -1.46186, -1.04921, -1.37596, -0.992455, -1.37596, -0.992455, -0.906552, -1.47413, -0.906552, -1.47413, -0.906552, -1.09063])

        names.append("LElbowYaw")
        times.append([1, 1.64, 1.96, 2.28, 2.6, 2.92, 3.24, 3.56, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([-1.37144, -2.06787, -2.07555, -2.06787, -2.07555, -1.34689, -1.33002, -1.34689, -1.33002, -1.5233, -1.54171, -1.5233, -1.54171, -1.5233, -1.53404])

        names.append("LHand")
        times.append([1, 1.64, 1.96, 2.28, 2.6, 2.92, 3.24, 3.56, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([0.2676, 0.2676, 0.2676, 0.2676, 0.2676, 0.2676, 0.2676, 0.2676, 0.2676, 0.2676, 0.2676, 0.2676, 0.2676, 0.2676, 0.2676])

        names.append("LHipPitch")
        times.append([1, 2.6, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([-0.452488, -0.452487, -0.463226, -0.450954, -0.450954, -0.450955, -0.450955, -0.450955, -0.450955])

        names.append("LHipRoll")
        times.append([1, 2.6, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([-0.00302601, 0.14884, -0.0827939, 0.00157595, 0.00157595, 0.00157595, 0.00157595, 0.00157595, 0.00157595])

        names.append("LHipYawPitch")
        times.append([1, 2.6, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([0.00310993, 0.00310993, -0.0137641, 0.00924587, 0.00924587, 0.00924586, 0.00924586, 0.00924586, 0.00924586])

        names.append("LKneePitch")
        times.append([1, 2.6, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([0.700996, 0.734743, 0.808375, 0.699462, 0.699462, 0.699462, 0.699462, 0.699462, 0.699462])

        names.append("LShoulderPitch")
        times.append([1, 1.64, 1.96, 2.28, 2.6, 2.92, 3.24, 3.56, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([1.43118, 1.1658, 1.2425, 1.1658, 1.2425, 1.13358, 1.16733, 1.13358, 1.16733, 0.960242, 1.60912, 0.960242, 1.60912, 0.960242, 1.34528])

        names.append("LShoulderRoll")
        times.append([1, 1.64, 1.96, 2.28, 2.6, 2.92, 3.24, 3.56, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([0.266874, -0.0537319, -0.107422, -0.0537319, -0.107422, -0.0583339, -0.115092, -0.0583338, -0.115092, -0.0353239, 0.0214341, -0.0353239, 0.021434, -0.0353239, -0.0153821])

        names.append("LWristYaw")
        times.append([1, 1.64, 1.96, 2.28, 2.6, 2.92, 3.24, 3.56, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([0.0152981, 0.223922, 0.263807, 0.223922, 0.263807, 0.176368, 0.262272, 0.176367, 0.262272, -0.0153821, -0.0322559, -0.0153821, -0.032256, -0.0153821, -0.0767419])

        names.append("RAnklePitch")
        times.append([1, 2.6, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([-0.346642, -0.41107, -0.366584, -0.351244, -0.346642, -0.351244, -0.346642, -0.351244, -0.348176])

        names.append("RAnkleRoll")
        times.append([1, 2.6, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([0.00310993, -0.130348, 0.0767419, 0.00771189, 0.00771189, 0.00771189, 0.00771189, 0.00771189, 0.00771189])

        names.append("RElbowRoll")
        times.append([1, 1.64, 1.96, 2.28, 2.6, 2.92, 3.24, 3.56, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([0.983336, 1.1214, 0.779314, 1.1214, 0.779314, 1.35456, 0.871354, 1.35456, 0.871354, 1.49262, 0.837606, 1.49262, 0.837606, 1.49262, 1.1306])

        names.append("RElbowYaw")
        times.append([1, 1.64, 1.96, 2.28, 2.6, 2.92, 3.24, 3.56, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([1.38209, 1.16273, 1.11211, 1.16273, 1.11211, 1.78553, 1.89445, 1.78554, 1.89445, 1.60299, 1.59072, 1.60299, 1.59072, 1.60299, 1.67815])

        names.append("RHand")
        times.append([1, 1.64, 1.96, 2.28, 2.6, 2.92, 3.24, 3.56, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([0.2696, 0.2696, 0.2696, 0.2696, 0.2696, 0.2696, 0.2696, 0.2696, 0.2696, 0.2696, 0.2696, 0.2696, 0.2696, 0.2696, 0.2696])

        names.append("RHipPitch")
        times.append([1, 2.6, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([-0.452572, -0.452573, -0.449504, -0.449504, -0.449504, -0.449504, -0.449504, -0.449504, -0.449504])

        names.append("RHipRoll")
        times.append([1, 2.6, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([0.00157595, 0.145772, -0.0551819, 0.00771189, 0.00771189, 0.00771189, 0.00771189, 0.00771189, 0.00771189])

        names.append("RHipYawPitch")
        times.append([1, 2.6, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([0.00310993, 0.00310993, -0.0137641, 0.00924587, 0.00924587, 0.00924586, 0.00924586, 0.00924586, 0.00924586])

        names.append("RKneePitch")
        times.append([1, 2.6, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([0.696478, 0.734827, 0.728692, 0.694944, 0.688808, 0.694945, 0.688808, 0.694945, 0.694945])

        names.append("RShoulderPitch")
        times.append([1, 1.64, 1.96, 2.28, 2.6, 2.92, 3.24, 3.56, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([1.42666, 0.960326, 1.07538, 0.960325, 1.07538, 1.15514, 1.04776, 1.15514, 1.04776, 1.84698, 1.05697, 1.84698, 1.05697, 1.84698, 1.2932])

        names.append("RShoulderRoll")
        times.append([1, 1.64, 1.96, 2.28, 2.6, 2.92, 3.24, 3.56, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([-0.293036, 0.199378, 0.249999, 0.199378, 0.249999, 0.075124, 0.024502, 0.075124, 0.024502, 0.00609398, 0.0597839, 0.00609397, 0.059784, 0.00609397, 0.116542])

        names.append("RWristYaw")
        times.append([1, 1.64, 1.96, 2.28, 2.6, 2.92, 3.24, 3.56, 3.88, 4.2, 4.52, 4.88, 5.24, 5.6, 5.96])
        keys.append([0.0337059, 0.263806, 0.251533, 0.263807, 0.251533, -0.0307219, -0.06447, -0.030722, -0.06447, 0.0199001, -0.0368581, 0.0199001, -0.036858, 0.0199001, -0.0552659])

        self.updateWithBlink(names, keys, times, self.eyeColor['happy'], self.eyeShape['happy'])

    def sad1Emotion(self):
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

    def sad2Emotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False
        # Choregraphe simplified export in Python.

        names.append("HeadPitch")
        times.append([1, 2, 2.72, 3.4, 4.12, 4.8])
        keys.append([-0.16418, 0.455556, 0.283748, 0.47243, 0.283749, 0.472429])

        names.append("HeadYaw")
        times.append([1, 2, 2.72, 3.4, 4.12, 4.8])
        keys.append([-0.0138481, 0.0367742, 0.026036, 0.026036, 0.0260359, 0.0260359])

        names.append("LAnklePitch")
        times.append([1])
        keys.append([0.0919981])

        names.append("LAnkleRoll")
        times.append([1])
        keys.append([-0.124212])

        names.append("LElbowRoll")
        times.append([1, 2])
        keys.append([-0.423342, -0.423342])

        names.append("LElbowYaw")
        times.append([1, 2])
        keys.append([-1.20883, -1.20883])

        names.append("LHand")
        times.append([1, 2])
        keys.append([0.2856, 0.2856])

        names.append("LHipPitch")
        times.append([1])
        keys.append([0.136568])

        names.append("LHipRoll")
        times.append([1])
        keys.append([0.092082])

        names.append("LHipYawPitch")
        times.append([1])
        keys.append([-0.170232])

        names.append("LKneePitch")
        times.append([1])
        keys.append([-0.0923279])

        names.append("LShoulderPitch")
        times.append([1, 2])
        keys.append([1.46493, 1.46493])

        names.append("LShoulderRoll")
        times.append([1, 2])
        keys.append([0.167164, 0.167164])

        names.append("LWristYaw")
        times.append([1, 2])
        keys.append([0.0873961, 0.0873961])

        names.append("RAnklePitch")
        times.append([1])
        keys.append([0.093616])

        names.append("RAnkleRoll")
        times.append([1])
        keys.append([0.12583])

        names.append("RElbowRoll")
        times.append([1, 2])
        keys.append([0.443368, 1.19963])

        names.append("RElbowYaw")
        times.append([1, 2])
        keys.append([1.21182, -0.181054])

        names.append("RHand")
        times.append([1, 2])
        keys.append([0.2916, 0.5556])

        names.append("RHipPitch")
        times.append([1])
        keys.append([0.131882])

        names.append("RHipRoll")
        times.append([1])
        keys.append([-0.0935321])

        names.append("RHipYawPitch")
        times.append([1])
        keys.append([-0.170232])

        names.append("RKneePitch")
        times.append([1])
        keys.append([-0.082794])

        names.append("RShoulderPitch")
        times.append([1, 2])
        keys.append([1.47115, -0.4034])

        names.append("RShoulderRoll")
        times.append([1, 2])
        keys.append([-0.165714, 0.314159])

        names.append("RWristYaw")
        times.append([1, 2])
        keys.append([0.0873961, -0.460242])


        self.updateWithBlink(names, keys, times, self.eyeColor['sad'], self.eyeShape['sad'],True)

    def scared1Emotion(self):
        names = list()
        times = list()
        keys = list()

        names.append("HeadPitch")
        times.append([0.8, 2.36])
        keys.append([-0.0537319, 0.279146])

        names.append("HeadYaw")
        times.append([0.8, 2.36])
        keys.append([0.0183661, -0.77011])

        names.append("LAnklePitch")
        times.append([0.8, 2.36])
        keys.append([-0.34826, 0.21165])

        names.append("LAnkleRoll")
        times.append([0.8, 2.36])
        keys.append([-0.00609397, -0.0935321])

        names.append("LElbowRoll")
        times.append([0.8, 2.36])
        keys.append([-0.989389, -1.43118])

        names.append("LElbowYaw")
        times.append([0.8, 2.36])
        keys.append([-1.3699, -0.90817])

        names.append("LHand")
        times.append([0.8, 2.36])
        keys.append([0.262, 0.9844])

        names.append("LHipPitch")
        times.append([0.8, 2.36])
        keys.append([-0.440216, -0.154892])

        names.append("LHipRoll")
        times.append([0.8, 2.36])
        keys.append([0.00157595, 0.108956])

        names.append("LHipYawPitch")
        times.append([0.8, 2.36])
        keys.append([0.00464392, -0.519984])

        names.append("LKneePitch")
        times.append([0.8, 2.36])
        keys.append([0.707132, 0.37272])

        names.append("LShoulderPitch")
        times.append([0.8, 2.36])
        keys.append([1.45419, 0.39573])

        names.append("LShoulderRoll")
        times.append([0.8, 2.36])
        keys.append([0.299088, -0.214802])

        names.append("LWristYaw")
        times.append([0.8, 2.36])
        keys.append([0.0137641, 1.2517])

        names.append("RAnklePitch")
        times.append([0.8, 2.36])
        keys.append([-0.352778, -0.5568])

        names.append("RAnkleRoll")
        times.append([0.8, 2.36])
        keys.append([0.00771189, 0.158044])

        names.append("RElbowRoll")
        times.append([0.8, 2.36])
        keys.append([0.981802, 1.34536])

        names.append("RElbowYaw")
        times.append([0.8, 2.36])
        keys.append([1.36829, 1.36062])

        names.append("RHand")
        times.append([0.8, 2.36])
        keys.append([0.2644, 0.9844])

        names.append("RHipPitch")
        times.append([0.8, 2.36])
        keys.append([-0.449504, 0.08126])

        names.append("RHipRoll")
        times.append([0.8, 2.36])
        keys.append([-0.00609397, -0.282214])

        names.append("RHipYawPitch")
        times.append([0.8, 2.36])
        keys.append([0.00464392, -0.519984])

        names.append("RKneePitch")
        times.append([0.8, 2.36])
        keys.append([0.70108, 0.865218])

        names.append("RShoulderPitch")
        times.append([0.8, 2.36])
        keys.append([1.45581, 0.41729])

        names.append("RShoulderRoll")
        times.append([0.8, 2.36])
        keys.append([-0.276162, 0.0659201])

        names.append("RWristYaw")
        times.append([0.8, 2.36])
        keys.append([0.0168321, -1.17815])

        if self.bScared == False:
            self.blinkAlarmingEyes(max(max(times))*3,self.eyeColor['scared'],self.eyeShape['scared'])
            self.updateWithBlink(names, keys, times, self.eyeColor['scared'], self.eyeShape['scared'],bDisableEye=True)
            self.setEyeEmotion('scared')
            self.bScared = True


    def scared2Emotion(self):
        names = list()
        times = list()
        keys = list()

        names.append("HeadPitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.00310993, 0.11961, 0.15029, 0.102736, 0.331302])

        names.append("HeadYaw")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.00617791, 0.00302601, 0.00302601, -0.489388, -0.71642])

        names.append("LAnklePitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.343659, -0.277696, -0.12583, 0.246932, 0.375788])

        names.append("LAnkleRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.00464392, 0.19486, 0.224006, 0.182588, 0.0997519])

        names.append("LElbowRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.981718, -0.977116, -0.966378, -0.76389, -1.47873])

        names.append("LElbowYaw")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-1.37144, -1.34689, -1.35763, -1.14747, -1.14747])

        names.append("LHand")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.2572, 0.2596, 0.2596, 0.2596, 0.9844])

        names.append("LHipPitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.450955, -0.44942, -0.61816, -0.789968, -0.523052])

        names.append("LHipRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.00464392, -0.171766, -0.197844, -0.167164, -0.14262])

        names.append("LHipYawPitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.00157595, 0.0138481, -0.0720561, -0.162562, -0.162562])

        names.append("LKneePitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.696393, 0.654976, 0.670316, 0.44175, 0.44175])

        names.append("LShoulderPitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([1.41737, 1.43271, 1.43271, 1.05382, 0.685656])

        names.append("LShoulderRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.27301, 0.271476, 0.260738, -0.0567999, -0.138102])

        names.append("LWristYaw")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.0152981, 0.0229681, 0.0229681, 0.0444441, 1.7932])

        names.append("RAnklePitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.36505, -0.404934, -0.619694, -0.539926, -1.0124])

        names.append("RAnkleRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.00609397, 0.158044, 0.147306, 0.228608, -0.0628521])

        names.append("RElbowRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.977199, 0.989472, 0.9772, 0.935782, 1.45734])

        names.append("RElbowYaw")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([1.38209, 1.36062, 1.36062, 1.46953, 1.23943])

        names.append("RHand")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.2476, 0.2472, 0.2472, 0.2472, 0.9768])

        names.append("RHipPitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.461776, -0.282298, -0.0567999, 0.331302, 0.25])

        names.append("RHipRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.00617791, -0.116542, -0.15796, -0.191708, -0.0383081])

        names.append("RHipYawPitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.00157595, 0.0138481, -0.0720561, -0.162562, -0.162562])

        names.append("RKneePitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([0.702614, 0.564554, 0.575292, 0.0782759, 1.02322])

        names.append("RShoulderPitch")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([1.41286, 1.4374, 1.4374, 1.0631, 0.483252])

        names.append("RShoulderRoll")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.27923, -0.24088, -0.24088, 0.0383081, 0.18864])

        names.append("RWristYaw")
        times.append([0.8, 1.44, 2.24, 3.08, 3.84])
        keys.append([-0.0138481, -0.00924587, 0.026036, 0.0152981, -1.54785])

        if self.bScared == False:
            self.blinkAlarmingEyes(max(max(times))*3,self.eyeColor['scared'], self.eyeShape['scared'])
            self.updateWithBlink(names, keys, times, self.eyeColor['scared'], self.eyeShape['scared'],bDisableEye=True)
            self.setEyeEmotion('scared')
            self.bScared = True


    def worried1Emotion(self):
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
        self.updateWithBlink(names, keys, times, self.eyeColor['worried'], self.eyeShape['worried'])


    def worried2Emotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False
        # Choregraphe simplified export in Python.

        names.append("HeadPitch")
        times.append([0.36, 2.28, 3.12, 4.04, 4.88, 5.76, 6.36])
        keys.append([-0.19486, -0.19486, -0.19486, -0.194861, -0.194861, -0.194861, -0.19486])

        names.append("HeadYaw")
        times.append([0.36, 2.28, 3.12, 4.04, 4.88, 5.76, 6.36])
        keys.append([0.0137641, -0.613642, 0.406468, -0.613642, 0.406468, -0.613642, 0.00762796])

        names.append("LAnklePitch")
        times.append([0.36])
        keys.append([0.0843279])

        names.append("LAnkleRoll")
        times.append([0.36])
        keys.append([-0.12728])

        names.append("LElbowRoll")
        times.append([0.36, 1.8])
        keys.append([-0.412604, -0.401866])

        names.append("LElbowYaw")
        times.append([0.36, 1.8])
        keys.append([-1.2073, -1.2073])

        names.append("LHand")
        times.append([0.36, 1.8])
        keys.append([0.2952, 0.2952])

        names.append("LHipPitch")
        times.append([0.36])
        keys.append([0.136568])

        names.append("LHipRoll")
        times.append([0.36])
        keys.append([0.10282])

        names.append("LHipYawPitch")
        times.append([0.36])
        keys.append([-0.16563])

        names.append("LKneePitch")
        times.append([0.36])
        keys.append([-0.0844119])

        names.append("LShoulderPitch")
        times.append([0.36, 1.8])
        keys.append([1.46339, 1.47413])

        names.append("LShoulderRoll")
        times.append([0.36, 1.8])
        keys.append([0.177902, 0.177902])

        names.append("LWristYaw")
        times.append([0.36, 1.8])
        keys.append([0.0873961, 0.0873961])

        names.append("RAnklePitch")
        times.append([0.36])
        keys.append([0.0890141])

        names.append("RAnkleRoll")
        times.append([0.36])
        keys.append([0.124296])

        names.append("RElbowRoll")
        times.append([0.36, 1.8])
        keys.append([0.438766, 1.07998])

        names.append("RElbowYaw")
        times.append([0.36, 1.8])
        keys.append([1.18114, 0.391128])

        names.append("RHand")
        times.append([0.36, 1.8])
        keys.append([0.3156, 0.9916])

        names.append("RHipPitch")
        times.append([0.36])
        keys.append([0.136484])

        names.append("RHipRoll")
        times.append([0.36])
        keys.append([-0.099668])

        names.append("RHipYawPitch")
        times.append([0.36])
        keys.append([-0.16563])

        names.append("RKneePitch")
        times.append([0.36])
        keys.append([-0.082794])

        names.append("RShoulderPitch")
        times.append([0.36, 1.8])
        keys.append([1.46655, -0.826784])

        names.append("RShoulderRoll")
        times.append([0.36, 1.8])
        keys.append([-0.14884, 0.131882])

        names.append("RWristYaw")
        times.append([0.36, 1.8])
        keys.append([0.131882, -1.26559])

        self.updateWithBlink(names, keys, times, self.eyeColor['worried'], self.eyeShape['worried'],True)




    def interested1Emotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False
        # Choregraphe simplified export in Python.
        # Choregraphe simplified export in Python.

        names.append("HeadPitch")
        times.append([1, 2.24])
        keys.append([-0.181053, -0.589098])

        names.append("HeadYaw")
        times.append([1, 2.24])
        keys.append([0.00609397, 0.0137641])

        names.append("LAnklePitch")
        times.append([1, 2.24])
        keys.append([0.0966001, 0.182504])

        names.append("LAnkleRoll")
        times.append([1, 2.24])
        keys.append([-0.122678, -0.133416])

        names.append("LElbowRoll")
        times.append([1, 2.24, 2.64, 3.04, 3.44, 3.84, 4.24, 4.64])
        keys.append([-0.421808, -1.27318, -1.24557, -1.27318, -1.24557, -1.27318, -1.24557, -1.27318])

        names.append("LElbowYaw")
        times.append([1, 2.24, 2.64, 3.04, 3.44, 3.84, 4.24, 4.64])
        keys.append([-1.17969, -0.949588, -1.33309, -0.949588, -1.33309, -0.949588, -1.33309, -0.949588])

        names.append("LHand")
        times.append([1, 2.24, 2.64, 3.04, 3.44, 3.84, 4.24, 4.64])
        keys.append([0.3084, 0.9904, 0.9784, 0.9904, 0.9784, 0.9904, 0.9784, 0.9904])

        names.append("LHipPitch")
        times.append([1, 2.24])
        keys.append([0.127364, -0.236194])

        names.append("LHipRoll")
        times.append([1, 2.24])
        keys.append([0.10282, 0.0614018])

        names.append("LHipYawPitch")
        times.append([1, 2.24])
        keys.append([-0.176367, -0.259204])

        names.append("LKneePitch")
        times.append([1, 2.24])
        keys.append([-0.0844118, -0.0859461])

        names.append("LShoulderPitch")
        times.append([1, 2.24, 2.64, 3.04, 3.44, 3.84, 4.24, 4.64])
        keys.append([1.46493, 1.03234, 1.16887, 1.03234, 1.16887, 1.03234, 1.16887, 1.03234])

        names.append("LShoulderRoll")
        times.append([1, 2.24, 2.64, 3.04, 3.44, 3.84, 4.24, 4.64])
        keys.append([0.174835, -0.0153821, 0.0337059, -0.0153821, 0.033706, -0.0153821, 0.033706, -0.0153821])

        names.append("LWristYaw")
        times.append([1, 2.24, 2.64, 3.04, 3.44, 3.84, 4.24, 4.64])
        keys.append([0.0843279, -0.039926, -0.067538, -0.039926, -0.067538, -0.039926, -0.067538, -0.039926])

        names.append("RAnklePitch")
        times.append([1, 2.24])
        keys.append([0.101286, 0.237812])

        names.append("RAnkleRoll")
        times.append([1, 2.24])
        keys.append([0.12583, 0.145772])

        names.append("RElbowRoll")
        times.append([1, 2.24, 2.64, 3.04, 3.44, 3.84, 4.24, 4.64])
        keys.append([0.444902, 1.27786, 1.23645, 1.27786, 1.23645, 1.27786, 1.23645, 1.27786])

        names.append("RElbowYaw")
        times.append([1, 2.24, 2.64, 3.04, 3.44, 3.84, 4.24, 4.64])
        keys.append([1.20108, 0.954107, 1.35908, 0.954107, 1.35908, 0.954107, 1.35908, 0.954107])

        names.append("RHand")
        times.append([1, 2.24, 2.64, 3.04, 3.44, 3.84, 4.24, 4.64])
        keys.append([0.3048, 0.9908, 0.9776, 0.9908, 0.9776, 0.9908, 0.9776, 0.9908])

        names.append("RHipPitch")
        times.append([1, 2.24])
        keys.append([0.12728, -0.312978])

        names.append("RHipRoll")
        times.append([1, 2.24])
        keys.append([-0.105804, -0.0935321])

        names.append("RHipYawPitch")
        times.append([1, 2.24])
        keys.append([-0.176367, -0.259204])

        names.append("RKneePitch")
        times.append([1, 2.24])
        keys.append([-0.0858622, -0.0919981])

        names.append("RShoulderPitch")
        times.append([1, 2.24, 2.64, 3.04, 3.44, 3.84, 4.24, 4.64])
        keys.append([1.45734, 1.01708, 1.14134, 1.01708, 1.14134, 1.01708, 1.14134, 1.01708])

        names.append("RShoulderRoll")
        times.append([1, 2.24, 2.64, 3.04, 3.44, 3.84, 4.24, 4.64])
        keys.append([-0.15651, 0.0199001, 0.0122299, 0.0199001, 0.0122299, 0.0199001, 0.0122299, 0.0199001])

        names.append("RWristYaw")
        times.append([1, 2.24, 2.64, 3.04, 3.44, 3.84, 4.24, 4.64])
        keys.append([0.118076, 0.061318, 0.0858622, 0.061318, 0.0858622, 0.061318, 0.0858622, 0.061318])


        self.updateWithBlink(names, keys, times, self.eyeColor['interested'], self.eyeShape['interested'], True)


    def interested2Emotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False
        # Choregraphe simplified export in Python.
        # Choregraphe simplified export in Python.

        names.append("HeadPitch")
        times.append([1, 1.84, 2.32, 2.76, 3.2, 3.6, 4.04])
        keys.append([-0.145772, -0.385075, -0.145772, -0.613642, -0.145772, -0.613642, -0.385075])

        names.append("HeadYaw")
        times.append([1, 1.84, 2.32, 2.76, 3.2, 3.6, 4.04])
        keys.append([0.0122299, -0.00924586, 0.0106959, -0.00771189, 0.0106959, -0.00771189, -0.00924586])

        names.append("LAnklePitch")
        times.append([1, 1.84])
        keys.append([0.093532, 0.170232])

        names.append("LAnkleRoll")
        times.append([1, 1.84])
        keys.append([-0.12728, -0.131882])

        names.append("LElbowRoll")
        times.append([1, 1.84])
        keys.append([-0.420274, -0.0429101])

        names.append("LElbowYaw")
        times.append([1, 1.84])
        keys.append([-1.17048, 0.030638])

        names.append("LHand")
        times.append([1, 1.84])
        keys.append([0.292, 0.5864])

        names.append("LHipPitch")
        times.append([1, 1.84])
        keys.append([0.12583, -0.154892])

        names.append("LHipRoll")
        times.append([1, 1.84])
        keys.append([0.10282, 0.0982179])

        names.append("LHipYawPitch")
        times.append([1, 1.84])
        keys.append([-0.161028, -0.21932])

        names.append("LKneePitch")
        times.append([1, 1.84])
        keys.append([-0.0859461, -0.0859461])

        names.append("LShoulderPitch")
        times.append([1, 1.84])
        keys.append([1.46646, 0.931096])

        names.append("LShoulderRoll")
        times.append([1, 1.84])
        keys.append([0.170232, -0.191792])

        names.append("LWristYaw")
        times.append([1, 1.84])
        keys.append([0.0889301, -1.78408])

        names.append("RAnklePitch")
        times.append([1, 1.84])
        keys.append([0.0951499, 0.2102])

        names.append("RAnkleRoll")
        times.append([1, 1.84])
        keys.append([0.122762, 0.0951499])

        names.append("RElbowRoll")
        times.append([1, 1.84])
        keys.append([0.444902, 0.144238])

        names.append("RElbowYaw")
        times.append([1, 1.84])
        keys.append([1.16887, 0.335904])

        names.append("RHand")
        times.append([1, 1.84])
        keys.append([0.29, 0.5032])

        names.append("RHipPitch")
        times.append([1, 1.84])
        keys.append([0.124212, -0.181053])

        names.append("RHipRoll")
        times.append([1, 1.84])
        keys.append([-0.0966001, -0.05058])

        names.append("RHipYawPitch")
        times.append([1, 1.84])
        keys.append([-0.161028, -0.21932])

        names.append("RKneePitch")
        times.append([1, 1.84])
        keys.append([-0.0827939, -0.0827939])

        names.append("RShoulderPitch")
        times.append([1, 1.84])
        keys.append([1.48189, 0.935782])

        names.append("RShoulderRoll")
        times.append([1, 1.84])
        keys.append([-0.17185, 0.223922])

        names.append("RWristYaw")
        times.append([1, 1.84])
        keys.append([0.131882, 1.40817])


        self.updateWithBlink(names, keys, times, self.eyeColor['interested'], self.eyeShape['interested'],True)


    def anger1Emotion(self):
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



    def anger2Emotion(self):
        names = list()
        times = list()
        keys = list()
        self.bScared = False
        # Choregraphe simplified export in Python.
        # Choregraphe simplified export in Python.

        names.append("HeadPitch")
        times.append([1, 2.68])
        keys.append([-0.0123138, 0.00762796])

        names.append("HeadYaw")
        times.append([1, 2.68])
        keys.append([-0.00771189, -0.00771189])

        names.append("LAnklePitch")
        times.append([1])
        keys.append([-0.358999])

        names.append("LAnkleRoll")
        times.append([1])
        keys.append([4.19617e-05])

        names.append("LElbowRoll")
        times.append([1, 2, 2.36, 2.68, 3, 3.32, 4.04, 4.44, 4.84, 5.2])
        keys.append([-0.981718, -0.888144, -1.30693, -1.29772, -0.384992, -1.3959, -0.607422, -0.61049, -0.61049, -0.61049])

        names.append("LElbowYaw")
        times.append([1, 2, 2.36, 2.68, 3, 3.32, 4.04, 4.44, 4.84, 5.2])
        keys.append([-1.36684, -1.27633, -1.29167, -0.935783, -0.879025, -1.04163, -1.33155, -1.31468, -1.31468, -1.31468])

        names.append("LHand")
        times.append([1, 2, 2.36, 2.68, 3, 3.32, 4.04, 4.44, 4.84, 5.2])
        keys.append([0.2588, 0.2904, 0.2904, 0.3012, 0.2936, 0.3012, 0.2936, 0.2952, 0.2952, 0.2952])

        names.append("LHipPitch")
        times.append([1])
        keys.append([-0.452487])

        names.append("LHipRoll")
        times.append([1])
        keys.append([-0.00149202])

        names.append("LHipYawPitch")
        times.append([1])
        keys.append([-0.00762796])

        names.append("LKneePitch")
        times.append([1])
        keys.append([0.704064])

        names.append("LShoulderPitch")
        times.append([1, 2, 2.36, 2.68, 3, 3.32, 4.04, 4.44, 4.84, 5.2])
        keys.append([1.42965, 0.414139, -0.438765, -0.351328, -0.694945, -0.517, 1.49714, 1.47873, 1.47873, 1.47873])

        names.append("LShoulderRoll")
        times.append([1, 2, 2.36, 2.68, 3, 3.32, 4.04, 4.44, 4.84, 5.2])
        keys.append([0.266875, 0.220854, 0.710201, -0.0567998, 0.90962, -0.0107799, 0.329768, 0.308291, 0.308291, 0.308291])

        names.append("LWristYaw")
        times.append([1, 2, 2.36, 2.68, 3, 3.32, 4.04, 4.44, 4.84, 5.2])
        keys.append([0.0152981, -0.895898, -1.00174, -0.93118, -0.983336, -0.949588, -1.70432, -1.67824, -1.67824, -1.67824])

        names.append("RAnklePitch")
        times.append([1])
        keys.append([-0.361981])

        names.append("RAnkleRoll")
        times.append([1])
        keys.append([0.00464392])

        names.append("RElbowRoll")
        times.append([1, 2, 2.36, 2.68, 3, 3.32, 4.04, 4.44, 4.84, 5.2])
        keys.append([0.974133, 1.01862, 1.00481, 1.40825, 0.805393, 1.54018, 0.661195, 0.68574, 0.68574, 0.68574])

        names.append("RElbowYaw")
        times.append([1, 2, 2.36, 2.68, 3, 3.32, 4.04, 4.44, 4.84, 5.2])
        keys.append([1.37135, 1.05228, 0.67952, 0.67952, 0.754686, 0.742414, 0.579811, 0.484702, 0.489305, 0.484702])

        names.append("RHand")
        times.append([1, 2, 2.36, 2.68, 3, 3.32, 4.04, 4.44, 4.84, 5.2])
        keys.append([0.2604, 0.2892, 0.2892, 0.3016, 0.288, 0.3016, 0.288, 0.018, 0.0272, 0.018])

        names.append("RHipPitch")
        times.append([1])
        keys.append([-0.454105])

        names.append("RHipRoll")
        times.append([1])
        keys.append([0.00157595])

        names.append("RHipYawPitch")
        times.append([1])
        keys.append([-0.00762796])

        names.append("RKneePitch")
        times.append([1])
        keys.append([0.702614])

        names.append("RShoulderPitch")
        times.append([1, 2, 2.36, 2.68, 3, 3.32, 4.04, 4.44, 4.84, 5.2])
        keys.append([1.43433, -0.059784, 0.300706, -0.555266, 0.16418, -0.736278, -1.42965, -0.665714, -1.44959, -0.665714])

        names.append("RShoulderRoll")
        times.append([1, 2, 2.36, 2.68, 3, 3.32, 4.04, 4.44, 4.84, 5.2])
        keys.append([-0.257754, -0.50166, -0.280764, -0.179519, -0.894364, -0.343659, -0.247016, -0.266959, -0.30224, -0.266959])

        names.append("RWristYaw")
        times.append([1, 2, 2.36, 2.68, 3, 3.32, 4.04, 4.44, 4.84, 5.2])
        keys.append([0.033706, 1.08143, 0.87127, 0.911154, 1.19494, 1.18267, 1.35448, 1.31613, 1.31613, 1.31613])



        self.updateWithBlink(names, keys, times, self.eyeColor['anger'], self.eyeShape['anger'],True)

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
