# MeteorFinder
Detection of Meteoroid Falls from NEXRAD Radar Archives   
ver 0.1

Benjamin Miller <benjamin.g.miller@utexas.edu>  
The University of Texas at Austin 

02/01/2019

---

## 1. SUMMARY

This algorithm searches the NOAA NEXRAD Level II Doppler Radar archive for phenomena indicating meteoroid falls.  For a given set of dates, archive files from across all available radar sites are retrieved \[1] and unwrapped using the Python ARM Radar Toolkit by \[2].  Latitude/longitude/altitude data is returned for all detections.  The original problem was motivated by \[3], and was developed using NEXRAD data for West, TX on 15 Feb, 2009.  The current algorithm uses radial velocity and spectral width data, with edge detection software in *Locator.py* by \[4].

> \[1] Staniewicz, S., Keh, R. (2018). Maual_Input_Scraper.py. The University of Texas at Austin
>
> \[2] Helmus, J.J. & Collis, S.M., (2016). The Python ARM Radar Toolkit (Py-ART), a Library for Working with Weather Radar Data in the Python Programming Language. Journal of Open Research Software. 4(1), p.e25. DOI: http://doi.org/10.5334/jors.119
>
> \[3] Fries, M. & Fries, J., (2010). Doppler Weather Radar as a Meteorite Recovery Tool. Meteoritics & Planetary Sciences 45, Nr. 9, 1476-1487. DOI: 10.1111/j.1945-5100.2010.01115.x 
>
> \[4] Henriques, J., (2010). Fast Edges of a Color Image: coloredges.m v.1.1.0.0. Mathworks File Exchange

---

## 2. REQUIREMENTS

Python (3.6.6)  
Py-ART (1.9.2)  
NumPy (1.15.4)  
SciPy (1.1.0)  
matplotlib (3.0.2)  
netCDF4 (1.4.2)  
opencv (3.4.4)  
bs4 (4.7.1) 
requests (2.21.0)

Tested on Windows 7
Tested on Spyder IDE; known issues with PyCharm

---

## 3. VERSION NOTES

v0.1: Initial release.  KFWS fall confirmed with 1 ID at 16:53:32, no false positves over the full date 2/15/2009.

v0.2: KLRX fall confirmed in KnownFalls.txt, 2 ID's identified for previously known KFWS event.  Outputs include latitude/longitude/altitude for each ID. 

---

## 4. OPERATION

The "Master_MeteorFinder.py" function provides a simple interface for selecting the following variables.  For a demonstration, please see the *Files* folder 

- "dates": Interval of start/end dates as an int array \[yyyy,m,d,yyyy,m,d] \(default \[2009, 2, 15, 2009, 2, 16]).  Options: 1992-present  
- "times": Interval of start/end times for each day as an int array \[hhmmss, hhmmss] \(default \[000000,245960]).  Note that zeros cannot precede numbers, and thus may be excluded.  
- "stations": String list of 4-letter codes or 'all' \(default \['KFWS']).  Options: see FullStationList.txt.  
- "colorCutoff": Uint8 cutoff for valid color-coded measurements \(default 100)   
- "edgeIntensity": Float cutoff for intesity of velocity edges \(default 15)   
- "sizeFilter": Scalar ratio of image area to blob area for trimming small bodies  \(default 1e-4)  
- "circularityFilter": Scalar ratio of blob area to enclosing circle area for trimming anomolous bodies \(default 0.3)  
- "fillFilter": Precentage of velocity phenomena which must contain high velocity gradients, filtering out trivial phenomena.  \(default 50) 

When running the program, the algorithm will fetch the NEXRAD data corresponding to the selected dates, times, and WGS-88D sites.  The console will display a record of the current data and site, followed by updates on the current time.  For each time instant, the console will display the unwrapped altitude cut for reasurrance.  An alert will be displayed whenever a fall phenomena is detected, indicating the altitude cut of interest, and the respective data images will be saved for manual analysis in the site code folder.  See the *Example Detection* folder for the results of the West, TX event (KFWS 02/15/2009 16:53:32).  Other known falls are stored in the *KnownFalls.txt* file.  

---

## 5. SUBPROCESSES

### GetArchive.py 
This primary subprocess controls the retrieval of the NEXRAD archive files via the bs4 package.  The main function organizes folder instantiation and sorting.  The called subfunctions "save_links" records the entire archive contents for calling by "download_link", which will filter relevent times before calling the Unwrapper.  Additional subfunctions download the respective files from the recorded links and format date ranges.  The colormaps for the Unwrapper are also instantiated for optimization.         

### Unwrapper.py
This secondary subprocess opens the retrieved radar image set and formats the relevant data by scan order for further analysis.  The private graphing methods of the py-art package are modified and passed into custom matplotlib figures for high resolution image-format data, and these data are handed to the Locator as bgr image lists.  This subprocess runs for each time-specific archive retrieved by the parent process, and the level of scans will change based on the operation of the local radar station at any given time.  If falls are identified, the latitude/longitude/altitude positions are calculated by Py-ART's azimuthal equidistant projection.        

### Locator.py
This tertiary subprocess finally looks for phenomena of interest within the retrieved data.  In this process, velocity images are analyzed first as they are robust to false-positives.  The color content and radial distance from the station are used as preliminary image masks.  Then, color gradients are calculated and trivial solutions are removed.  Using contour-based object detection, remaining gradient data is filtered based on area, shape, and edge density.  The altidude cuts are collapsed prior to identification, exluding the lowermost quarter cuts.  Valid targets are added to a candidate list, and the spectrum width algorithm runs.  For spectrum width processing, the preliminary filtering is followed directly by object detection, applying area, shape, and density filters.  If the two data type algorithms result in a single matching scan level candidate, the algorithm loosens detection restrictions and captures all markers present in the spectrum width data.  The respective unprocessed images are saved, and the user is alerted of the altitudes and LLA positions through the Unwrapper.            

	
