#!/usr/bin/env python

##
# Disclaimer: make sure that no human or animal is inside the car when
# activating Sentry mode!
# tip: Sentry mode can not be activated when Dog mode is active or in
# this script when the car is unlocked

import os, sys
sys.path.append(os.path.abspath(os.path.expanduser("~/git/teslajson")))
import teslajson
import datetime

def readfile(file):
    file = os.path.expanduser(file)
    if (os.path.isfile(file)):
        with open(file) as fp:
            return fp.read().rstrip()
    print('No such file '+file)
    exit(1)

cmds = sys.argv[1:]
if len(cmds) == 0:
    print("Must have at least one command")
    exit(0)

today = datetime.datetime.today()
ftoday = '{:%a %d %b %H:%M:%S %Y}'.format(today)

tesla_email = readfile('~/.teslaemail') # your email adresse when logging into tesla.com
tesla_pwd = readfile('~/.teslapwd') # your password when logging into tesla.com

try:
    c = teslajson.Connection(email=tesla_email, password=tesla_pwd)
except:
    try:
        print ftoday+" can't contact api - retry after 15 seconds"
        sleep(15) # wait 15 seconds
        c = teslajson.Connection(email=tesla_email, password=tesla_pwd)
    except:
        print ftoday+" can't contact api - do nothing"
        exit(1)

v = c.vehicles[0] #just use the first car - at least I can't afford more than one :)

drive_state = None
vehicle_state = None
charge_state = None
climate_state = None

for cmd in cmds:
    if cmd == 'lock':
        # check if car is parked but unlocked then lock it if climate is off, not charging and 
        # no file for disable auto locking exists

        # check if disable auto lock file exists
        if (os.path.isfile('/tmp/disable_tesla_auto_lock')):
            print ftoday+" disable auto lock is on, do nothing"
        else:
            try:
                if drive_state is None:
                    drive_state = v.data_request('drive_state')
                if vehicle_state is None:
                    vehicle_state = v.data_request('vehicle_state')
                if charge_state is None:
                    charge_state = v.data_request('charge_state')
                if climate_state is None:
                    climate_state = v.data_request('climate_state')
            except Exception as e:
                print ftoday+" can't contact car, do nothing " + str(e)
            else:
                # ignore if charging
                if (charge_state['charge_port_latch'] == 'Engaged' and charge_state['charging_state'] == 'Charging'):
                    continue

                # ignore if climate is on
                if (climate_state['is_climate_on'] == True):
                    continue

                # check if shift_state is in park and car is not locked
                if (drive_state['shift_state'] == 'P' or drive_state['shift_state'] is None):
                    if (vehicle_state['locked'] != True):
                        # get gps position
                        msg = ftoday+" car is parked but not locked - locking it now\n"+"lat,lon: "+str(drive_state['latitude'])+","+str(drive_state['longitude'])
                        res = v.command('door_lock')
                        print msg
                        # make sure vehicle_state is also set to locked
                        vehicle_state['locked'] = True;
                    else:
                        print ftoday+" car is parked and is locked"

    if cmd == 'sentry_mode':
        # check if parked and locked then enable sentry mode if no file 
        # no file for disable auto sentry mode file exists
        if (os.path.isfile('/tmp/disable_tesla_auto_sentry_mode')):
            print ftoday+" disable auto sentry-mode is on, do nothing"
        else:
            try:
                if drive_state is None:
                    drive_state = v.data_request('drive_state')
                if vehicle_state is None:
                    vehicle_state = v.data_request('vehicle_state')
            except Exception as e:
                print ftoday+" can't contact car, do nothing " + str(e)
            else:
                # check if drive_state is parked and car is locked and not sentry mode active
                if (drive_state['shift_state'] == 'P' or drive_state['shift_state'] is None):
                    if (vehicle_state['locked'] == True and vehicle_state['sentry_mode'] != True):
                        if (vehicle_state['is_user_present'] == False):
                            msg = ftoday+" car is parked and locked - activating Sentry Mode\n"+"lat,lon: "+str(drive_state['latitude'])+","+str(drive_state['longitude'])
                            params = {'on': True}
                            res = v.command('set_sentry_mode', params)
                            if res["response"]["result"] != True:
                                msg = ftoday+" car is parked and locked - but not activating Sentry Mode because: "+res["response"]["reason"]+"\n"+"lat,lon: "+str(drive_state['latitude'])+","+str(drive_state['longitude'])
                            print msg
                        else:
                            print ftoday+" car is parked, locked and Sentry Mode is enabled"

exit(0)
