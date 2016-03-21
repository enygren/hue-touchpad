#!/usr/bin/python

import sys, os, re, string, datetime, logging, time, random

sys.path.append('/home/house/src/house/hue/python-hue')
import hue

hue.logger.setLevel(logging.WARNING)
#hue.logger.setLevel(logging.INFO)
#hue.logger.setLevel(logging.DEBUG)
logger = hue.logger

def time_to_color():
    hour = datetime.datetime.now().hour + datetime.datetime.now().minute/60.0
    temp = 2000
    if hour > 4 and hour <= 7:
        # ramp from 2000K up to 6500K from 4:00 to 7:00
        temp = max(2000, min(6500,2000+(4500/3)*(hour-4)))
    elif hour > 7 and hour < 23:
        # ramp from 6500K down to 2000K from 12:00 to 21:00
        temp = max(2000, min(6500, 5000-(3000/6)*(hour-15)))
    return int(temp)

h = hue.Hue() # Initialize the class
h.station_ip = "hue.example.com"  # Your base station IP
h.client_identifier = 'ffff__put_station_id_here_ffff'  # put your client identifier / auth token here
h.get_state()

def update_lightset(arg):
    hue.logger.warn("Using lightset "+arg)
    if arg == 'O':
        return ('l1','l2','l3')
    elif arg == 'N':
        return ('l4','l5','l6')
    elif arg == 'L':
        return ('l7',)
    else:
        return ('l1','l2','l3')

lightset = ('l1','l2','l3')
lightsetall = ('l1','l2','l3','l4','l5','l6','l7')
colortemp = time_to_color()
if sys.argv[1] == 'state' or sys.argv[1] == 'status':
    for x in lightsetall:
        light = h.lights.get(x)
        light.update_state_cache()
        #print light, dir(light), light.state
        state = light.state['state']
        print "%s name='%s' on=%s reachable=%s colormode=%s bri=%d sat=%d ct=%d xy=%s"%(x, 
                                                 light.state['name'], 
                                                 str(state['on']), 
                                                 str(state['reachable']), 
                                                 str(state['colormode']), 
                                                 int(state['bri']),
                                                 int(state['sat']),
                                                 int(1e6/(state['ct']+1)),
                                                 str(state['xy']))
elif sys.argv[1] == 'redshift':
    for x in lightsetall:
        light = h.lights.get(x)
        light.update_state_cache()
        state = light.state['state']
        if state['reachable'] and state['on'] and state['colormode'] == 'ct':
            logger.info("Shifting %s from %d to %d"%(x, int(1e6/state['ct']), colortemp))
            light.cct(colortemp)
        else:
            logger.info("Skipping %s due to %s and %s"%(x, state['on'], state['colormode']))
elif sys.argv[1] == 'on':
    if len(sys.argv) > 2:
        lightset = update_lightset(sys.argv[2])
    for x in lightset:
        h.lights.get(x).on().cct(colortemp).bri(255)
elif sys.argv[1] == 'dim':
    if len(sys.argv) > 2:
        lightset = update_lightset(sys.argv[2])
    if len(sys.argv) == 3:
        dim = int(sys.argv[2])
    else:
        dim = 100
    for x in lightset:
        h.lights.get(x).on().bri(dim)
elif sys.argv[1] == 'candle':
    if len(sys.argv) > 2:
        lightset = update_lightset(sys.argv[2])
    #for x in ('l1','l2'):
    #    h.lights.get(x).off()
    for x in lightset:
        h.lights.get(x).on().xy(.5767, 0.383).bri(20)
    ctr = 10000
    while ctr > 0:
        ctr -= 1
        x = lightset[random.randrange(0,len(lightset))]
        h.lights.get(x).on().bri(int(20+30*random.random()))
        time.sleep(random.random()/5.0)
        h.lights.get(x).on().bri(20)
        time.sleep(random.random()/3.0)
        # bri=20 sat=236
elif sys.argv[1] == 'red':
    if len(sys.argv) > 2:
        lightset = update_lightset(sys.argv[2])
    for x in lightset:
        #h.lights.get(x).on().rgb('#ff0000').bri(10).on().bri(10)
        h.lights.get(x).on().bri(5).xy(0.674, 0.322).bri(10).on().bri(5)
elif sys.argv[1] == 'ramp':
    if len(sys.argv) > 2:
        lightset = update_lightset(sys.argv[2])
    ramptime = 250.0
    newct = 2000
    rampincr = 2
    for x in lightset:
        h.lights.get(x).on().cct(newct).bri(5)
    for bri in range(10,255,rampincr):
        newct = int((colortemp-2000)/255.*bri+2000)
        print bri, newct
        for x in lightset:
            h.lights.get(x).bri(bri).cct(newct)
        time.sleep(ramptime/(245./rampincr))
elif sys.argv[1] == 'color':
    if len(sys.argv) == 3:
        color = sys.argv[2]
    else:
        color = "#ff0000"
    for x in lightset:
        h.lights.get(x).on().rgb('#'+color)
elif sys.argv[1] == 'off':
    if len(sys.argv) > 2:
        lightset = update_lightset(sys.argv[2])
    for x in lightset: 
        h.lights.get(x).off()
else:
    print "Unknown command"
    sys.exit(-1)


