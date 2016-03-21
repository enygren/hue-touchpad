# hue-touchpad
Code for controlling a Philips Hue lightbulb using a Logitech Touchpad.

Relies on [isaackelly's python-hue](https://github.com/issackelly/python-hue).

For more details see [my blog post](https://erik.nygren.org/?p=87) and a [video of this in action](https://www.youtube.com/watch?v=HWzJMHpNs9Y).

Two tools are included:  TouchPadControl.py and hue.py

For both of them, you will need to update paths and replace the API
key in the file.

## hue.py

This is a command-line tool for controlling the lights.  

## TouchPadControl.py

This reads events from the touchpad and controls the lights based on
button pushes and gestures.

