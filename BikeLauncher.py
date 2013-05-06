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
import shelve

class BikeLauncher:
    def __init__(self):
        reconnect = True
        logging.basicConfig(level=logging.INFO)
        self.aplist = shelve.open('/home/pi/build/bugswarm-tools/aplist.dat')
        self.lcd=Adafruit_CharLCDPlate()
        self.lcd.begin(16,2)
        try:
            while(True):
                print "Launcher Start"
                if not self.online() or not reconnect:
                    self.doProvision()
                bike = BikeConnector("Bike01", lcd=self.lcd)
                reconnect = True
                while(reconnect):
                    self.lcd.clear()
                    self.lcd.message("Connecting to\nSwarm")
                    reconnect = bike.runLoop()
                    print "reconnect: "+str(reconnect)
                    self.lcd.message("Please wait\n")
                    time.sleep(1.0)
                    self.lcd.clear()
                    self.lcd.message("Reconnecting\n")
                bike.stop()
        except KeyboardInterrupt:
            print "Quit the loop"
            bike.stop()
            print "Should be quit..."

    def doProvision(self):
        success = False
        self.lcd.clear()
        while not success:
            self.lcd.message("Wifi Scanning...\n")
            ssidlist = self.wifiScan()
            print "AP list: "+str(ssidlist)
            ssid = self.doSelectSSID(ssidlist)
            passwd = self.getPass(ssid)
            self.lcd.clear()
            time.sleep(0.2)
            passwd = self.doSelectPass(passwd)
            self.setPass(ssid, passwd)
            self.lcd.clear()
            self.lcd.message("Connecting...\n")
            success = self.connectWifi(ssid, passwd)
            if not success:
                self.lcd.clear()
                self.lcd.message("ERR No IP\n")
                self.lcd.message("Please Try Again\n")
                time.sleep(2.0)
                continue
            self.lcd.clear()
            self.lcd.message("Verifying...\n")
            success = self.waitForInternet()
            if not success:
                self.lcd.clear()
                self.lcd.message("ERR No Internet\n")
                self.lcd.message("Please try Again\n")
                time.sleep(2.0)

    def connectWifi(self, ssid, passwd):
        print "Connecting to "+ssid+" with "+passwd
        getstatusoutput('cp /etc/network/interfaces /etc/network/interfaces.bak')
        fout = open('/etc/network/interfaces.new','w')
        fin = open('/etc/network/interfaces.bak','r')
        for line in fin:
            ssidpos = line.find('wpa-ssid')
            passpos = line.find('wpa-psk')
            if len(line.lstrip()) > 0 and line.lstrip()[0] == '#':
                fout.write(line)
            elif ssidpos >= 0:
                fout.write(line[:ssidpos+8]+' "'+ssid+'"\n')
            elif passpos >= 0:
                fout.write(line[:passpos+7]+' "'+passwd+'"\n')
            else:
                fout.write(line)
        fout.close()
        fin.close()
        getstatusoutput('mv /etc/network/interfaces.new /etc/network/interfaces')
        ret = getstatusoutput('/etc/init.d/networking restart')
        print ret
        return (ret[1].find('bound') > 0)

    def getPass(self, ssid):
        if ssid in self.aplist:
            return self.aplist[ssid]
        return ""

    def setPass(self, ssid, password):
        self.aplist[ssid] = password
        self.aplist.sync()

    def doSelectPass(self, password=""):
        self.lcd.clear()
        self.lcd.message("Enter Password:\n")
        self.lcd.message(password+'\n')
        self.lcd.setCursor(0,1)
        self.lcd.cursor()
        pos = 0
        done = False
        passlist = list(password)
        for i in range(0,16-len(password)):
            passlist.append(' ')
        while not done:
            if self.lcd.buttonPressed(self.lcd.UP):
                letter = ord(passlist[pos])+1
                if letter > 126:
                    letter = 32
                passlist[pos] = chr(letter)
            if self.lcd.buttonPressed(self.lcd.DOWN):
                letter = ord(passlist[pos])-1
                if letter < 32:
                    letter = 126 
                passlist[pos] = chr(letter)
            if self.lcd.buttonPressed(self.lcd.LEFT):
                pos = pos - 1
                if pos < 0:
                    pos = 0
            if self.lcd.buttonPressed(self.lcd.RIGHT):
                pos = pos + 1
                if pos > 15:
                    pos = 15
            if self.lcd.buttonPressed(self.lcd.SELECT):
                done = True
            self.lcd.clear()
            self.lcd.message("Enter Password:\n"+"".join(passlist))
            self.lcd.setCursor(pos,1)
            time.sleep(0.1)
        password = ("".join(passlist)).rstrip()
        self.lcd.noCursor()
        print "Selected "+password
        return password

    def printSSID(self, idx, ssid):
        self.lcd.clear()
        self.lcd.message("Select SSID:\n")
        self.lcd.message(str(idx)+':'+ssid)

    def doSelectSSID(self, ssidlist):
        selected = False
        idx = 0
        self.printSSID(idx, ssidlist[idx])
        while not selected:
            if self.lcd.buttonPressed(self.lcd.DOWN):
                idx = idx + 1
                if idx > len(ssidlist)-1:
                    idx = 0
                self.printSSID(idx, ssidlist[idx])
                time.sleep(0.1)
            if self.lcd.buttonPressed(self.lcd.UP):
                idx = idx - 1
                if idx < 0:
                    idx = len(ssidlist)-1
                self.printSSID(idx, ssidlist[idx])
                time.sleep(0.1)
            if self.lcd.buttonPressed(self.lcd.SELECT):
                return ssidlist[idx]

    def wifiScan(self):
        ret = getstatusoutput('iwlist wlan0 scan | grep ESSID')
        ret = getstatusoutput('iwlist wlan0 scan | grep ESSID')
        rawlist = ret[1].split('"')
        result = []
        for i in range(0, len(rawlist)):
            if i%2==1:
                result.append(rawlist[i])
        return result

    def waitForInternet(self):
        self.connected = False
        start = time.time()
        while not self.connected and time.time() - start < 30.0:
            time.sleep(1.0)
            if self.online():
                self.connected = True
            self.lcd.message("Net: "+str(self.connected)+'\n')
            print "Ping: "+str(self.connected)
        return self.connected

    def online(self):
        ret = getstatusoutput('ping -c 1 www.google.com')
        if ret[0] != 0:
            return False
        ret = getstatusoutput('ping -c 1 www.google.com')
        return (ret[0] == 0)
        

if __name__ == '__main__':
    launcher = BikeLauncher()
