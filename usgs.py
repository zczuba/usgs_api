# helpful link: https://apps.nationalmap.gov/tnmaccess/#/product

import json
import math
import os
import shutil
import time
import urllib3

def get_valid_x(prompt):
    while True:
        try:
            xValue = float(input(prompt))
        except:
            print("X value must be between -180 and 180")
            continue

        if abs(xValue) > 180:
            print("X value must be between -180 and 180")
            continue
        else:
            break
    return xValue

def get_valid_y(prompt):
    while True:
        try:
            yValue = float(input(prompt))
        except:
            print("Y value must be between -90 and 90")
            continue

        if abs(yValue) > 90:
            print("Y value must be between -90 and 90")
            continue
        else:
            break
    return yValue

def get_bounding_box():
    while True:
        try:
            xMin = get_valid_x("xMin (West bound): ")
            yMin = get_valid_y("yMin (South bound): ")
            xMax = get_valid_x("xMax (East bound): ")
            yMax = get_valid_y("yMax (North bound): ")
        except:
            print("Invalid bounding box")
            continue
        
        if yMin > yMax:
            print("yMin must be less than yMax. Please re-enter boudning box coordinates")
            continue
        elif xMin > xMax:
            print("xMin must be less than xMax. Please re-enter boudning box coordinates")
            continue
        else:
            print(f'Bounding box of [{xMin}, {yMin}, {xMax}. {yMax}] received')
            break
    return [xMin, yMin, xMax, yMax]

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def find_year_from_string(title):
    indexOf20 = title.index('20')
    year = title[indexOf20:(indexOf20+4)]    
    return int(year)


timestr = time.strftime("%Y-%m-%d_%H-%M-%S")

nhdString = "National%20Hydrography%20Dataset%20Plus%20High%20Resolution%20(NHDPlus%20HR)"
lpcString = "Lidar%20Point%20Cloud%20(LPC)"

print("Please make a selection:")
print("Enter 1 to search for NHD Plus data")
print("Enter 2 to search for Lidar Point Cloud data")
dataType = int(input())

if dataType == 1:
    dataString = nhdString
elif dataType == 2:
    dataString = lpcString
else:
    print("Invalid entry, exiting script")
    exit()

print('\nEnter boudning box coordinates one at a time in decimal format (ex. -23.846127)')
bbox = get_bounding_box()

http = urllib3.PoolManager()

mostRecentNHD = "0000-00-00"
mostRecentLPC = "0000-00-00"
mostRecentList = []

print("\nConnecting to USGS...")
r1 = http.request('GET', f'https://tnmaccess.nationalmap.gov/api/v1/products?bbox={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}&datasets={dataString}')
data_values = json.loads(r1.data.decode('utf-8'))

if dataType == 1:
    print('Searching USGS for the newest NHD Plus datasets...')
    for dataset in data_values['items']:
        if 'HU' in dataset['extent']:
            if dataset['modificationInfo'] > mostRecentNHD:
                mostRecentNHD = dataset['modificationInfo']
                mostRecentList = [dataset]
            elif dataset['modificationInfo'] == mostRecentNHD:
                mostRecentList.append(dataset)

else:
    print('Searching USGS for the newest Lidar Point Cloud datasets...')
    for dataset in data_values['items']:
        currentDataYear = dataset['publicationDate']
        if currentDataYear > mostRecentLPC:
            mostRecentLPC = currentDataYear
            mostRecentList = [dataset]
        elif currentDataYear == mostRecentLPC:
            mostRecentList.append(dataset)
        
if len(mostRecentList) > 0:
    print(f'{len(mostRecentList)} dataset(s) found\n')
else:
    print(f'No datasets found for the bounding box: {bbox}')
    exit()

if dataType == 1:
    dirName = 'NHD_' + timestr
else:
    dirName = 'LPC_' + timestr
os.makedirs(dirName)
os.chdir(dirName)

for i, entry in enumerate(mostRecentList, 1):
    if dataType == 1:
        url_gdb = entry['urls']['FileGDB']
    else:
        url_gdb = entry['urls']['LAZ']
    url_meta = entry['metaUrl'] + '?format=json'
    c1 = urllib3.PoolManager()
    c2 = urllib3.PoolManager()
    filename = url_gdb.rsplit('/', 1)[-1]
    metaFileName = filename[:-4] + '.json'
    with c1.request('GET', url_gdb, preload_content=False) as res, open(filename, 'wb') as out_file:
        if hasattr(entry, 'sizeInBytes'):
            downloadSize = convert_size(entry['sizeInBytes'])
            print(f'{filename} is downloading...\nFile size will be approximately {downloadSize}')
        else:
            print(f'{filename} is downloading...\nFile size unknown')
        shutil.copyfileobj(res, out_file)

    with c2.request('GET', url_meta, preload_content=False) as res, open(metaFileName, 'wb') as out_file:
        print(f'Metadata for {filename} is downloading...\n')   
        shutil.copyfileobj(res, out_file)
    
    print(f"Dataset download {i}/{len(mostRecentList)} done\n")

print("Exiting script now")