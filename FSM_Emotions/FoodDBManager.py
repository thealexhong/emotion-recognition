import FileUtilitiy
import sqlite3
import json
import os.path

class FoodDBManager:
    def __init__(self):
        dbDir = "ProgramDataFiles\\foodDB.db"
        if os.path.isfile(dbDir):
            self.conn = sqlite3.connect(dbDir)
        else:
            self.conn = sqlite3.connect(dbDir.replace('\\', '/'))
        self.c = self.conn.cursor()

        foodItemsFile = "ProgramDataFiles\\foodItemsJSON.txt"
        foodItemsJSON = FileUtilitiy.readLinesToJSON(foodItemsFile)

        self.c.execute("select name from sqlite_master where type='table'")
        # print self.c.fetchall()

        self.dbName = "foodItems"
        sqlStr = "DROP TABLE " + self.dbName
        self.c.execute(sqlStr)
        sqlStr =  "CREATE TABLE " +  self.dbName + " "
        sqlStr += "(id, name, hasPoultry, hasGluten, calories, buyFrom, mealType, hasFish)"
        self.c.execute(sqlStr)

        for food in foodItemsJSON:
            sqlStr =  "INSERT INTO " + self.dbName + " VALUES "
            sqlStr += "('" + str(food['id']) + "', '" + str(food['name']) + "', '" + str(food['hasPoultry'])
            sqlStr += "', '" + str(food['hasGluten']) + "', '" + str(food['calories'])
            sqlStr += "', '" + str(food['buyFrom']) + "', '" + str(food['mealType'])
            sqlStr += "', '" + str(food['hasFish']) + "')"
            self.c.execute(sqlStr)
        self.conn.commit()

    def showDB(self):
        sqlStr = "PRAGMA table_info('" + self.dbName + "')"
        self.c.execute(sqlStr)
        dbRows = self.c.fetchall()
        for row in dbRows:
            print self.dict_factory(row)['name'], " | ",
        print

        sqlStr = "SELECT * FROM " + self.dbName
        self.c.execute(sqlStr)
        dbRows = self.c.fetchall()
        for row in dbRows:
            print self.dict_factory(row)

    def selectDBWhere(self, mealType = "Lunch", canEatPoultry = True, canEatGluten = True, canEatFish = True,
                      strictIngredients = False):
        sqlStr = "SELECT * FROM " + self.dbName + " "
        sqlStr += "WHERE mealType='" + mealType + "' "
        if (not canEatPoultry) or (not canEatGluten) or (not canEatFish) or strictIngredients:
            sqlStr += "AND "
        if (not canEatPoultry) or strictIngredients:
            sqlStr += "hasPoultry='" + str(canEatPoultry) + "' "
            if (not canEatGluten) or (not canEatFish) or strictIngredients:
                sqlStr += "AND "
        if (not canEatGluten) or strictIngredients:
            sqlStr += "hasGluten='" + str(canEatGluten) + "' "
            if (not canEatFish) or strictIngredients:
                sqlStr += "AND "
        if (not canEatFish) or strictIngredients:
            sqlStr += "hasFish='" + str(canEatFish) + "' "

        print sqlStr
        self.c.execute(sqlStr)

        dbRows = self.c.fetchall()
        return dbRows

    def dict_factory(self, row):
        d = {}
        for idx, col in enumerate(self.c.description):
            d[col[0]] = row[idx]
        return d




#
# fDB = FoodDBManager()
# fDB.showDB()
# print
#
# dbRows = fDB.selectDBWhere(True, False)
# for row in dbRows:
#     print fDB.dict_factory(row)

