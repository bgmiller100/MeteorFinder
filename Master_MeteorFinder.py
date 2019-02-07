# -*- coding: utf-8 -*-
"""
Created on Thu Jan 17 12:58:28 2019
ver 1.0 as of Feb 01, 2019

See README for details

@author: Benjamin Miller 
"""

from GetArchive import runFunction as fetchFile 

#SEE README FOR OPERATING INSTRUCTIONS
#West,TX Meteorite Fall: KFWS 2/15/2009 16:53:32

# USER INPUT
dates = [2009, 2, 15, 2009, 2, 16] 
times = [165000, 165500] 
stations = ['KFWS']

# ADVANCED INPUT
colorCutoff = 100
edgeIntensity = 15
sizeFilter = 1*(10**-4)
circularityFilter = 0.3
fillFilter = 50

#run program
fetchFile(dates,times, stations, colorCutoff, edgeIntensity, sizeFilter , colorCutoff, circularityFilter, fillFilter)
print('END') 







