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

class BikeConnector:
    def __init__(self, resource_name, device="/dev/ttyUSB0", lcd=Adafruit_CharLCDPlate()):
        logging.basicConfig(level=logging.INFO)
        self.api = apikey.apikey("demo", "buglabs55", port=8080)
        self.res = resource.getResourceByName(self.api, resource_name)
        self.swarms = self.res.getSwarms()
        self.airquality = 1024
        self.sats = 0
        self.tx = 0
        self.rx = 0
        self.locationupdates = 0
        self.airupdates = 0
        self.lcd = lcd
        self.lcd.clear()
        self.lastCapabilities = time.time()
        self.lastLCDUpdate = time.time()
        self.ser = serial.Serial(device, 9600, timeout=1)
        self.warmedup = False
        self.gpslock = False

    def runLoop(self):
        self.running = True
        reconnect = True
        try:
            self.pt = participation.participationThread(self.api, self.res, self.swarms,
                onPresence=self.presence, onMessage=self.message, onError=self.error)
            self.running = self.pt.connected
            while(self.running):
                line = self.ser.readline()
                if len(line) > 5:
                    self.parseSerial(line)
                if time.time() > self.lastCapabilities + 5.0:
                    self.sendCapabilities()
                    self.lastCapabilities = time.time()
                if time.time() > self.lastLCDUpdate + 1.0 and self.running:
                    self.lcd.clear()
                    self.lcd.message("sats:"+str(self.sats)+" Air:"+str(self.airquality)+"\n")
                    if not self.warmedup:
                        self.lcd.message("Sensor WarmingUp\n")
                    elif not self.gpslock:
                        self.lcd.message("No GPS Fix\n")
                    else:
                        self.lcd.message("tx:"+str(self.tx)+" rx:"+str(self.rx)+"\n")
                    self.lastLCDUpdate = time.time()
                if self.lcd.buttonPressed(self.lcd.SELECT):
                    reconnect = False
                    self.running = False
        except Exception as e:
            reconnect = True
            print e
        finally:
            print "Loop quit"
            return reconnect

    def sendCapabilities(self):
        msg = {"capabilities": {
                "feeds": ["Location", "AirQuality"]
            }}
        self.produce(msg)

    def NMEAPostoDec(self, param):
        if len(param) < 2:
            return None
        period = param.find('.')
        pos = float(param[period-2:])/60.0
        pos = pos + int(param[:period-2])
        return pos

    def parseSerial(self, msg):
        payload = {}
        if msg.startswith("$GPGGA"):
            pos = nmea.GPGGA()
            pos.parse(msg)
            lat = self.NMEAPostoDec(pos.latitude)
            lon = self.NMEAPostoDec(pos.longitude)
            #western hemisphere HACK
            if lon != None:
                lon = lon * -1
            payload = { "name": "Location",
                        "feed": {
                            "latitude": lat,
                            "longitude": lon,
                            "valid": (int(pos.gps_qual) > 0),
                            "satellites": int(pos.num_sats)
                    }}
            self.sats = int(pos.num_sats)
            self.gpslock = (int(pos.gps_qual) > 0)
            self.locationupdates = self.locationupdates + 1
            if self.locationupdates%6==0:
                self.produce(payload)
        if msg.startswith("$GPOSD"):
            msg = msg[:msg.find('*')]
            vals = msg.split(',')
            payload = { "name": "AirQuality",
                        "feed": {
                            "value": int(vals[1])
                    }}
            if int(vals[1]) > self.airquality:
                self.warmedup = True
            self.airquality = int(vals[1])
            self.airupdates = self.airupdates + 1
            if self.airupdates%6==2:
                self.produce(payload)

    def produce(self, obj):
        msg = json.dumps(obj)
        #print msg
        try:
            self.pt.produce(msg)
        except socket.timeout:
            self.stop()
            self.lcd.clear()
            self.lcd.message("ERROR DISCONNECT\n")
            print "Socket timeout, lets reconnect"
        self.tx = self.tx + 1

    def presence(self, obj):
        print "presence from "+obj['from']['resource']

    def message(self, obj):
        try:
            resid = obj["from"]["resource"]
            if resid == self.res.id:
                return
        except Exception as e:
            print e
            return
        self.rx = self.rx + 1
        print "message "+str(obj['payload'])

    def error(self, obj):
        print "error "+str(obj['errors'])

    def stop(self):
        self.running = False
        if self.pt:
            self.pt.stop()

if __name__ == '__main__':
    lcd=Adafruit_CharLCDPlate()
    bike = BikeConnector("Bike01", lcd=lcd)
    try:
        while(True):
            bike.runLoop()
            lcd.message("Please wait\n")
            time.sleep(1.0)
            lcd.clear()
            lcd.message("Reconnecting\n")
    except KeyboardInterrupt:
        print "Quit the loop"
        bike.stop()
        print "Should be quit..."
