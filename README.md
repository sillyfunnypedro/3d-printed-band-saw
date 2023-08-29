# 3d-printed-band-saw
The python script that generates the openSCAD files for the 3d printed band saw

I decided to not pull these objects apart into different files because this produces one output (albeit in 23 files)

If you are debugging the code i recommend that you set two varialbles as follows
```
class BandSaw:
    def __init__(self):
        self.make_stl = False  # this is turned off for debuging
        self.production = False

        # initialize the tools.
```

I attempted to make the functions self descriptive and every time i jump back into this code i updates comments 
where i am working

You will need to install the solid library that embellishes python to work with OpenSCAD objects.

use the one at https://github.com/SolidCode/SolidPython

the OpenSCAD viewer is available here.

https://openscad.org/

