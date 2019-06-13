# -*- coding: utf-8 -*-

import pyart
import os.path as pth
import os
import matplotlib.pyplot as plt
import numpy as np
import matplotlib 
import gc
import cv2

from Locator import DetectMeteors

def runFunction(filename, response , velMap, spwMap, cutoff, edgeFilter, areaFraction, colorIntensity, circRatio, fillFilt):
    matplotlib.use("agg") 
        
    #Instantiate RadarData dictionary and lists
    RadarData = {}
    RadarData['velocity'] = []
    RadarData['spectrum_width'] = []
    
    #Read in radar archive
    RADAR_NAME = filename;  
    radar = pyart.io.read_nexrad_archive(RADAR_NAME, exclude_fields='reflectivity')
    plotter = pyart.graph.RadarDisplay(radar)
    
    plotter = pyart.graph.RadarDisplay(radar)
    
    #Display iteration scan time 
    pthname = pth.splitext(RADAR_NAME)[0]
    pthname = pth.split(pthname)[1]
    print('Time: '+pthname.split('_')[1]+'\n',end='   ')
    
    for x in range(radar.nsweeps):

        # Instantiate figure
        fig = plt.figure(figsize=(25,25), frameon=False)
        ax = plt.Axes(fig, [0.,0.,1.,1.])
        ax.set_axis_off()
        fig.add_axes(ax)
        plotter.set_limits(xlim=(-150, 150), ylim=(-150, 150), ax=ax)
        #Get velocity data
        vmin, vmax = pyart.graph.common.parse_vmin_vmax(radar, 'velocity', None, None) 
        data = plotter._get_data('velocity', x, mask_tuple=None, filter_transitions=True, gatefilter=None)
        #Check for empty altitude cuts
        if np.any(data)>0:
            xDat, yDat = plotter._get_x_y(x, edges=True, filter_transitions=True)
            data = data*(70/np.max(np.abs(data)))
            #Format data for passing to Locator
            ax.pcolormesh(xDat, yDat, data, vmin=-70, vmax=70, cmap=velMap)
            #NOTE: Color reduces data range, but required for openCV processing,
            #      and may correct later to deeper resolution if necessary.
            fig.canvas.draw()
            img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
            img = img.reshape(fig.canvas.get_width_height()[::1]+(3,))
            img = np.flip(img,axis=2)
            img.setflags(write=1)
            img[np.where((img==[255,255,255]).all(axis=2))] = [0,0,0] 
            #Attatch data to dictionary variable for passing
            RadarData['velocity'].append(img)
            plt.close(fig)
            plt.clf()
            plt.cla()
            gc.collect()
    
            # Instantiate figure 
            fig = plt.figure(figsize=(25,25), frameon=False)
            ax = plt.Axes(fig, [0.,0.,1.,1.])
            ax.set_axis_off()
            fig.add_axes(ax)
            plotter.set_limits(xlim=(-150, 150), ylim=(-150, 150), ax=ax)
            #Get spectrum width data
            vmin, vmax = pyart.graph.common.parse_vmin_vmax(radar, 'spectrum_width', None, None) 
            data = plotter._get_data('spectrum_width', x, mask_tuple=None, filter_transitions=True, gatefilter=None)
            xDat, yDat = plotter._get_x_y(x, edges=True, filter_transitions=True)
            data = data*(30/np.max(data))
            #Format data for passing to Locator
            ax.pcolormesh(xDat, yDat, data, vmin=0, vmax=30, cmap=spwMap)
            fig.canvas.draw()
            img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
            img = img.reshape(fig.canvas.get_width_height()[::1]+(3,))
            img = np.flip(img,axis=2) #convert to bgr
            img.setflags(write=1)
            img[np.where((img==[255,255,255]).all(axis=2))] = [0,0,0] 
            #Attatch data to dictionary variable for passing
            RadarData['spectrum_width'].append(img)
            plt.close(fig)
            plt.clf()
            plt.cla()
            gc.collect()
            
            #Update user on unwrapping progress
            print(str(x)+' ', end='')
            
        #Update for empty data scans
        else:
            plt.close(fig)
            plt.clf()
            plt.cla()
            gc.collect()
            print(str(x)+' ', end='')
            
    #Double-check figure closing
    del img
       
    #Run Locator
    #pyRadarData, cutoff, edgeFilter, areaFraction, colorIntensity, circRatio
    fallCount, fallId, xy= DetectMeteors(RadarData,cutoff, edgeFilter, areaFraction, colorIntensity, circRatio, fillFilt, RADAR_NAME)

    #Update user on any detections and get positions
    if fallCount>0:    
        fallId = list(map(int,fallId))
        print('\n   FALLS DETECTED AT SCAN(S): '+str(fallId))
        lonlat0 = [radar.longitude['data'],radar.latitude['data']]
        lla = []
        for ind, r in enumerate(xy, start=0):
            lon,lat = pyart.core.cartesian_to_geographic_aeqd(r[0],r[1],lonlat0[0],lonlat0[1])
            dist = np.sqrt(np.abs(r[0])**2+np.abs(r[1])**2)
            el = radar.get_elevation(fallId[ind])
            alt = dist*np.tan(el[0]*np.pi/180)
            lla.append([lat.item(),lon.item(),alt])
            print('   LLA:'+str([lat.item(),lon.item(),alt]))

            #Close Unwrapper

    else:
        print('\n', end='')
        os.remove(RADAR_NAME)
                        
                        
