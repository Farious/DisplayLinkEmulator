# DisplayLinkEmulator
Processes a DisplayLink USB Dump and renders the video

## Requirements
This process depends on: 
* [OpenCV2](http://opencv.org/ "OpenCV Homepage")
* [NumPy](http://www.numpy.org/ "NumPy Homepage")
* [dpkt](https://pypi.python.org/pypi/dpkt "dpkt's PyPi page")

Obviously you will need an DisplayLink USB Dump.

## Related Work
This project was only possible due to the hard work made by [Florian Echtler](https://github.com/floe "Florian Echtler's GitHub") and Chris Hodges, that you can follow in the following links:

1. http://events.ccc.de/congress/2009/Fahrplan/attachments/1490_slides.pdf
2. http://floe.butterbrot.org/displaylink/doku.php
3. https://github.com/floe/tubecable

Some of my classes, including the decryptor was strongly based on Florian Echtler's C implementation found on [1].

If you have any question feel free to do so.
