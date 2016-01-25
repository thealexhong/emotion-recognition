# utility functions
import time
import datetime
from NAO_Util.BasicMotions import BasicMotions
from FoodDBManager import FoodDBManager
import random

class GenUtil:
    def __init__(self, naoMotions = BasicMotions()):
        # no inits
        self.emotionExpressionDict = ["Happy", "Sad", "Fearful", "Angry", "Surprised", "Hopeful",
                                      "Happy2", "Sad2", "Fearful2", "Angry2", "Surprised2",
                                      "Scared", "Hopeful2"]
                                    
        self.numOE = len(self.emotionExpressionDict)
        self.naoMotions = naoMotions
        self.naoIsSafe = True
        self.fDB = FoodDBManager()
		
    def toNum(self, numAsString):
        # Convert string to either int or float
        try:
            ret = int(float(numAsString))
        except ValueError:
            print "***** This string is not a number: ", numAsString
            ret = numAsString
        return ret

    def expressEmotion(self, obserExpresNum = -1):
        print "********************* Yay I can Express myself"
        print "OE Num: ", obserExpresNum
        # expresses NAOs emotion through what ever was picked as the observable expression
        if obserExpresNum == -1:
            print "Neutral ", "Face"
            self.naoEmotionalVoiceSay("I am " + "Neutral", obserExpresNum)
        else:
            oe = self.emotionExpressionDict[obserExpresNum]
            print oe, "Face"
            self.naoEmotionalVoiceSay("I am expressing " + oe, obserExpresNum)

            if "Happy" in oe:
                self.showHappyEyes()
            elif "Sad" in oe:
                self.showSadEyes()
            elif "Fearful" in oe:
                self.showFearEyes()
            elif "Angry" in oe:
                self.showAngryEyes()
            elif "Hopeful" in oe:
                self.showHopeEyes()
            elif "Scared" in oe:
                self.showScaredEyes()
                
            if oe == "Happy2":
                self.showHappyBody()
            elif oe == "Sad2":
                self.showSadBody()
            elif oe == "Fearful2":
                self.showFearBody()
            elif oe == "Angry2":
                self.showAngryBody()
            elif oe == "Hopeful2":
                self.showHopeBody()
            elif oe == "Scared2":
                self.showScaredBody()
            

    def naoEmotionalSay(self, sayText, sayEmotionExpres = -1, moveIterations=1):
#        print "Yay I get to Express myself through sound!"
        # make nao say something in an emotional manner
        if sayEmotionExpres == -1:
            print "Neutral Voice"
            # self.naoMotions.naoWaveRightSay(sayText, sayEmotionExpres, 0, moveIterations)
            # self.naoMotions.naoShadeHeadSay(sayText)
            self.naoMotions.naoSayWait(sayText, 0.5)
        else:
            oe = self.emotionExpressionDict[sayEmotionExpres]
            print oe, "Voice"
            # self.naoMotions.naoWaveRightSay(sayText, sayEmotionExpres,(sayEmotionExpres+1.0)/(self.numOE+1), 1)
            # self.naoMotions.naoShadeHeadSay(sayText)
            self.naoMotions.naoSayWait(sayText, 0.5)

    def naoEmotionalVoiceSay(self, sayText, sayEmotionExpres = -1):
        self.naoMotions.naoSay(sayText)

################################################ Eyes
    def showHappyEyes(self):
        print "My eyes are Happy"
       
    def showSadEyes(self):
        print "My eyes are Sad"
        
    def showFearEyes(self):
        print "My eyes are Fear"
            
    def showAngryEyes(self):
        print "My eyes are Angry"

    def showHopeEyes(self):
        print "My eyes are Hopeful"
     
    def showScaredEyes(self):
        print "My eyes are Scared"

################################################# Body
    def showHappyBody(self):
        print "My body is Happy"
       
    def showSadBody(self):
        print "My body is Sad"
        
    def showFearBody(self):
        print "My body is Fear"
            
    def showAngryBody(self):
        print "My body is Angry"

    def showHopeBody(self):
        print "My body is Hopeful"
     
    def showScaredBody(self):
        print "My body is Scared"








    def getTimeStamp(self):
        return time.time()

    def getDateTimeFromTime(self, timeStamp):
        return datetime.datetime.fromtimestamp(timeStamp).strftime('%Y-%m-%d_%H-%M-%S')

    def getDateTime(self):
        ts = time.time()
        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H-%M-%S')

    def checkSafety(self):
        return self.naoIsSafe

    def stopNAOActions(self):
        self.naoMotions.stopNAOActions()

    def showFoodDB(self):
        self.fDB.showDB()

    def foodDBSelectWhere(self, mealType = "lunch", canEatPoultry = True, canEatGluten = True, canEatFish = True,
                          strictIngredients = True):
        return self.fDB.selectDBWhere(mealType, canEatPoultry, canEatGluten, canEatFish, strictIngredients)

    def dbRowToDict(self, row):
        return self.fDB.dict_factory(row)

    def randMeal(self, mealsTries, mealPos):
        keepLooping = True
        ranMeal = 0
        while keepLooping:
            ranMeal = random.randint(0, len(mealPos)-1)
            ranIndex = self.dbRowToDict(mealPos[ranMeal])['id']
            # print mealPos
            # print "ranMeal: ", ranMeal, " ranIndex: ", ranIndex, " mealsTries: ", mealsTries

            keepLooping = (ranIndex) in mealsTries


        return ranMeal