# OsteoSense Vibroarthography

OsteoSense Vibroarthograpy (VAG) consists of a dedicated sensor and supporting software to explore VAG signals.  It is a collaboration between Right Step Health and TalTech Environmental Sensing Group supported by the Estonian Research Council via SekMo.


## VAG
VAG is a methodology and technique to "listen" to sounds of joints during in active motion.  OsteoSense VAG is initially focused on assessing the knee joint with the goal of classifying knee pathology (osteoarthritis).  

The technique relies on acceleration signals collected from the knee joint (patella) and processing the captured signal to produce discriminatory features. 

## Hardware

Currently, the hardware consists of an IMU with a high g accelerometer sampling at 6kHz. https://www.st.com/resource/en/datasheet/lsm6dso32.pdf

The system is developed on the Adafruit Itsybitsy M4 and firmware is developed using the Arduio IDE.
The INO file can be found in the osteosense_hardware directory.

The sensor can operate in stream mode when connected to a usb port or via logging mode which is initiated by a push button. 

[add images][add circuit digram][add code snippets to explain functionality]

## Software
The inital software is a python tkinter desktop application
It allows two core views - stream and analyse. 
It is curently developed and test on Ubuntu and other platforms will be tested at a later date

### Stream
The stream view allows data to be streamed from the sensor over USB and is used to test functionality of the sensor and also to provide the ability to observe motion in real time.
### Analyse
Analyse allows  logged data to be exported from the sensor and analysed. (more to come on this)

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
|vag_intensity.ipynb| loading intensity alogirthm from the sensor|
|vag_study.ipynb| ways to analyse a cohort |



