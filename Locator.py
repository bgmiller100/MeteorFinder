# -*- coding: utf-8 -*-
"""
Created on Sun Dec 30 16:05:05 2018

@author: Ben
"""
#, colorCutoff, edgeIntensity, sizeFilter
import cv2
import os.path as pth
import numpy as np


def DetectMeteors(pyRadarData, colorCutoff, edgeIntensity, sizeFilter, colorIntensity, circularityFilter, fillFilter, name):
    
    #Instantiate storage of contours for object detection
    contourDict = {}
    contourDict['vel'] = []
    contourDict['spw'] = []
    edgeArray = []
    
    #Set adaptive area filters
    adaptArea = (np.size(pyRadarData['velocity'][0], axis=0) * 
        np.size(pyRadarData['velocity'][0], axis=1))
    size_filter = np.array([adaptArea, adaptArea*5])*sizeFilter
    scanHt = len(pyRadarData['velocity'])
   
    #Instantiate velocity processing
    countim=0
    velKeys = 0
    velCounter = 0;
    for x in pyRadarData['velocity']:
        if velCounter<scanHt/4:
            velCounter = velCounter + 1
            continue
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
        img = np.sqrt(e1*20) 
        del gx,rx,gy,ry,Jx,Jy,Jxy,D,e1
        img = img.astype(np.uint8, copy=False)
        img = cv2.threshold(img,edgeIntensity,255,cv2.THRESH_BINARY)[1]
        edgeArray.append(img)
        velCounter = velCounter + 1
        
    #Collapse data    
    edgeShape = np.shape(edgeArray[0]);
    edgeSum = np.zeros((edgeShape[0],edgeShape[1]))
    for img in edgeArray:
        edgeSum = edgeSum+img
        
    #Optional 
    #Filter trivial gradients
        #kernel = np.ones((2,2),np.uint8)
    #Will need to raise
        #img = cv2.erode(img, kernel)
        #img = cv2.dilate(img, kernel)
    
    #Instantiate object detection 
    img = edgeSum #img*15
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
        if (area>=size_filter[0]) & (aspect>circularityFilter) & (filled>fillFilter):
            contourfix.append(cnt)
            
    #Print scan 
    imgprint = np.copy(edgeSum)
    imgprint = np.expand_dims(imgprint,axis=2)
    imgprint = np.tile(imgprint,(1,1,3))
    nametag = pth.splitext(name)[0]
    velIm = cv2.drawContours(imgprint, contourfix, -1, [255, 0, 0], thickness = 2)
    nametag = pth.splitext(name)[0]
    cv2.imwrite(nametag+'_VEL_DETECTIONS'+'.png', velIm)
    
    #Record data for candidate scans
    if len(contourfix)>0:
        velKeys = velKeys + len(contourfix)
        contourDict['vel'].append(contourfix)
        #print('\n   vel detection count:'+str(velKeys))

    countim = countim+1
    
    ######################################################################
    ######################################################################
    ######################################################################
    
    #Instantiate spectral width processing
    countim = 0
    spwKeys = 0
    spwArray=[];
    spwCounter=0
    #Run where only trustworthy data
    if  velKeys==1:
        for x in pyRadarData['spectrum_width']:
            if spwCounter<scanHt/4:
                spwCounter = spwCounter+1
                continue
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
            spwArray.append(img)
            spwCounter = spwCounter + 1
        
    #Collapse data
    spwShape = np.shape(edgeArray[0]);
    spwSum = np.zeros((spwShape[0],spwShape[1]))
    for img in spwArray:
        spwSum = spwSum+img
    img = np.copy(spwSum)    

    #Instantiate object detection 
    img = img.astype(np.uint8, copy=False)
    img = cv2.threshold(img,colorCutoff,255,cv2.THRESH_BINARY)[1]
    img = img.astype(np.uint8, copy=False)
    #cv2.imwrite('check.png', img*100)

    im2,contours,hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contourfix = [];
    for cnt in contours:
        #Area-based filtering
        area = cv2.contourArea(cnt)
        #Shape-based filtering
        (x,y), radius = cv2.minEnclosingCircle(cnt)
        aspect = area/(np.pi*radius**2)
        #Anti-weather density-based filtering
        if (area>=size_filter[0]) & (aspect>circularityFilter):
            x,y,w,h = cv2.boundingRect(cnt)
            imageROI = img[y-(1*h):y+(2*h),x-(1*w):x+(2*w)]
            total = cv2.countNonZero(imageROI) - cv2.arcLength(cnt,True)
            area = 3*h*3*w
            if (total/area)<.1:                          
                contourfix.append(cnt) 
            
    #Record data for candidate scans
    if len(contourfix)>0: 
        spwKeys = spwKeys + len(contourfix)
        contourDict['spw'].append(contourfix)
        #print('   spw detection count:'+str(spwKeys))

    countim = countim+1
        
    #Print data
    imgprint = np.copy(spwSum)
    imgprint = np.expand_dims(imgprint,axis=2)
    imgprint = np.tile(imgprint,(1,1,3))
    nametag = pth.splitext(name)[0]
    velIm = cv2.drawContours(imgprint, contourfix, -1, [255, 0, 0], thickness = 2)
    nametag = pth.splitext(name)[0]
    cv2.imwrite(nametag+'_SPW_DETECTIONS'+'.png', velIm)
         
    ##########################################################################
    ##########################################################################
    ##########################################################################
    
    
    #Check candidate matches for robustness
    if spwKeys==1:
        #Density-based analysis for altitude identification 
        nullArray = np.zeros((spwShape[0],spwShape[1]))
        velIdentity = [];
        velLoosen = []
        #Loosen Vel - To Be Incorporated
        velCounter = np.ceil(scanHt/4)
        for x in edgeArray:
            img = np.copy(nullArray) + np.copy(x)
            img = img.astype(np.uint8)
            im2,contours,hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                (x,y), radius = cv2.minEnclosingCircle(cnt)
                aspect = area/(np.pi*radius**2)
                x,y,w,h = cv2.boundingRect(cnt)
                imageROI = img[y:y+h,x:x+w]
                total = cv2.countNonZero(imageROI) - cv2.arcLength(cnt,True)
                if area>0:
                    filled = (total/area)*100
                else:
                    filled=0 
                if (area>=size_filter[0]/4) & (aspect>circularityFilter/4) & (filled>fillFilter): #/2 test
                    velIdentity.append(velCounter)
                    velLoosen.append(cnt)
            velCounter = velCounter+1  
            
        #Loosen  Spw  (with adaptable dilation)   
        spwIdentity = [];
        spwLoosen = []
        spwrough=0
        loopCheck = 1
        errorCheck = 1
        while loopCheck==1:
            spwCounter=np.ceil(scanHt/4)
            for x in spwArray:
                #adaptability to loosen 
                img =  np.copy(x)
                img = img.astype(np.uint8)
                img = cv2.threshold(img,colorCutoff,255,cv2.THRESH_BINARY)[1]
                img = img.astype(np.uint8, copy=False)
                #Dilation permits greater capture range 
                dilationScale = 2*errorCheck
                img = cv2.dilate(img, np.ones((dilationScale,dilationScale),np.uint8))
                #cv2.imwrite('spwCheck'+str(spwCounter)+'.png', img)
                #Repeats detection of spectrum width bodies
                im2,contours,hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    (x,y), radius = cv2.minEnclosingCircle(cnt)
                    aspect = area/(np.pi*radius**2)
                    if (area>=size_filter[0]) & (aspect>circularityFilter/errorCheck): #note /errorCheck 
                        x,y,w,h = cv2.boundingRect(cnt)
                        imageROI = img[y-(1*h):y+(2*h),x-(1*w):x+(2*w)]
                        total = cv2.countNonZero(imageROI) - cv2.arcLength(cnt,True)
                        area = 3*h*3*w
                        spwrough = spwrough+1
                        if (total/area)<.1:   
                            spwIdentity.append(spwCounter)
                            spwLoosen.append(cnt) 
                            loopCheck = 0
                            #end loop after detections
                spwCounter = spwCounter + 1 
            errorCheck = errorCheck+1
            if errorCheck>=10:
                #print('loosening loop error')
                break
        #print('   vel loose count:'+str((velIdentity)))
        #print('   spw pre   count:'+str(spwrough))
        #print('   spw loose count:'+str((spwIdentity)))

        #Robustness check
        #idMatch = list(set(velIdentity).intersection(spwIdentity))        
        idMatch = spwIdentity 
        XY = []
        for lev in idMatch:  
            lev = lev.astype(np.uint8)
            #Instantiate plot data           
            nametag = pth.splitext(name)[0]
            velCopy = pyRadarData['velocity'][lev].astype(np.uint8, copy=True)
            spwCopy = pyRadarData['spectrum_width'][lev].astype(np.uint8, copy=True)
            #Mark detections on data images
            velIm = cv2.drawContours(velCopy, spwLoosen[spwIdentity.index(lev)], -1, [255, 0, 0], thickness = 2) #Adjusted for spwIdentity track
            spwIm = cv2.drawContours(spwCopy, spwLoosen[spwIdentity.index(lev)], -1, [255, 0, 0], thickness = 2)
            #Record data images
            cv2.imwrite(nametag+'_VEL'+str(lev)+'.png', velIm)            
            cv2.imwrite(nametag+'_SPW'+str(lev)+'.png', spwIm)
            #Calculate centroid positions
            M = cv2.moments(spwLoosen[spwIdentity.index(lev)])
            dim = np.shape(spwIm)[0]/2
            x = (int(M["m10"] / M["m00"])-dim)*100/dim
            y = (dim-int(M["m01"] / M["m00"]))*100/dim
            XY.append([x,y]) #km from instrument 
            
    else:
        idMatch = []
        XY = []
    return len(idMatch),idMatch, XY

