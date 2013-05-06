#!/usr/bin/python
from Adafruit_CharLCDPlate.Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from BUGswarm import apikey
from BUGswarm import resource
from BUGswarm import participation
from pynmea import nmea
import logging
import time
import serial
import json
import socket
from BikeConnector import *
from commands import getstatusoutput
import time

password = "bikepass"
lcd=Adafruit_CharLCDPlate()
lcd.begin(16,2)
lcd.clear()
lcd.message("Enter Password:\n")
lcd.message(password+'\n')
lcd.setCursor(0,1)
lcd.cursor()
pos = 0
done = False
passlist = list(password)
for i in range(0,16-len(password)):
    passlist.append(' ')
while not done:
    if lcd.buttonPressed(lcd.UP):
        letter = ord(passlist[pos])+1
        if letter > 126:
            letter = 32
        passlist[pos] = chr(letter)
    if lcd.buttonPressed(lcd.DOWN):
        letter = ord(passlist[pos])-1
        if letter < 32:
            letter = 126 
        passlist[pos] = chr(letter)
    if lcd.buttonPressed(lcd.LEFT):
        pos = pos - 1
        if pos < 0:
            pos = 0
    if lcd.buttonPressed(lcd.RIGHT):
        pos = pos + 1
        if pos > 15:
            pos = 15
    if lcd.buttonPressed(lcd.SELECT):
        done = True
    lcd.clear()
    lcd.message("Enter Password:\n"+"".join(passlist))
    lcd.setCursor(pos,1)
    time.sleep(0.1)
password = ("".join(passlist)).rstrip()
print "result: *"+password+"*"
