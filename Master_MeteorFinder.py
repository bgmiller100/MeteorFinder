# -*- coding: utf-8 -*-
"""
Created on Thu Jan 17 12:58:28 2019

@author: Ben
"""

from GetArchive import runFunction as fetchFile 

#SEE READ_ME.TXT FOR OPERATING INSTRUCTIONS
#West,TX Meteorite Fall: KFWS 2/15/2009 16:53:32

#User Input
dates = [2009, 2, 15, 2009, 2, 16] 
times = [000000, 235960] 
stations = ['KFWS']
colorCutoff = 100
edgeIntensity = 15
sizeFilter = 1*(10**-4)
circularityFilter = 0.3
fillFilter = 50

#Run Program 
fetchFile(dates,times, stations, colorCutoff, edgeIntensity, sizeFilter , colorCutoff, circularityFilter, fillFilter)
print('END') 







