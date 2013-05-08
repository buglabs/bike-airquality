#!/usr/bin/python
from BUGswarm import apikey
from BUGswarm import resource
from BUGswarm import participation
import logging
import time
import sys

logging.basicConfig(level=logging.INFO)
api = apikey.apikey("demo","buglabs55")
res = resource.getResourceByName(api,"OrangePortal")
swarms = res.getSwarms()
airqual = 0
#Don't do this here, do this in response to a "start" request
#Also store the "f" object somewhere that would allow multiple files to be open
#at once.  For example:
# files = {}
# resourceid = '498871cd3e8246b9f466d37968f6ef1a1e0c464e'
# files[resourceid] = open('Bike04-050813.csv', 'w')
#
# don't forget at some point later to do
# files[resourceid].close()
# del files[resourceid]
# ^^ so that the entry is removed when recording is to "stop"
f = open('airlog.csv','a')

print "Press Control-C to quit\r\n"

def presence(obj):
    print "presence from "+obj['from']['resource']
def message(obj):
    global airqual
    try:
        # if using a files map, could do:
        # for resid in files:
        #   if obj['from']['resource'] == resid:
        #     files[resid].write(...)
        if obj['from']['resource'] == '498871cd3e8246b9f466d37968f6ef1a1e0c464e':
            payload = obj['payload']
            if not 'name' in payload:
                return
            if payload['name'] == 'AirQuality':
                airqual = int(payload['feed']['value'])
            elif payload['name'] == 'Location':
                lat = payload['feed']['latitude']
                lon = payload['feed']['longitude']
                valid = payload['feed']['valid']
                if valid:
                    line = str(time.time())+','+\
                        str(lat)+','+\
                        str(lon)+','+\
                        str(airqual)
                    print line
                    f.write(line+'\n')
                    f.flush()
    except Exception as e:
        print 'Exception: '+str(e)+' '+str(sys.exc_info())
    #print "message "+str(obj)
    #print "message "+str(obj['payload'])
def error(obj):
    print "error "+str(obj['errors'])

pt = participation.participationThread(api,res, swarms,
        onPresence=presence, onMessage=message, onError=error)
try:
    while(True):
        time.sleep(2)
except KeyboardInterrupt:
    pass
pt.stop()
