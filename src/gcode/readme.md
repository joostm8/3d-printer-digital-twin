# printing files

This folder contains the gcode (vase-m400.gcode) to print a low poly rose vase as found on https://www.printables.com/model/1595-low-poly-rose-vase

It also contains printer profiles (Octoprint-virtual.ini, Klipper-virtual.ini) and a print profile (octoprint-virtual-vase.ini) for printing in [PrusaSlicer](https://www.prusa3d.com/p/prusaslicer/)

Lastly it contains a Python script (gcode_append_m400.py) to append M400 commands to the gcode. Specify the filename of the sliced output of PrusaSlicer to obtain the printable gcode.

Read on to learn what profiles are needed for your configuration.

## Profiles location

To store the profiles in your PrusaSlicer configuartion folder:

1. Open PrusaSlicer
2. In the toolbar on top: click `Help>Show Configuration Folder`
3. Printer profiles go in the printer folder, print profiles in the print folder.

Select the right profiles in PrusaSlicer before slicing.

## Klipper

Klipper just needs you to set the Printer in PrusaSlicer to `Klipper-virtual`. Other than that, you are free to choose whatever print settings you want. The exported gcode can be printed in MainSail as-is.

## OctoPrint+Marlin

OctoPrint+Marlin is a bit more convoluted: select the printer and print profile in PrusaSlicer, then pass the generated gcode in the Python script (gcode_append_m400.py). The Reason is given below.

To be able to track the movement of the printer, we need Marlin (the firmware of a Typical Ender 3, emulated by the Virtual Printer) to send out position updates. These can either be sent out as response to the M114 command, or by the [M154](https://marlinfw.org/docs/gcode/M154.html) command, which additionally specifies the rate at which to output, with 1 Hz being the fastest. These position updates are published by OctoPrint to the MQTT broker, from which we can receive updates in our visualization. There are however some problems with using the generated gcode as is:

- The position of the printer updates much more than once a second. At a rate of 1 Hz, which is the fastest the M154 command goes, we would be undersampling the position info of the printer, which breaks the visualization. We could use M114 after each movement command instead, which would print the position.
- Secondly, the M114/M154 command output is not the actual position of the printer, but the last planned position of the printer. By default, it will plan many moves in advance. The M114 command seems to be processed asynchronously as well.

So, the profiles and the python script in this repository do the following to enable a good visualization:

- The printer profile adds custom startup gcode for the M154 command

The gcode_append_M400.py script adds two commands after each movement command. Not recommended though, since updating once per second makes the print really slow. Don't use this one, legacy

- It adds a `G4 S1` command, which makes the printer dwell in place for 1 second, alleviating the undersampling issue mentioned earlier.
- It adds a `M400` command, which makes the printer finish all its current moves before planning any new ones. This alleviates the planner issue mentioned earlier. Essentially we're disabling the movement queue.

The gcode_append_M114.py script adds two commands after each movement command. Not recommended though, since updating once per second makes the print really slow. Use this one

- It adds a `M114` command, which makes the printer print the position.
- It adds a `M400` command, which makes the printer finish all its current moves before planning any new ones. This alleviates the planner issue mentioned earlier and ensures the printer prints the last position.

- The print profile prints in vase mode (just one continuous outer perimeter), and bypasses the bottom layer, which allows us to visualize the print at a somewhat acceptable speed still.

TODO Joost: what if I just input M114 commands after each move operation instead?

Alright, I just tested this, and that works just fine, just need to keep th M400 in there so moves don't get planned ahead, but otherwise it seems to work alright!
Means I can update the coursetext, and that octoprint now no longer needs the vase profile and the custom M154 startup code!
Will update that later, this is really a great find. Makes me wonder why I didn't think of this before though.
Also means that the octoprint+klipper should work. Will give that a test next.

Updated documentation above.