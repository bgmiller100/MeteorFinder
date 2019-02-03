# -*- coding: utf-8 -*-
"""
Created on Sun Dec 30 16:05:05 2018

@author: Ben
"""
#, cutoff, edgeFilter, areaFraction
import cv2
import os.path as pth
import numpy as np


def DetectMeteors(pyRadarData, cutoff, edgeFilter, areaFraction, colorIntensity, circRatio, fillFilt, name):
    
    #Instantiate storage of contours for object detection
    contourDict = {}
    contourDict['vel'] = []
    contourDict['spw'] = []
    
    #Set adaptive area filters
    adaptArea = (np.size(pyRadarData['velocity'][0], axis=0) * 
        np.size(pyRadarData['velocity'][0], axis=1))
    size_filter = np.array([adaptArea, adaptArea*5])*areaFraction
   
    #Instantiate velocity processing
    countim=0
    velKeys = 0
    velIdentity = [];    
    for x in pyRadarData['velocity']:
        img = np.copy(x)
        
        #Filter image color content 
        gFilt = cv2.inRange(img, np.array([0,colorIntensity,0]), np.array([255,255,255]))
        rFilt = cv2.inRange(img, np.array([0,0,colorIntensity]), np.array([255,255,255]))
        imgMask = (gFilt+rFilt)>0
        del gFilt, rFilt
        #Filter false-positives close to station
        masksize = 200
        circ = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (masksize,masksize))
        overlay = np.zeros(imgMask.shape)
        lo = 900 - np.int_(masksize/2)
        hi = 900 + np.int_(masksize/2)
        overlay[lo:hi,lo:hi] = circ
        overlay = overlay.astype(np.bool_, copy=False)
        imgMask[overlay] = 0
        del circ, overlay
        #Apply masks to image 
        imgOrig = np.copy(img)
        img[:][:][:] = 0
        imgMask = np.expand_dims(imgMask,axis=2)
        imgMask = np.tile(imgMask,(1,1,3))
        img[imgMask] = imgOrig[imgMask]
        img[:][:][0] = 0
        img = img.astype(np.float32, copy=False)
        img = img / 255
        del imgOrig, imgMask
        
        #Calculate color (ie velocity) gradients
        yfilter = np.array([[1.,2.,1.],[0.,0.,0.],[-1.,-2.,-1.]])
        xfilter = np.transpose(yfilter)
        gx = cv2.filter2D(img[:,:,1],-1,xfilter)
        rx = cv2.filter2D(img[:,:,2],-1,xfilter)
        gy = cv2.filter2D(img[:,:,1],-1,yfilter)
        ry = cv2.filter2D(img[:,:,2],-1,yfilter)
        Jx = gx**2 + rx**2 
        Jy = gy**2 + ry**2
        Jxy = gx*gy + rx*ry
        D = np.sqrt(np.abs(Jx**2 - 2*Jx*Jy + Jy**2 + 4*Jxy**2)+1)
        e1 = (Jx + Jy + D) / 2
        img = np.sqrt(e1* 100) 
        del gx,rx,gy,ry,Jx,Jy,Jxy,D,e1
        
        #Filter trivial gradients
        kernel = np.ones((2,2),np.uint8)
        img = img.astype(np.uint8, copy=False)
        img = cv2.threshold(img,edgeFilter,255,cv2.THRESH_BINARY)[1]
        img = cv2.erode(img, kernel)
        img = cv2.dilate(img, kernel)
        #Optional printing:
        #imgprint = np.copy(img)
        #imgprint = np.expand_dims(imgprint,axis=2)
        #imgprint = np.tile(imgprint,(1,1,3))
        #nametag = pth.splitext(name)[0]
        #cv2.imwrite(nametag+'_edgefilt'+str(countim)+'.png', imgprint*20)
        
        #Instantiate object detection 
        img = img*15
        img = img.astype(np.uint8, copy=False)
        im2,contours,hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contourfix = [];
        for cnt in contours:
            #Area-based filtering
            area = cv2.contourArea(cnt)
            #Shape-based filtering
            (x,y), radius = cv2.minEnclosingCircle(cnt)
            aspect = area/(np.pi*radius**2)
            #Density-based filtering
            x,y,w,h = cv2.boundingRect(cnt)
            imageROI = img[y:y+h,x:x+w]
            total = cv2.countNonZero(imageROI) - cv2.arcLength(cnt,True)
            if area>0:
                filled = (total/area)*100
            else:
                filled=0 
            #Apply filters to object set
            if (area>=size_filter[0]) & (aspect>circRatio) & (filled>fillFilt):
                contourfix.append(cnt)
                
        #Record data for candidate scans
        if len(contourfix)>0:
            velIdentity.append(countim)
            velKeys = velKeys + len(contourfix)
            contourDict['vel'].append(contourfix)
        countim = countim+1
   
    #Instantiate spectral width processing
    countim = 0
    spwKeys = 0
    spwIdentity = []; 
    #Run where only trustworthy data
    if  velKeys==1:
        for x in pyRadarData['spectrum_width']:
            
            #Filter image color content 
            img = np.copy(x)
            gFilt = cv2.inRange(img, np.array([0,colorIntensity,0]), np.array([255,255,255]))
            rFilt = cv2.inRange(img, np.array([0,0,colorIntensity]), np.array([255,255,255]))
            imgMask = (gFilt+rFilt)>0
            del gFilt,rFilt
            #Filter false-positives close to station
            masksize = 200
            circ = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (masksize,masksize))
            overlay = np.zeros(imgMask.shape)
            lo = 900 - np.int_(masksize/2)
            hi = 900 + np.int_(masksize/2)
            overlay[lo:hi,lo:hi] = circ
            overlay = overlay.astype(np.bool_, copy=False)
            imgMask[overlay] = 0   
            del circ, overlay
            #Apply mask to image
            imgOrig = np.copy(img)
            img[:][:][:] = 0
            imgMask = np.expand_dims(imgMask,axis=2)
            imgMask = np.tile(imgMask,(1,1,3))
            img[imgMask] = imgOrig[imgMask]
            img[:][:][0] = 0
            img = np.sum(img,axis=2)
            img = img.astype(np.uint8, copy=False)
            del imgOrig, imgMask

            #Instantiate object detection 
            img = img.astype(np.uint8, copy=False)
            img = cv2.threshold(img,cutoff,255,cv2.THRESH_BINARY)[1]
            img = img.astype(np.uint8, copy=False)
            im2,contours,hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contourfix = [];
            for cnt in contours:
                #Area-based filtering
                area = cv2.contourArea(cnt)
                #Shape-based filtering
                (x,y), radius = cv2.minEnclosingCircle(cnt)
                aspect = area/(np.pi*radius**2)
                if (area>=size_filter[0]) & (aspect>circRatio):
                    contourfix.append(cnt)  
                    
            #Record data for candidate scans
            if len(contourfix)>0: 
                spwKeys = spwKeys + len(contourfix)
                contourDict['spw'].append(contourfix)
                spwIdentity.append(countim)
            countim = countim+1
         
    #Check candidate matches for robustness
    if spwKeys==1:
        idMatch = list(set(velIdentity).intersection(spwIdentity))
        countim = 0
        for lev in idMatch:  
            #Instantiate plot data           
            nametag = pth.splitext(name)[0]
            velCopy = pyRadarData['velocity'][lev].astype(np.uint8, copy=True)
            spwCopy = pyRadarData['spectrum_width'][lev].astype(np.uint8, copy=True)
            #Mark detections on data images
            velIm = cv2.drawContours(velCopy, contourDict['vel'][countim], -1, [255, 0, 0], thickness = 2)
            spwIm = cv2.drawContours(spwCopy, contourDict['spw'][countim], -1, [255, 0, 0], thickness = 2)
            #Record data images
            cv2.imwrite(nametag+'_VEL'+str(lev)+'.png', velIm)            
            cv2.imwrite(nametag+'_SPW'+str(lev)+'.png', spwIm)
            countim=countim+1
    else:
        idMatch = []
        
    return len(idMatch), idMatch

