# hue-touchpad

Simple hacks for controlling a Philips Hue lightbulb using a Logitech Touchpad.

Relies on [isaackelly's python-hue](https://github.com/issackelly/python-hue).

For more details see [my blog post](https://erik.nygren.org/?p=87) and a [video of this in action](https://www.youtube.com/watch?v=HWzJMHpNs9Y).

Two tools are included:  TouchPadControl.py and hue.py

For both of them, you will need to update paths and replace the API
key in the file.  For example, replace:

~~~
    h.station_ip = "hue.example.com"  # Your base station IP
    h.client_identifier = 'ffff__put_station_id_here_ffff'  # put your client identifier / auth token here
~~~

with the relevant hostname or IP address of your hue hub as well as the station identifier.
You will also need to make sure sys.path includes the python-hue library, so update this as needed:

~~~
    sys.path.append('/home/house/src/house/hue/python-hue')
~~~

You will also want to update the lightsets to cover your lights.

## hue.py

This is a command-line tool for controlling the lights.  For example:

* "hue on" turns on lights
* "hue redshift" can be run from a crontab to adjust the color temperature of lights turned on

## TouchPadControl.py

This reads events from the touchpad and controls the lights based on
button pushes and gestures.

