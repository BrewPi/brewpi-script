# Copyright 2013 BrewPi
# This file is part of BrewPi.

# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BrewPi.  If not, see <http://www.gnu.org/licenses/>.

restoreOrder = ("tempFormat", "tempSetMin", "tempSetMax",  # it is critical that these are applied first
                "pidMax", "Kp", "Ki", "Kd", "iMaxErr",
                "idleRangeH", "idleRangeL", "heatTargetH", "heatTargetL", "coolTargetH", "coolTargetL",
                "maxHeatTimeForEst", "maxCoolTimeForEst",
                "fridgeFastFilt", "fridgeSlowFilt", "fridgeSlopeFilt", "beerFastFilt", "beerSlowFilt",
                "beerSlopeFilt", "lah", "hs", "heatEst", "coolEst", "mode", "fridgeSet", "beerSet")

keys_0_1_x_to_0_2_x = [{'key': "mode", 'validAliases': ["mode"]},
                       {'key': "beerSet", 'validAliases': ["beerSet"]},
                       {'key': "fridgeSet", 'validAliases': ["fridgeSet"]},
                       {'key': "heatEst", 'validAliases': ["heatEst"]},
                       {'key': "coolEst", 'validAliases': ["coolEst"]},
                       {'key': "tempFormat", 'validAliases': ["tempFormat"]},
                       {'key': "tempSetMin", 'validAliases': ["tempSetMin"]},
                       {'key': "tempSetMax", 'validAliases': ["tempSetMax"]},
                       {'key': "pidMax", 'validAliases': []},
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

keys_0_2_x_to_0_2_0 = [{'key': "mode", 'validAliases': ["mode"]},
                       {'key': "beerSet", 'validAliases': ["beerSet"]},
                       {'key': "fridgeSet", 'validAliases': ["fridgeSet"]},
                       {'key': "heatEst", 'validAliases': ["heatEst"]},
                       {'key': "coolEst", 'validAliases': ["coolEst"]},
                       {'key': "tempFormat", 'validAliases': ["tempFormat"]},
                       {'key': "tempSetMin", 'validAliases': ["tempSetMin"]},
                       {'key': "tempSetMax", 'validAliases': ["tempSetMax"]},
                       {'key': "pidMax", 'validAliases': []},
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

keys_0_2_x_to_0_2_2 = [{'key': "mode", 'validAliases': ["mode"]},
                       {'key': "beerSet", 'validAliases': ["beerSet"]},
                       {'key': "fridgeSet", 'validAliases': ["fridgeSet"]},
                       {'key': "heatEst", 'validAliases': ["heatEst"]},
                       {'key': "coolEst", 'validAliases': ["coolEst"]},
                       {'key': "tempFormat", 'validAliases': ["tempFormat"]},
                       {'key': "tempSetMin", 'validAliases': ["tempSetMin"]},
                       {'key': "tempSetMax", 'validAliases': ["tempSetMax"]},
                       {'key': "pidMax", 'validAliases': []},
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
                       {'key': "beerSlowFilt", 'validAliases': []},
                       {'key': "beerSlopeFilt", 'validAliases': []},
                       {'key': "lah", 'validAliases': ["lah"]},
                       {'key': "hs", 'validAliases': ["hs"]}]

keys_0_2_x_to_0_2_1 = keys_0_2_x_to_0_2_2

keys_0_2_x_to_0_2_3 = [{'key': "mode", 'validAliases': ["mode"]},
                       {'key': "beerSet", 'validAliases': ["beerSet"]},
                       {'key': "fridgeSet", 'validAliases': ["fridgeSet"]},
                       {'key': "heatEst", 'validAliases': ["heatEst"]},
                       {'key': "coolEst", 'validAliases': ["coolEst"]},
                       {'key': "tempFormat", 'validAliases': ["tempFormat"]},
                       {'key': "tempSetMin", 'validAliases': ["tempSetMin"]},
                       {'key': "tempSetMax", 'validAliases': ["tempSetMax"]},
                       {'key': "pidMax", 'validAliases': []},
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
                       {'key': "beerSlowFilt", 'validAliases': []},
                       {'key': "beerSlopeFilt", 'validAliases': []},
                       {'key': "lah", 'validAliases': ["lah"]},
                       {'key': "hs", 'validAliases': ["hs"]}]

keys_0_2_x_to_0_2_4 = [{'key': "mode", 'validAliases': ["mode"]},
                       {'key': "beerSet", 'validAliases': ["beerSet"]},
                       {'key': "fridgeSet", 'validAliases': ["fridgeSet"]},
                       {'key': "heatEst", 'validAliases': ["heatEst"]},
                       {'key': "coolEst", 'validAliases': ["coolEst"]},
                       {'key': "tempFormat", 'validAliases': ["tempFormat"]},
                       {'key': "tempSetMin", 'validAliases': ["tempSetMin"]},
                       {'key': "tempSetMax", 'validAliases': ["tempSetMax"]},
                       {'key': "pidMax", 'validAliases': []},
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
                       {'key': "beerSlowFilt", 'validAliases': []},
                       {'key': "beerSlopeFilt", 'validAliases': []},
                       {'key': "lah", 'validAliases': ["lah"]},
                       {'key': "hs", 'validAliases': ["hs"]}]

keys_0_2_3_to_0_2_4 = [{'key': "mode", 'validAliases': ["mode"]},
                       {'key': "beerSet", 'validAliases': ["beerSet"]},
                       {'key': "fridgeSet", 'validAliases': ["fridgeSet"]},
                       {'key': "heatEst", 'validAliases': ["heatEst"]},
                       {'key': "coolEst", 'validAliases': ["coolEst"]},
                       {'key': "tempFormat", 'validAliases': ["tempFormat"]},
                       {'key': "tempSetMin", 'validAliases': ["tempSetMin"]},
                       {'key': "tempSetMax", 'validAliases': ["tempSetMax"]},
                       {'key': "pidMax", 'validAliases': []},
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

# defaults, will be overwritten
ccNew = {"tempFormat": "C", "tempSetMin": 1.0, "tempSetMax": 30.0, "pidMax": 10.0, "Kp": 5.000, "Ki": 0.25, "Kd": -1.500,
         "iMaxErr": 0.500, "idleRangeH": 1.000, "idleRangeL": -1.000, "heatTargetH": 0.301, "heatTargetL": -0.199,
         "coolTargetH": 0.199, "coolTargetL": -0.301, "maxHeatTimeForEst": "600", "maxCoolTimeForEst": "1200",
         "fridgeFastFilt": "1", "fridgeSlowFilt": "4", "fridgeSlopeFilt": "3", "beerFastFilt": "3", "beerSlowFilt": "5",
         "beerSlopeFilt": "4"}
ccOld = {"tempFormat": "C", "tempSetMin": 1.0, "tempSetMax": 30.0, "pidMax": 10.0, "Kp": 5.000, "Ki": 0.25, "Kd": -1.500,
         "iMaxErr": 0.500, "idleRangeH": 1.000, "idleRangeL": -1.000, "heatTargetH": 0.301, "heatTargetL": -0.199,
         "coolTargetH": 0.199, "coolTargetL": -0.301, "maxHeatTimeForEst": "600", "maxCoolTimeForEst": "1200",
         "fridgeFastFilt": "1", "fridgeSlowFilt": "4", "fridgeSlopeFilt": "3", "beerFastFilt": "3", "beerSlowFilt": "5",
         "beerSlopeFilt": "4"}
csNew = {"mode": "b", "beerSet": 20.00, "fridgeSet": 1.00, "heatEst": 0.199, "coolEst": 5.000}
csOld = {"mode": "b", "beerSet": 20.00, "fridgeSet": 1.00, "heatEst": 0.199, "coolEst": 5.000}
settingsRestoreLookupDict = keys_0_1_x_to_0_2_x
