

# OsteoSense Vibroarthography

OsteoSense Vibroarthograpy (VAG) consists of a dedicated sensor and supporting software to explore VAG signals.  It is a collaboration between Right Step Health and TalTech Environmental Sensing Group supported by the Estonian Research Council via SekMo.

https://www.rightstep-health.com/

contact: mike@rightstep-health.com 

### Offerings and Collaboration
If you are interested in this work then please do get in touch.  

We offer hardware and software to support musculoskeletal research activities particuarly around degnerative bone disorders.

The open source nature of this work invites collaboration so again, please do get in touch if you wish to contribute.

## VAG
VAG is a methodology and technique to "listen" to joints during in active motion.  OsteoSense VAG is initially focused on assessing the knee joint with the goal of classifying knee pathology (osteoarthritis).  The outcome of this work will be two fold, 1. to provide hardware and software tools and 2. to provide a robust methodology and solution to be used in the field.

The technique relies on acceleration signals collected from the knee joint (patella) and processing the captured signal to produce discriminatory features. In addition the angular velocity maybe useful for segmenting flexion / extension.

## Hardware

Currently, the hardware consists of an IMU with a high g accelerometer sampling at 6kHz. https://www.st.com/resource/en/datasheet/lsm6dso32.pdf

The system is developed on the Adafruit Itsybitsy M4 and firmware is developed using the Arduio IDE.
The INO file can be found in the osteosense_hardware directory.

The sensor can operate in stream mode when connected to a usb port or via logging mode which is initiated by a push button. 

[add images][add circuit digram][add code snippets to explain functionality]

## Software
The inital software is a python tkinter desktop application
It allows two core views - stream and analyse. 
It is curently developed and tested on Ubuntu / Windows and other platforms will be tested at a later date

### Stream
The stream view allows data to be streamed from the sensor over USB and is used to test functionality of the sensor and also to provide the ability to observe motion in real time.  

Data stream includes both accleration and angular velocity

### Analyse
WIP

### Modules
- convert
- data_reader
- data_stream
- serial_interface
- processing_pipeline
### Settings
[default settings for the application]
### Components
[structure of the application in terms of views - canvas, stream, analyse]
### Notebooks

NOTE: these are being added to all the time and not updated here.  Check them out!
NOTE: there has been a restrucutre with the addition of ML tests

a set of notebooks for understanding and analyzing VAG signals.  These are all in progress and incomplete but will be continually updated.

|  Notebook|Description  |
|--|--|
| 0.0.vag_intro.ipynb |	  paper highlights|
|0.1.vag.ipynb | book notes|
|0.2.poll_usb.ipynb | polling usb ports|
|0.2.VAG_preliminary_tests.ipynb | analysis of VAG signals |
|1.vag_data_convert.ipynb |converting sensor data |
|2.0.0.vag_explore.ipynb | exploration of VAG analysis methods|
|2.0.1 signal_preprocessing.ipynb| exploration of filters |
|2.1.vag_explore_1khz.ipynb | exploration of <1kHz as per papers|
|3.0.vag_open_data.ipynb | exploration of 89 VAG signals|
|3.0.2.vag_open_data.ipynb | Fractal Index|
|5.0.0.matrix_profiling.ipynb | Intro to Matrix Profiling|




### Features /  Bugs
3. recording is still a bit slow
5. time axis of vag signal graph
7. click to tag ML / L / Patella (get correct names)