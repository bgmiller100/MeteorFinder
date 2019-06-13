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
#Battle Mountain, NV   : KLRX 8/22/2012 06:

# USER INPUT
dates = [2009, 2, 15, 2009, 2, 16]
times = [0, 230000] 
stations = ['KFWS']

# ADVANCED INPUT, see readme and demo
colorCutoff = 100 
edgeIntensity = 12 #15, to loosen constraint
sizeFilter = 1*(10**-4)
circularityFilter = 0 #0.3, to detect all
fillFilter = 0 #50, to detect all

#run program
fetchFile(dates,times, stations, colorCutoff, edgeIntensity, sizeFilter , colorCutoff, circularityFilter, fillFilter)
print('END') 








