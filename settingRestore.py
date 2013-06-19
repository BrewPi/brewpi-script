keys_0_1_x_to_0_2_0 = [{'key': "mode", 'validAliases': ["mode"]},
                       {'key': "beerSet", 'validAliases': ["beerSet"]},
                       {'key': "fridgeSet", 'validAliases': ["fridgeSet"]},
                       {'key': "heatEst", 'validAliases': ["heatEst"]},
                       {'key': "coolEst", 'validAliases': ["coolEst"]},
                       {'key': "tempFormat", 'validAliases': ["tempFormat"]},
                       {'key': "tempSetMin", 'validAliases': ["tempSetMin"]},
                       {'key': "tempSetMax", 'validAliases': ["tempSetMax"]},
                       {'key': "pidMax", 'validAliases': ["pidMax"]},
                       {'key': "Kp", 'validAliases': ["Kp"]},
                       {'key': "Ki", 'validAliases': ["Ki"]},
                       {'key': "Kd", 'validAliases': ["Kd"]},
                       {'key': "iMaxErr", 'validAliases': ["iMaxErr"]},
                       {'key': "idleRangeH", 'validAliases': ["idleRangeH"]},
                       {'key': "idleRangeL", 'validAliases': ["idleRangeL"]},
                       {'key': "heatTargetH", 'validAliases': ["heatTargetH"]},
                       {'key': "heatTargetL", 'validAliases': ["heatTargetL"]},
                       {'key': "coolTargetH", 'validAliases': ["coolTargetH"]},
                       {'key': "coolTargetL", 'validAliases': ["coolTargetL"]},
                       {'key': "maxHeatTimeForEst", 'validAliases': ["maxHeatTimeForEst"]},
                       {'key': "maxCoolTimeForEst", 'validAliases': ["maxCoolTimeForEst"]},
                       # Skip filters, these could mess things up when they are in the old format
                       {'key': "fridgeFastFilt", 'validAliases': []},
                       {'key': "fridgeSlowFilt", 'validAliases': []},
                       {'key': "fridgeSlopeFilt", 'validAliases': []},
                       {'key': "beerFastFilt", 'validAliases': []},
                       {'key': "beerSlowFilt", 'validAliases': []},
                       {'key': "beerSlopeFilt", 'validAliases': []},
                       {'key': "lah", 'validAliases': ["lah"]},
                       {'key': "hs", 'validAliases': ["hs"]}]

keys_0_2_0_to_0_2_0 = [{'key': "mode", 'validAliases': ["mode"]},
                       {'key': "beerSet", 'validAliases': ["beerSet"]},
                       {'key': "fridgeSet", 'validAliases': ["fridgeSet"]},
                       {'key': "heatEst", 'validAliases': ["heatEst"]},
                       {'key': "coolEst", 'validAliases': ["coolEst"]},
                       {'key': "tempFormat", 'validAliases': ["tempFormat"]},
                       {'key': "tempSetMin", 'validAliases': ["tempSetMin"]},
                       {'key': "tempSetMax", 'validAliases': ["tempSetMax"]},
                       {'key': "pidMax", 'validAliases': ["pidMax"]},
                       {'key': "Kp", 'validAliases': ["Kp"]},
                       {'key': "Ki", 'validAliases': ["Ki"]},
                       {'key': "Kd", 'validAliases': ["Kd"]},
                       {'key': "iMaxErr", 'validAliases': ["iMaxErr"]},
                       {'key': "idleRangeH", 'validAliases': ["idleRangeH"]},
                       {'key': "idleRangeL", 'validAliases': ["idleRangeL"]},
                       {'key': "heatTargetH", 'validAliases': ["heatTargetH"]},
                       {'key': "heatTargetL", 'validAliases': ["heatTargetL"]},
                       {'key': "coolTargetH", 'validAliases': ["coolTargetH"]},
                       {'key': "coolTargetL", 'validAliases': ["coolTargetL"]},
                       {'key': "maxHeatTimeForEst", 'validAliases': ["maxHeatTimeForEst"]},
                       {'key': "maxCoolTimeForEst", 'validAliases': ["maxCoolTimeForEst"]},
                       {'key': "fridgeFastFilt", 'validAliases': ["fridgeFastFilt"]},
                       {'key': "fridgeSlowFilt", 'validAliases': ["fridgeSlowFilt"]},
                       {'key': "fridgeSlopeFilt", 'validAliases': ["fridgeSlopeFilt"]},
                       {'key': "beerFastFilt", 'validAliases': ["beerFastFilt"]},
                       {'key': "beerSlowFilt", 'validAliases': ["beerSlowFilt"]},
                       {'key': "beerSlopeFilt", 'validAliases': ["beerSlopeFilt"]},
                       {'key': "lah", 'validAliases': ["lah"]},
                       {'key': "hs", 'validAliases': ["hs"]}]


def getAliases(restoreDict, key):
	for keyDict in restoreDict:
		if keyDict['key'] == key:
			return keyDict['validAliases']
	return []

ccNew = {"tempFormat":"C","tempSetMin": 1.0,"tempSetMax": 30.0,"Kp": 20.000,"Ki": 0.600,"Kd":-3.000,"iMaxErr": 0.500,"idleRangeH": 1.000,"idleRangeL":-1.000,"heatTargetH": 0.301,"heatTargetL":-0.199,"coolTargetH": 0.199,"coolTargetL":-0.301,"maxHeatTimeForEst":"600","maxCoolTimeForEst":"1200","fridgeFastFilt":"1","fridgeSlowFilt":"4","fridgeSlopeFilt":"3","beerFastFilt":"3","beerSlowFilt":"5","beerSlopeFilt":"4"}
ccOld = {"tempFormat":"C","tempSetMin": 1.0,"tempSetMax": 30.0,"Kp": 20.000,"Ki": 0.600,"Kd":-3.000,"iMaxErr": 0.500,"idleRangeH": 1.000,"idleRangeL":-1.000,"heatTargetH": 0.301,"heatTargetL":-0.199,"coolTargetH": 0.199,"coolTargetL":-0.301,"maxHeatTimeForEst":"600","maxCoolTimeForEst":"1200","fridgeFastFilt":"1","fridgeSlowFilt":"4","fridgeSlopeFilt":"3","beerFastFilt":"3","beerSlowFilt":"5","beerSlopeFilt":"4"}
csNew = {"mode":"b","beerSet": 20.00,"fridgeSet": 1.00,"heatEst": 0.199,"coolEst": 5.000}
csOld = {"mode":"b","beerSet": 20.00,"fridgeSet": 1.00,"heatEst": 0.199,"coolEst": 5.000}
settingsRestoreLookupDict = keys_0_1_x_to_0_2_0
