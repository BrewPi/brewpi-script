from datetime import datetime
import time

jsonCols = ("\"cols\":[{\"type\":\"datetime\",\"id\":\"Time\",\"label\":\"Time\"}," +
        "{\"type\":\"number\",\"id\":\"BeerTemp\",\"label\":\"Beer temperature\"}," +
        "{\"type\":\"number\",\"id\":\"BeerSet\",\"label\":\"Beer setting\"}," +
        "{\"type\":\"string\",\"id\":\"BeerAnn\",\"label\":\"Beer Annotate\"}," +
        "{\"type\":\"number\",\"id\":\"FridgeTemp\",\"label\":\"Fridge temperature\"}," +
        "{\"type\":\"number\",\"id\":\"FridgeSet\",\"label\":\"Fridge setting\"}," +
        "{\"type\":\"string\",\"id\":\"FridgeAnn\",\"label\":\"Fridge Annotate\"}]")


def addRow(jsonFileName, row):
    jsonFile = open(jsonFileName, "r+")
    jsonFile.seek(-3, 2)  # Go insert point to add the last row
    if jsonFile.read(1) != '[':
        # not the first item
        jsonFile.write(',')
    newRow = {}
    newRow['Time'] = datetime.today()

    # insert something like this into the file:
    # {"c":[{"v":"Date(2012,8,26,0,1,0)"},{"v":18.96},{"v":19.0},null,{"v":19.94},{"v":19.6},null]},
    jsonFile.write("{\"c\":[")
    now = datetime.now()
    jsonFile.write("{{\"v\":\"Date({y},{M},{d},{h},{m},{s})\"}},".format(
            y=now.year, M=(now.month - 1), d=now.day, h=now.hour, m=now.minute, s=now.second))
    if row['BeerTemp'] is None:
        jsonFile.write("null,")
    else:
        jsonFile.write("{\"v\":" + str(row['BeerTemp']) + "},")

    if row['BeerSet'] is None:
        jsonFile.write("null,")
    else:
        jsonFile.write("{\"v\":" + str(row['BeerSet']) + "},")

    if row['BeerAnn'] is None:
        jsonFile.write("null,")
    else:
        jsonFile.write("{\"v\":\"" + str(row['BeerAnn']) + "\"},")

    if row['FridgeTemp'] is None:
        jsonFile.write("null,")
    else:
        jsonFile.write("{\"v\":" + str(row['FridgeTemp']) + "},")

    if row['FridgeSet'] is None:
        jsonFile.write("null,")
    else:
        jsonFile.write("{\"v\":" + str(row['FridgeSet']) + "},")

    if row['FridgeAnn'] is None:
        jsonFile.write("null")
    else:
        jsonFile.write("{\"v\":\"" + str(row['FridgeAnn']) + "\"}")

    # rewrite end of json file
    jsonFile.write("]}]}")
    jsonFile.close()


def newEmptyFile(jsonFileName):
    jsonFile = open(jsonFileName, "w")
    jsonFile.write("{" + jsonCols + ",\"rows\":[]}")
    jsonFile.close()