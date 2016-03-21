#!/usr/bin/python

from evdev import InputDevice, list_devices, categorize, ecodes
import sys, os, re, string, datetime, logging, time, random, select
sys.path.append('/home/house/house/hue/python-hue')
import hue


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

hue.logger.setLevel(logging.WARNING)
logger = logging.getLogger('TouchPadControl')
logger.setLevel(logging.DEBUG)


class HueAxisControl:
    def __init__(self, hue):
        self.h = hue
    def lights(self):
        return self.h.lights

class DimControl(HueAxisControl):
    def trigger(self, v):
        self.h.check_state_cache()
        for x in self.h.lights:
            dim = x.state['state']['bri']
            newdim = max(min(dim - v/2, 255), 1)
            logger.info('Adjusting light dim from %d to %d', dim, newdim)
            x.bri(newdim)

class OnOffControl(HueAxisControl):
    def trigger(self, v):
        if v < -300 and not self.h.are_any_lights_off():
            logger.info('Turning ON lights to full brightness  (v=%d)', v)
            for x in self.h.lights:
                x.on().bri(255).cct(time_to_color())
        elif v < -50:
            logger.info('Turning ON lights  (v=%d)', v)
            for x in self.h.lights:
                x.bri(5).on().bri(50).cct(time_to_color())
        if v > 50:
            logger.info('Turning OFF lights  (v=%d)', v)
            for x in self.h.lights:
                x.bri(5).off()

class ColorHueControl(HueAxisControl):
    def trigger(self, v):
        if self.h.in_color_mode():
            for x in self.h.lights:
                colorhue = x.state['state']['hue']
                newcolorhue = colorhue + v*2
                if newcolorhue > 2**16: newcolorhue -= 2**16
                if newcolorhue < 0: newcolorhue += 2**16
                logger.info('Adjusting color hue from %d to %d', colorhue, newcolorhue)
                x.set_state({'hue': newcolorhue})
        else:
            for x in self.h.lights:
                colortemp = int(1000000. / x.state['state']['ct'])
                newcolortemp = colortemp + v
                if newcolortemp > 6000: newcolortemp = 6000
                if newcolortemp < 1500: newcolortemp = 1500
                logger.info('Adjusting cct from %d to %d', colortemp, newcolortemp)
                x.cct(newcolortemp)
            
    
class ColorSatControl(HueAxisControl):
    def trigger(self, v):
        if not self.h.in_color_mode():
            logger.debug('Not in color mode, so not adjusting Saturation')
            return
        for x in self.h.lights:
            colorsat = x.state['state']['sat']
            newcolorsat = max(0, min(colorsat - v/10, 255))
            logger.info('Adjusting color sat from %d to %d', colorsat, newcolorsat)
            x.set_state({'sat': newcolorsat})
    

class RedModeControl(HueAxisControl):
    def trigger(self, v):
        if v < -150:
            logger.info('Turning ON lights to RED (v=%d)', v)
            for x in self.h.lights:
                x.on().bri(5).xy(0.674, 0.322).bri(10).on().bri(5)
        if v > 150:
            logger.info('Turning OFF lights  (v=%d)', v)
            for x in self.h.lights:
                x.bri(5).off()

class ControlledHue:
    #def __init__(self, lightset=('l4','l5','l6')):   # Nursery
    def __init__(self, lightset=('l7',)):  # Lightstrip
        self.last_state_cache_update = 0
        self.h = h = hue.Hue() # Initialize the class
        h.station_ip = "hue"  # Your base station IP
        h.client_identifier = 'ffff__put_station_id_here_ffff'
        h.get_state()
        self.lights = []
        for l in lightset:
            light = h.lights.get(l)
            light.update_state_cache()
            self.lights.append(light)

    def check_state_cache(self):
        logger.debug('Updating state cache')
        if time.time() - self.last_state_cache_update > 30:
            for l in self.lights:
                l.update_state_cache()
        self.last_state_cache_update = time.time()

    def in_color_mode(self):
        self.check_state_cache()
        r = True
        for l in self.lights:
            state = l.state['state']
            if not state['reachable'] or not state['on']:
                continue
            if state['colormode'] == 'ct':
                r = False
        return r


    def are_any_lights_off(self):
        self.check_state_cache()
        r = True
        for l in self.lights:
            if not l.state['state']['on']:
                r = False
        return r



class debugPrintFactory:
    def __init__(self, s):
        self.s = s
    def trigger(self, v):
        print("%s: %s"%(self.s,str(v)))

class ControlDimension:
    def __init__(self, name, onLeftUp, onRightDown):
        self.name = name
        self.onLeftUp = onLeftUp
        self.onRightDown = onRightDown
        self.abandon_thresh = 3   # how many seconds to abandon accumulated data
        self.last_time = 0.0
        self.accum = 0      # how much value have we accumulated

    def consume(self, ev, amount):
        evtime = ev.timestamp()
        if evtime - self.last_time > self.abandon_thresh:
            self.accum = 0
            logger.debug('%s: abandon', self.name)
        self.accum += amount
        self.last_time = evtime
        if False:  # handle immediately? 
            if self.accum > 100:
                self.onRightDown.trigger(self.accum)
                self.accum = 0
            elif self.accum < -100:
                self.onLeftUp.trigger(self.accum)
                self.accum = 0


    def idle(self, now):
        if self.accum > 70:
            self.onRightDown.trigger(self.accum)
            self.accum = 0
        elif self.accum < -70:
            self.onLeftUp.trigger(self.accum)
            self.accum = 0
      

class TouchPadEventHandler:
    def __init__(self, dev, huectl):
        self.dev = dev
        self.btn = ControlDimension('Button', 
                                    OnOffControl(huectl), 
                                    OnOffControl(huectl))
                                    #debugPrintFactory('left_btn'), 
                                    #debugPrintFactory('right_btn'))
        self.lr1f = ControlDimension('One.LeftRight', 
                                     debugPrintFactory('left_1f'), 
                                     debugPrintFactory('right_1f'))
        self.ud1f = ControlDimension('One.UpDown', 
                                     DimControl(huectl), 
                                     DimControl(huectl))
                                     #debugPrintFactory('up_1f'), 
                                     #debugPrintFactory('down_1f'))
        self.lr2f = ControlDimension('Two.LeftRight', 
                                     ColorHueControl(huectl),
                                     ColorHueControl(huectl))
                                     #debugPrintFactory('left_2f'), 
                                     #debugPrintFactory('right_2f'))
        self.ud2f = ControlDimension('Two.UpDown', 
                                     ColorSatControl(huectl),
                                     ColorSatControl(huectl))
                                     #debugPrintFactory('up_2f'), 
                                     #debugPrintFactory('down_2f'))
        self.lr3f = ControlDimension('Three.LeftRight', 
                                     debugPrintFactory('left_3f'), 
                                     debugPrintFactory('right_3f'))
        self.ud3f = ControlDimension('Three.UpDown', 
                                     RedModeControl(huectl),
                                     RedModeControl(huectl))
                                     #debugPrintFactory('up_3f'), 
                                     #debugPrintFactory('down_3f'))
        self.all_dimensions = (self.btn, self.lr1f, self.ud1f, self.lr2f, self.ud2f, self.lr3f, self.ud3f)


    def handleEvent(self, ev):
        if ev.code == 272 and ev.type == 1 and ev.value == 2:   # left down and hold
            self.btn.consume(ev, -40)
        elif ev.code == 272 and ev.type == 1 and ev.value == 0: # left up
            self.btn.consume(ev, -30)
        elif ev.code == 273 and ev.type == 1 and ev.value == 2: # right down and hold
            self.btn.consume(ev, 40)
        elif ev.code == 1 and ev.type == 2: # single finger up/down
            self.ud1f.consume(ev, ev.value)
        elif ev.code == 0 and ev.type == 2: # single finger right/left
            self.lr1f.consume(ev, ev.value)
        elif ev.code == 8 and ev.type == 2: # two finger up/down
            self.ud2f.consume(ev, ev.value*-20)
        elif ev.code == 6 and ev.type == 2: # two finger right/left
            self.lr2f.consume(ev, ev.value*20)
        elif ev.code == 109 and ev.type == 1 and ev.value == 1: # three finger down
            self.ud3f.consume(ev, 200)
        elif ev.code == 104 and ev.type == 1 and ev.value == 1: # three finger up
            self.ud3f.consume(ev, -200)
        elif ev.code == 275 and ev.type == 1 and ev.value == 0: # three finger left
            self.lr3f.consume(ev, -200)
        elif ev.code == 276 and ev.type == 1 and ev.value == 1: # three finger right
            self.lr3f.consume(ev, 200)

    def idle(self, now):
        for d in self.all_dimensions:
            d.idle(now)


def testme(dev):
    for event in dev.read_loop():
        print event
        if event.type == ecodes.EV_KEY:
            print(categorize(event))

def main():
    devices = map(InputDevice, list_devices())
    founddev = None
    for dev in devices:
        logger.debug( '[%s] [%s] [%s]' % (dev.fn, dev.name, dev.phys) )
        if dev.name == 'Logitech Unifying Device. Wireless PID:4011':
            logger.info('Found device controller on %s (%s)'%(dev.fn,dev.phys))
            founddev = dev
    if not founddev:
        logger.error('No device found (permissions missing?  chown or sudo?)')
        raise IOError("Unable to find device")
    founddev.grab()
    #testme(founddev)

    lightset = ('l7',)
    hn = os.popen("hostname")
    hostname = hn.read().split(".")[0].strip()
    hn.close()
    print "Running as "+hostname
    if hostname == "machine1" or hostname=="machine2":
        lightset=('l7',)
    elif hostname == 'machine3':
        lightset=('l4','l5','l6')
    print "Lightset: "+str(lightset)

    devicemap = {dev.fd : dev for dev in [founddev,]}
    # Replace later with an async loop
    tpeh = TouchPadEventHandler(founddev, ControlledHue(lightset=lightset))
    last_idle = 0.0
    while True:
        r,w,x = select.select([founddev.fd], [], [], 0.2)
        for fd in r:
            for event in devicemap[fd].read():
                tpeh.handleEvent(event)
        now = time.time()
        if now - last_idle > 0.3:
            tpeh.idle(now)
            last_idle=now

    #for event in founddev.read_loop():
    #     tpeh.handleEvent(event)

if __name__ == '__main__':
    while True:
        try:
            main()
        except IOError, e:
            print e
            print "Got IOError -- sleeping then retrying"
        time.sleep(5)

