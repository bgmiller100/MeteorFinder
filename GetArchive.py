

import os
import requests
import time
import matplotlib.colors as color
import numpy as np
from bs4 import BeautifulSoup, SoupStrainer
from datetime import timedelta, date
from Unwrapper import runFunction as filterFile 

def make_directory(dirname):
    print('\nMaking directory {}'.format(dirname))
    try:
        os.mkdir(dirname)
    except FileExistsError:
        pass

def save_links(page_url, dirname):
    # Record the data links on the page for this date or read already existing file
    # These will individually be pulled down and saved as files, as well as stored in a list
  
    link_time_num = []
    for i in range(000000,235960):
        q = str(i).zfill(6)
        link_time_num.append(q)
    for i in enumerate(link_time_num): # previously for i in range(0, len(link_time_num)):
        link_file = '{}/data_links.txt'.format(dirname)    
        links = []
        #print('Writing links to {}'.format(link_file))
        response = requests.get(page_url)
        with open(link_file, 'w') as f:
            for link in BeautifulSoup(response.text, 'html.parser', parse_only=SoupStrainer('a')):
                if link.has_attr('href') and ('amazonaws' in link['href']) or any(s in link for s in link_time_num):
                    f.write('{}\n'.format(link['href']))
                    links.append(link['href'])
                    #else:
                        #print("\nThere is no link for this link:\n", link,"\n")
        return links
    
def download_content(link , max_retries=5):
    # Try the url up to 5 times in case some error happens
    # Note: this is somewhat crude, as it will retry no matter what error happened
    num_retries = 0
    response = None
    while num_retries < max_retries:
        try:
            response = requests.get(link)
            break
        except Exception as e:
            print('{} errored {}: {}, retrying.'.format(link, num_retries, e))
            num_retries += 1
            time.sleep(1)

    return response

def write_to_file(filename, response):
    with open(filename, 'wb') as f:
        f.write(response.content)

def download_link(link, dirname, timerange, velMap, spwMap, cutoff, edgeFilter, areaFraction, colorIntensity, circRatio, fillFilt):
    '''Grab the content from a specific radar link and save binary output to a file'''
    namer = link.split('/')[-1]
    if namer.split('.')[1]=='gz':
        if int(namer.split('_')[1]) in range(timerange[0],timerange[1]):
    
            response = download_content(link)
            if not response:
                raise Exception
            # Use last part of the link as the filename (after the final slash)
            # "http://noaa-nexrad-level2.s3.amazonaws.com/2018/01/09/KABR/KABR20180109_000242_V06"
            filename = '{}/{}'.format(dirname, link.split('/')[-1])
            #print('Writing to file {}'.format(filename))
            write_to_file(filename, response)
            # Call the Unwrapper function 
            filterFile(filename, response, velMap, spwMap, cutoff, edgeFilter, areaFraction, colorIntensity, circRatio, fillFilt)

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)
        
def getMaps():
    #Set velocity colormap 
    cmaplist = np.array([[255,0,0],#-70
                         [255,0,0],#-60
                         [210,0,0],#-50
                         [180,0,0],#-40
                         [150,0,0],#-30
                         [115,0,0],#-20
                         [70,40,40],#-10
                         [70,70,70],#0
                         [40,70,40],#10
                         [0,115,0],#20
                         [0,150,0],#30
                         [0,180,0],#40
                         [0,210,0],#50
                         [0,255,0],#60
                         [0,255,0]])/255#70
    cmaplist = np.flip(cmaplist,axis=0)
    velMap = color.LinearSegmentedColormap.from_list('velMap',cmaplist,N=256)
    
    #Set spectrum width colormap
    cmaplist = np.array([[20,20,20],#0
                         [40,40,40],#6
                         [40,150,40],#12 40 150
                         [150,40,40],#18 150 40
                         [150,70,0],#24
                         [255,255,0]])/255#30
    spwMap = color.LinearSegmentedColormap.from_list('spwMap',cmaplist,N=256)
    return velMap, spwMap
    
def runFunction(dateList, timerange, sites, cutoff, edgeFilter, areaFraction, colorIntensity, circRatio, fillFilt):
    #Parse input
    origin_year = dateList[0]
    origin_month = dateList[1] 
    origin_day = dateList[2] 
    end_year = dateList[3]
    end_month = dateList[4] 
    end_day = dateList[5] 
    
    #Generate colormaps
    velMap,spwMap = getMaps()
    
    #Run Main
    try:
        product = 'AAL2' #  Level-II data include the original three meteorological base data quantities: reflectivity, mean radial velocity, and spectrum width,
                        # as well as the dual-polarization base data of differential reflectivity, correlation coefficient, and differential phase.
        start_date = date(origin_year, origin_month, origin_day)
        end_date = date(end_year, end_month, end_day)# date(now.year, now.month, now.day+1)

        for single_date in daterange(start_date, end_date): # --OPTION 2 DOWNLOAD WEATHER DATA FROM THE ORIGIN DATE TILL TODAY (usually run for the first time to download all the files, and then go to OPTION 2)
            dateN = single_date.strftime("%Y %m %d")
            date_arr = [int(s) for s in dateN.split() if s.isdigit()]
            year = date_arr[0]
            month = date_arr[1]
            day = date_arr[2]

            if month < 10: # formats the month to be 01,02,03,...09 for month < 10
                for i in range(1, 10):
                    if month == i:
                        month = '{num:02d}'.format(num=i)
 
            if day < 10: # formats the day variable to be 01,02,03,...09 for day < 10
                for i in range(1, 10): #Having 9 as the max will cause a formatting and link problem, i.e. creating a folder with 07/9/xxxx instead of 07/09/xxxx
                    if day == i:
                        day = '{num:02d}'.format(num=i)

            print("\n----------------------------------------Downloading data as of", str(month) + "/" + str(day) + "/" + str(year),"----------------------------------------")

            '''
            In case of preference of manual input date, use this block of code to get a specific date ONLY 
            
            if manual_entry:
                year = int(input('Please enter a year (YYYY):'))
                if year > now.year or year < 1993:
                    print("Error, year is not in the specified bounds of this year and 1993")
                    exit()
                month = int(input('Please enter a month (MM):'))
                if (month > 12 and month < 1) or (month > now.month and year == now.year):
                    print("Error, month is out of bounds")
                    exit()
                if month < 10:
                    for i in range(1,9):
                        if month == i:
                            month = '{num:02d}'.format(num=i)
                day = int(input('Please enter a day (DD):'))
                if day > 31 or day < 1: 
                    print("Error, day is out of bounds")
                    exit()
                if day < 10:
                    for i in range(1,9):
                        if day == i:
                            day = '{num:02d}'.format(num=i)
            else:
                print('Error, please run again')
                exit()
            '''
            # This is a list of radar sites that have specific end dates and not among the list of "registered" radar sites,
            # usually are considered test sites or deocommissioned sites: they usually start with a T for test sites,
            # the other letters for decomissioned sites

            # DAN1(05/26-2010-11/29/2016), DOP1(05/27/2010-09/30/2016),FOP1(06/09/2010-03/20/2018), KABQ(10/16/2003 - 10/23/2003),
            # KAFD(05/01/2003-05/24/2004), KBTV(03/19/2003-06/16/2003), KDOG(02/27/200-04/23/2004), KERI(01/15/2009-02/15/2017),
            # KILM(11/16/2000-03/13/2001), KJUA(02/27/2009-0826/2016), KLBF(02/01/2009-02/01/2009),KMES(02/23/2004-06/07/2004),
            # KNAW(06/08/2017-08/16/2018),LORT(03/17/2009-03/17/2009), KQYA(10/31/2017-10/31/2017), KUNR(04/26/2002-12/01/2003),
            # NOP3(10/10/2007-11/12/2014),NOP4(05/24/2010-09/29/2017),PGUM(09/16/2002-09/16/2002),ROP3(07/23/2012-01/03/2017),
            # ROP4(07/21/2010-07/30/2018),TIC(03/03/2009-03/03/2009),TJBQ(10/30/2017-06/28/2018),TJRV(10/30/2017-06/27/2018)
            # ,TLSX(03/03/2009-03/03/2009),TNAW(06/09/2017-08/16/2018),TTBW(03/03/2009-03/03/2009),KCRI(10/31/2014-10/31/2014)
            if sites=='all':
                radarSites = ['KABR' ,'KENX','KABX','KAMA','PAHG','PGUA','KFFC','KBBX','PABC','KBLX','KBGM','PACG','KBMX','KBIS','KFCX','KCBX','KBOX',
                         'KBRO','KBUF','KCXX','RKSG','KFDX','KCBW','KICX','KGRK','KCLX','KRLX','KCYS','KLOT','KILN','KCLE','KCAE','KGWX',
                         'KCRP','KFTG','KDMX','KDTX','KDDC','KDOX','KDLH','KDYX','KEYX','KEPZ','KLRX','KBHX','KVWX','PAPD','KFSX','KSRX',
                         'KFDR','KHPX','KPOE','KEOX','KFWS','KAPX','KGGW','KGLD','KMVX','KGJX','KGRR','KTFX','KGRB','KGSP','KUEX','KHDX',
                         'KHGX','KHTX','KIND','KJKL','KDGX','KJAX','RODN','PHKM','KEAX','KBYX','PAKC','KMRX','RKJK','KARX','KLCH','KLGX',
                         'KESX','KDFX','KILX','KLZK','KVTX','KLVX','KLBB','KMQT','KMXX','KMAX','KMLB','KNQA','KAMX','PAIH','KMAF','KMKX',
                         'KMPX','KMBX','KMSX','KMOB','PHMO','KTYX','KVAX','KMHX','KOHX','KLIX','KOKX','PAEC','KLNX','KIWX','KEVX','KTLX',
                         'KOAX','KPAH','KPDT','KDIX','KIWA','KPBZ','KSFX','KGYX','KRTX','KPUX','KDVN','KRAX','KUDX','KRGX','KRIW','KJGX',
                         'KDAX','KMTX','KSJT','KEWX','KNKX','KMUX','KHNX','TJUA','KSOX','KATX','KSHV','KFSD','PHKI','PHWA','KOTX','KSGF',
                         'KLSX','KCCX','KLWX','KTLH','KTBW','KTWX','KEMX','KINX','KVNX','KVBX','KAKQ','KICT','KLTX','KYUX']
            else:
                radarSites = sites
            script_path = os.path.dirname(os.path.realpath(__file__))

            for site_id in radarSites:
                if os.path.exists(site_id):
                    pass
                else:
                    make_directory(site_id) # destination folder, path should be on the same directory as the script
                print("\nDownloading data from radar: \""+site_id+"\"")
                dirname = "{year}{month}{day}_{site_id}_{product}".format(
                        year=year, month=month, day=day, site_id=site_id, product=product)
                os.chdir(site_id)
                if os.path.exists(dirname):
                    pass
                else:
                    make_directory(dirname) # Data folder, path should be the directory of the Site_id folder
                page_url_base = ("https://www.ncdc.noaa.gov/nexradinv/bdp-download.jsp"
                                 "?yyyy={year}&mm={month}&dd={day}&id={site_id}&product={product}")
                page_url = page_url_base.format(year=year, month=month, day=day,
                                                site_id=site_id, product=product)
                #page_url_base = ("https://noaa-nexrad-level2.s3.amazonaws.com/{year}/{month}/{day}/{site_id}/{site_id}{year}{month}{day}_")
                #page_url = page_url_base.format(year=year, month=str(month).zfill(2), day=str(day).zfill(2),
                #                                site_id=site_id, product=product)
                links = save_links(page_url, dirname)
                for link in links:
                    download_link(link, dirname, timerange, velMap, spwMap, cutoff, edgeFilter, areaFraction, colorIntensity, circRatio, fillFilt)
                os.chdir(dirname)
                if os.stat("data_links.txt").st_size == 0:
                    print("THERE IS NO DATA AVAILABLE FOR THIS DATE\n")
                    os.remove("data_links.txt")
                    os.chdir("..")
                    os.rmdir(dirname)
                    print("Deleted", dirname, 'because it has no data\n')
                else:
                    os.remove("data_links.txt")
                os.chdir(script_path)
                if not os.listdir(site_id):
                    os.rmdir(site_id)
    except KeyboardInterrupt:
        site_info = "The last data downloaded was from the site:  " + site_id
        date_info = "The last attempted download date was in the following format:" \
                    "  MONTH / DAY / YEAR:    " + str(month) + "/" + str(day) + "/" + str(year)
        note = "NOTE: Last download date usually means an incomplete download of all the weather files. " \
               "Set the new date to be one day before the last download date to ensure all files are downloaded."
        print("\n\n", site_info)
        print("\n", date_info)
        os.chdir(script_path)
        file = open("last_download_date.txt", "w")
        file.write(site_info + "\n" + date_info + "\n" + note)
        file.close()
        print("\nExported the last known dates before program ended to last_download_date.txt "
              "located in the same directory as scraper.py")
        print("\nChange the origin_month, origin_day, and origin_year variables accordingly "
              "from the last_download_date.txt\n")
        print(note)

