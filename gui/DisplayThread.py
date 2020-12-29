'''
Description: 
Version: 2.0
Autor: mario
Date: 2020-12-23 15:06:20
LastEditors: mario
LastEditTime: 2020-12-24 21:43:08
'''
import sys
sys.path.append('..')

import os
import cv2
import numpy as np
import time
from PySide2.QtCore import QThread, Signal, Slot
from srcmx import SubtitleDict
from threading import Thread


ShareImg = [0]


class DisplayThread(QThread):
    # word, videonum, offset, length, speed, demoindex
    StatesOutSignal = Signal(str, str, str, str, str, str)
    # PaintSignal = Signal(type(np.array([])))
    # length, currentindex
    ImgDisplaySignal = Signal(int, float)
    DisplayLengthSig = Signal(int)
    
    def __init__(self, worddictpath, subdictpath, videodir, recpoint):
        super().__init__()
        # load the data
        self.worddict = SubtitleDict.WordsDict(worddictpath, subdictpath)
        self.videohandledict = self.Getvideohandles(videodir)
        
        self.recpoint = recpoint
        # self.gui = gui

        # control variables
        self.wordlist = ['supermarket']
        self.random = True
        
        self.speed = 1.0
        self.duration = 0.033
        self.working = True
        self.wordloop = True
        self.sampleloop = True
        self.displayloop = True

        self.maximumindex = 0
        self.minimumindex = 0
        self.currentindex = 0

        # share img
        h, w = recpoint[1][1] - recpoint[0][1], recpoint[1][0] - recpoint[0][0]
        self.shareImg = np.zeros((h, w, 3), dtype=np.uint8)

    def Getvideohandles(self, videodir):
        videohandles = {}
        videofiles = os.listdir(videodir)
        for videofile in videofiles:
            if videofile.endswith('mp4'):
                filepath = os.path.join(videodir, videofile)
                videohandles[videofile[:3]] = cv2.VideoCapture(filepath)
        return videohandles

    @Slot()
    def UpdateWord(self, word, mode):
        self.wordlist = [word]
        self.wordloop = False

    @Slot()
    def UpdateLoopRange(self, minindex, maxindex):
        # print('get the signal of %d--%d' % (minindex, maxindex))
        self.minimumindex = minindex
        self.maximumindex = maxindex
        self.currentindex = self.minimumindex
    
    @Slot()
    def NextSample(self):
        self.displayloop = False
    
    @Slot()
    def NextWord(self):
        self.sampleloop = False

    def run(self):
        recpoint = self.recpoint
        h, w = recpoint[1][1] - recpoint[0][1], recpoint[1][0] - recpoint[0][0]

        while self.working:
            # self.wait(2000)
            print("i'm in the loop")
            time.sleep(1)
            self.wordloop = True
            for word in self.wordlist:
                if not self.wordloop:
                    break
                
                samples = self.worddict.ChooseSamples(word, 1.5)
                counter = sum([x[-1] for x in samples])
                number = 0

                self.sampleloop = True
                for sample in samples:
                    if not (self.wordloop and self.sampleloop):
                        break

                    keynum, begin, end, label = sample

                    if label != 1:
                        continue
                    number += 1
                    length = end - begin
                    videoclips = np.zeros((length, h, w, 3), dtype=np.uint8)
                    self.videohandledict[keynum].set(cv2.CAP_PROP_POS_FRAMES, begin)
                    for i in range(length):
                        _, frame = self.videohandledict[keynum].read()
                        frame = frame[recpoint[0][1]:recpoint[1][1], recpoint[0][0]:recpoint[1][0], :]
                        videoclips[i] = frame
                    
                    # word, videonum, offset, length, speed, demoindex
                    self.StatesOutSignal.emit(word, keynum, str(begin), str(length),
                                              '%.02f' % self.speed, '%d/%d' % (number, counter))
                    self.DisplayLengthSig.emit(length)
                    
                    self.currentindex = 0
                    self.displayloop = True
                    while self.displayloop and self.sampleloop and self.wordloop:
                        if self.currentindex >= self.maximumindex or self.currentindex < self.minimumindex:
                            self.currentindex = self.minimumindex
                            time.sleep(0.5)

                        # print(self.currentindex, self.maximumindex)
                        self.shareImg = videoclips[self.currentindex]
                        ShareImg[0] = videoclips[self.currentindex]
                        self.ImgDisplaySignal.emit(self.currentindex, self.speed)
                            
                        time.sleep(self.duration/self.speed)
                        self.currentindex += 1
                            