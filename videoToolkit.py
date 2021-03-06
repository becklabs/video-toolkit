# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 19:50:43 2020

@author: beck
"""
import cv2
from tqdm import *
import datetime
import dateparser
import os
import sys
import pandas as pd
import pytz

def getCreationDate(file):
    #GET CREATEDATE FROM EXIFTOOL
    stream = os.popen('exiftool '+file)
    output = stream.read().split('\n')
    for item in output:
        item = item.replace(' ','')
        if item.split(':')[0] == 'TrackCreateDate':
            break
    datelist=item.split(':')[1:]
    creationdate = ''
    for item in datelist:
        creationdate = creationdate+item
    creationdate = dateparser.parse(creationdate)
    return creationdate

def getOffsets(file):
    folder,filename = splitPath(file)
    #GET DELTA SECONDS FOR EVERY FRAME
    cap = cv2.VideoCapture(file)
    totalFps = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    offsets = []
    sys.stdout.flush()
    pbar = tqdm(total=totalFps,desc='Getting timedeltas for: '+filename,unit='Frames')
    while(cap.isOpened()):
        frame_exists, curr_frame = cap.read()
        if frame_exists:
            offsets.append(cap.get(cv2.CAP_PROP_POS_MSEC))
            pbar.update(1)
        else:
            break
    cap.release()
    pbar.close()
    offsets = [datetime.timedelta(milliseconds=i) for i in offsets]
    return offsets

def splitPath(file):
    if '\\' in file:
        listfile = file.split('\\')
        filename = listfile[-1]
        folder = file[:len(file)-len(filename)]
    elif '/' in file:
        listfile = file.split('/')
        filename = listfile[-1]
        folder = file[:len(file)-len(filename)]
    else:
        filename=file
        folder = ''
    return folder,filename
        
        
def getTimestamps(inputPath,file,projectPath,export=True):
    offsets = getOffsets(inputPath+file)
    creationdate = getCreationDate(inputPath+file)
    
    #CALCULATE TIMESTAMPS
    timestamps = [creationdate+offset+datetime.timedelta(hours=4) for offset in offsets]
    timestamps = [timestamp.replace(tzinfo=pytz.UTC) for timestamp in timestamps]
    
    #GENERATE FRAME NAMES

    frames = [file+'_'+str(i)+'.jpg' for i in range(len(timestamps))]
    
    #EXPORT DATA AS CSV
    df = pd.DataFrame()
    df['Frame'] = frames
    df['Timestamp'] = timestamps
    if export == True:
        if 'timestamps' not in os.listdir(projectPath):
            os.mkdir(projectPath+'timestamps/')
        df.to_csv(projectPath+'timestamps/'+file+'_timestamps.csv')
    return df

def createFrames(inputPath,file,projectPath,taggedDF):
    taggedList = [taggedDF.loc[i,'Frame'] for i in range(len(taggedDF['Frame']))]
    if 'frames' not in os.listdir(projectPath):
        os.mkdir(projectPath+'frames/')
    cap = cv2.VideoCapture(inputPath+file)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    sys.stdout.flush()
    pbar = tqdm(total=total_frames, unit='Frames',desc='Writing '+str(total_frames)+' frames from ' + file + ' to frames/')
    i=0
    while(cap.isOpened()):
        frame_exists, frame = cap.read()
        if frame_exists:
            framename = file+'_'+ str(i)+'.jpg'
            if framename in taggedList:
                cv2.imwrite(projectPath+'frames/'+framename,frame)
            i+=1
            pbar.update(1)
        else:
            break
    pbar.close()
    cap.release()
    cv2.destroyAllWindows()
#if __name__ == '__main__':
    #if len(sys.argv) != 2: 
        #print("Need exactly one argument ...")
        #print("usage: python creationdate.py <filename>")
        #sys.exit()
    #else:
        #file = sys.argv[1]
        #getTimestamps(file)