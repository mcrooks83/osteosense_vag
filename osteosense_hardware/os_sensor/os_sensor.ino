//Adafruit ItsyBitsy M4
#include <Wire.h> 
#include "SPI.h"
#include "SdFat.h"
#include "Adafruit_TinyUSB.h"
#include "RV-3028-C7.h"
#include "TimeLib.h"
#include <Adafruit_SleepyDog.h>
#include <Adafruit_DotStar.h>
#include <stdint.h>
#include "wiring_private.h" // pinPeripheral() function
//              sercom    miso sck  mosi  tx               rx 
SPIClass mySPI (&sercom0, A5,   A1,  A4,   SPI_PAD_0_SCK_1, SERCOM_RX_PAD_2);

//#define settings SPISettings(10000000, MSBFIRST, SPI_MODE0)
#define settings2 SPISettings(10000000, MSBFIRST, SPI_MODE0)

const int cSelect1 = 4;
const int cSelect2 = 11;

// File system on SD Card
SdFat sd;
File dataFile;
SdFile root;
SdFile file;

// USB Mass Storage object
Adafruit_USBD_MSC usb_msc;

// Set to true when PC write to flash
bool fs_changed;

//dotstar are leds
#define DOTSTAR_NUM        1
#define PIN_DOTSTAR_DATA   8
#define PIN_DOTSTAR_CLK    6
Adafruit_DotStar strip(DOTSTAR_NUM, PIN_DOTSTAR_DATA, PIN_DOTSTAR_CLK, DOTSTAR_BGR);

RV3028 rtc;

//RV-3028-C7 registers
#define RV3028_ADDR            0x52
#define RV3028_STATUS          0x0E
#define RV3028_CTRL1          0x0F
#define RV3028_CTRL2          0x10
#define RV3028_GPBITS         0x11
#define RV3028_INT_MASK         0x12
#define RV3028_EVENTCTRL        0x13
#define RV3028_COUNT_TS          0x14
//Alarm registers
#define RV3028_MINUTES_ALM           0x07
#define RV3028_HOURS_ALM            0x08
#define RV3028_DATE_ALM             0x09


// this will need to be updated when setting the sampling rate via the serial interface
uint32_t sampleRate = 6000; // hZ 

byte enableInt = 0;

const uint16_t bufferSize = 1000;

uint32_t  timeForBuffer = 1;
unsigned long timeBuffer[bufferSize];
uint8_t * ptrTimeBuffer = (uint8_t *) &timeBuffer;

// acceleration data
int16_t   accelerationx[bufferSize];
int16_t   accelerationy[bufferSize];
int16_t   accelerationz[bufferSize];
int16_t   gyrox[bufferSize];
int16_t   gyroy[bufferSize];
int16_t   gyroz[bufferSize];

//int16_t  spiBuffer[3];  // holds 3 values for accleration (6 for gyroscope?)
int16_t   spiBuffer[6];
uint8_t * ptrspiBuffer = (uint8_t *) &spiBuffer;

uint16_t dBufferIn = 0;
uint16_t dBufferOut = 0;

uint8_t regValue;
uint8_t RV3028COUNT;
uint8_t RV3028STATUS;

bool hasUSB = 0;
bool hasSD = 0;
byte shutDown = 0;
String offM;

uint32_t long blinkTime;
uint16_t OnTime = 50;
uint16_t OffTime = 450;
byte oldState = 0;

String filename;


// should be able to rename the sensor potentially which means storing it on disk
String sensorName = "OST-001";



//************************************************************************************************************
//**
// TC3 is a timer interrupt
//**

void TC3_Handler (void) {

  if(enableInt == 1){
    
    //LSM6DSO32 read
    digitalWrite(cSelect2, LOW);
    
      mySPI.transfer(0xA2);  // for gyro (A8 for acceleration)
      //pointer to the spi buffer
      ptrspiBuffer[0] = mySPI.transfer(0x00);
      ptrspiBuffer[1] = mySPI.transfer(0x00);
      ptrspiBuffer[2] = mySPI.transfer(0x00);
      ptrspiBuffer[3] = mySPI.transfer(0x00);
      ptrspiBuffer[4] = mySPI.transfer(0x00);
      ptrspiBuffer[5] = mySPI.transfer(0x00);
      ptrspiBuffer[6] = mySPI.transfer(0x00);
      ptrspiBuffer[7] = mySPI.transfer(0x00);
      ptrspiBuffer[8] = mySPI.transfer(0x00);
      ptrspiBuffer[9] = mySPI.transfer(0x00);
      ptrspiBuffer[10] = mySPI.transfer(0x00);
      ptrspiBuffer[11] = mySPI.transfer(0x00);

    digitalWrite(cSelect2, HIGH);   

      timeBuffer[dBufferIn] = timeForBuffer;

      gyrox[dBufferIn] = spiBuffer[0];
      gyroy[dBufferIn] = spiBuffer[1];
      gyroz[dBufferIn] = spiBuffer[2];
      accelerationx[dBufferIn] = spiBuffer[3];
      accelerationy[dBufferIn] = spiBuffer[4];
      accelerationz[dBufferIn] = spiBuffer[5];

      
      //can gryo be added here?

      timeForBuffer++;
      
      dBufferIn++;
      if (dBufferIn == bufferSize){dBufferIn = 0;}
  }
  TC3->COUNT16.INTFLAG.bit.MC0 = 1; //don't change this, it's part of the timer code
}
//************************************************************************************************************
//Configures the TC to generate output events at the sample frequency.
//Configures the TC in Frequency Generation mode, with an event output once
//each time the audio sample frequency period expires.
 void tcConfigure(void)
{
  // Enable GCLK TC3 (timer counter input clock)
  #if defined(__SAMD51__)
    GCLK->PCHCTRL[TC3_GCLK_ID].reg = GCLK_PCHCTRL_GEN_GCLK1_Val | (1 << GCLK_PCHCTRL_CHEN_Pos); //use clock generator 0
  #else
    GCLK->CLKCTRL.reg = (uint16_t) (GCLK_CLKCTRL_CLKEN | GCLK_CLKCTRL_GEN_GCLK0 | GCLK_CLKCTRL_ID(TC3_GCLK_ID)) ;
    while (GCLK->STATUS.bit.SYNCBUSY == 1);
  #endif

  tc3Reset(); //reset TC3
  
  // Set Timer counter Mode to 16 bits
  TC3->COUNT16.CTRLA.reg |= TC_CTRLA_MODE_COUNT16;
  // Set TC3 mode as match frequency
    #if defined(__SAMD51__)
      TC3->COUNT16.WAVE.bit.WAVEGEN = TC_WAVE_WAVEGEN_MFRQ;
    #else
      TC3->COUNT16.CTRLA.reg |= TC_CTRLA_WAVEGEN_MFRQ;
    #endif
  
  TC3->COUNT16.CTRLA.reg |= TC_CTRLA_PRESCALER_DIV64 | TC_CTRLA_ENABLE;
  //set TC5 timer counter based off of the system clock and the user defined sample rate or waveform
  TC3->COUNT16.CC[0].reg = (uint16_t) (750000 / sampleRate - 1);

  while (tc3IsSyncing());
  
  // Configure interrupt request
  NVIC_DisableIRQ(TC3_IRQn);
  NVIC_ClearPendingIRQ(TC3_IRQn);
  NVIC_SetPriority(TC3_IRQn, 3); //Low priority
  NVIC_EnableIRQ(TC3_IRQn);
  
  // Enable the TC3 interrupt request
  TC3->COUNT16.INTENSET.bit.MC0 = 1;
  while (tc3IsSyncing()); //wait until TC3 is done syncing 
} 
//************************************************************************************************************
//Function that is used to check if TC3 is done syncing
//returns true when it is done syncing

bool tc3IsSyncing()
{
#if defined(__SAMD51__)
  return TC3->COUNT16.SYNCBUSY.reg > 0;
#else
  return (TC3->COUNT16.STATUS.reg & TC_STATUS_SYNCBUSY);
#endif
}
//************************************************************************************************************
//This function enables TC3 and waits for it to be ready
void tc3StartCounter()
{
  TC3->COUNT16.CTRLA.reg |= TC_CTRLA_ENABLE; //set the CTRLA register
  while (tc3IsSyncing()); //wait until snyc'd
}
//************************************************************************************************************
//Reset TC3 
void tc3Reset()
{
  TC3->COUNT16.CTRLA.reg = TC_CTRLA_SWRST;
  while (tc3IsSyncing());
  while (TC3->COUNT16.CTRLA.bit.SWRST);
}
//************************************************************************************************************
//disable TC3

void tc3Disable()
{
  TC3->COUNT16.CTRLA.reg &= ~TC_CTRLA_ENABLE;
  while (tc3IsSyncing());
}
//************************************************************************************
// Callback invoked when received READ10 command.
// Copy disk's data to buffer (up to bufsize) and
// return number of copied bytes (must be multiple of block size)
int32_t msc_read_cb (uint32_t lba, void* buffer, uint32_t bufsize)
{
  bool rc;

#if SD_FAT_VERSION >= 20000
  rc = sd.card()->readSectors(lba, (uint8_t*) buffer, bufsize/512);
#else
  rc = sd.card()->readBlocks(lba, (uint8_t*) buffer, bufsize/512);
#endif

  return rc ? bufsize : -1;
}

// Callback invoked when received WRITE10 command.
// Process data in buffer to disk's storage and 
// return number of written bytes (must be multiple of block size)
int32_t msc_write_cb (uint32_t lba, uint8_t* buffer, uint32_t bufsize)
{
  bool rc;

#if SD_FAT_VERSION >= 20000
  rc = sd.card()->writeSectors(lba, buffer, bufsize/512);
#else
  rc = sd.card()->writeBlocks(lba, buffer, bufsize/512);
#endif

  return rc ? bufsize : -1;
}

// Callback invoked when WRITE10 command is completed (status received and accepted by host).
// used to flush any pending cache.
void msc_flush_cb (void)
{
#if SD_FAT_VERSION >= 20000
  sd.card()->syncDevice();
#else
  sd.card()->syncBlocks();
#endif

  // clear file system's cache to force refresh
  sd.cacheClear();

  fs_changed = true;

  //digitalWrite(LED_BUILTIN, LOW);
}
//************************************************************************************************************

void setup()
{
  pinMode ( cSelect1, OUTPUT );
  digitalWrite ( cSelect1, 1 );
  pinMode ( cSelect2, OUTPUT );
  digitalWrite ( cSelect2, 1 );
  Serial.begin(115200);

  Wire.begin();

  strip.begin(); // Initialize pins for output
  strip.setBrightness(50);
  strip.setPixelColor(0, 0x0000FF);
  strip.show();

  //RV-3028-C7 library must be newer than 2.1.0
  if (rtc.begin(Wire,true,true,true,false) == false) {
    delay(100);
    //Try again
    if (rtc.begin(Wire,true,true,true,false) == false) {
      strip.setPixelColor(0, 0xFF00FF);
      strip.show();
      while ( !Serial ) delay(10); 
      delay(1000);
      Serial.println("RTC not responding");
      while (1) delay(10);
    }

  }

  rtc.set24Hour();
  rtc.updateTime();

  //RTC button setup
  Wire.beginTransmission(RV3028_ADDR);
  Wire.write(RV3028_CTRL2);
  Wire.endTransmission();
  Wire.requestFrom(RV3028_ADDR,1);
  regValue = Wire.read();
  bitSet(regValue, 2) ; //button setup
  bitSet(regValue, 7) ; //button setup
  bitSet(regValue, 3) ; //alarm setup
  Wire.beginTransmission(RV3028_ADDR);
  Wire.write(RV3028_CTRL2);
  Wire.write(regValue);
  Wire.endTransmission();

  Wire.beginTransmission(RV3028_ADDR);
  Wire.write(RV3028_CTRL1);
  Wire.endTransmission();
  Wire.requestFrom(RV3028_ADDR,1);
  regValue = Wire.read();
  bitSet(regValue, 5) ; //alarm setup
  Wire.beginTransmission(RV3028_ADDR);
  Wire.write(RV3028_CTRL1);
  Wire.write(regValue);
  Wire.endTransmission();

  //Set debounce 
  Wire.beginTransmission(RV3028_ADDR);
  Wire.write(RV3028_EVENTCTRL);
  Wire.endTransmission();
  Wire.requestFrom(RV3028_ADDR,1);
  regValue = Wire.read();
  //bitSet(sy, 4) ;
  bitSet(regValue, 5) ;
  Wire.beginTransmission(RV3028_ADDR);
  Wire.write(RV3028_EVENTCTRL);
  Wire.write(regValue);
  Wire.endTransmission();

  //Remember the counter
  Wire.beginTransmission(RV3028_ADDR);
  Wire.write(RV3028_COUNT_TS);
  Wire.endTransmission();
  Wire.requestFrom(RV3028_ADDR,1);
  RV3028COUNT = Wire.read();

  //Remember the status
  Wire.beginTransmission(RV3028_ADDR);
  Wire.write(RV3028_STATUS);
  Wire.endTransmission();
  Wire.requestFrom(RV3028_ADDR,1);
  RV3028STATUS = Wire.read();

  
  if (bitRead(RV3028STATUS, 1 ) == 0 and bitRead(RV3028STATUS, 2 ) == 0) {
    //rtc interupts not set. Powered from usb
    hasUSB = 1;
    //sampleRate5 = 10; 
    //sampleRate4 = 5; 
  }

  //Function to uppdate file timestamps
  SdFile::dateTimeCallback(dateTimeSD);
  
  // Set disk vendor id, product id and revision with string up to 8, 16, 4 characters respectively
  usb_msc.setID("Adafruit", "SD Card", "1.0");

  // Set read write callback
  usb_msc.setReadWriteCallback(msc_read_cb, msc_write_cb, msc_flush_cb);

  // Still initialize MSC but tell usb stack that MSC is not ready to read/write
  // If we don't initialize, board will be enumerated as CDC only
  usb_msc.setUnitReady(false);
  usb_msc.begin();

  if (sd.begin(cSelect1, SD_SCK_MHZ(10)) )
  {
      //Sdcard working.
      hasSD = 1;
  }
  
  mySPI.begin();
  mySPI.beginTransaction(settings2);
  pinPeripheral(A1, PIO_SERCOM_ALT);
  pinPeripheral(A4, PIO_SERCOM_ALT);
  pinPeripheral(A5, PIO_SERCOM_ALT);

  // Size in blocks (512 bytes)
#if SD_FAT_VERSION >= 20000
  uint32_t block_count = sd.card()->sectorCount();
#else
  uint32_t block_count = sd.card()->cardSize();
#endif

  // Set disk size, SD block size is always 512
  usb_msc.setCapacity(block_count, 512);

  // MSC is ready for read/write
  usb_msc.setUnitReady(true);

  fs_changed = true; // to print contents initially

  //Check for time uppdate 
  if (sd.exists("time.txt")) {
    dataFile = sd.open("time.txt");
      String row1 = dataFile.readStringUntil('\n');
      row1.toUpperCase();
      
      if (row1.indexOf("Y")!= -1){
        //time needs uppdating.

        String row2 = dataFile.readStringUntil('\n');

        row2.replace(String(char(11)), "");
        row2.replace(String(char(13)), "");

        String newYear = String(row2.charAt(0)) + String(row2.charAt(1)) + String(row2.charAt(2)) + String(row2.charAt(3));
        String newMonth = String(row2.charAt(5)) + String(row2.charAt(6));
        String newDate = String(row2.charAt(8)) + String(row2.charAt(9));
        String newHour = String(row2.charAt(11)) + String(row2.charAt(12));
        String newMinute = String(row2.charAt(14)) + String(row2.charAt(15));
        String newSecond = String(row2.charAt(17)) + String(row2.charAt(18));

        String fileEnd;
        while (dataFile.available()) {
          fileEnd += char(dataFile.read());
        }

        dataFile.close(); 
        sd.remove("time.txt");
        
        //new time.txt
        String fileNew1;
        fileNew1 += "Update: N";
        fileNew1 += "\r\n";
        fileNew1 += row2;
        fileNew1 += "\r\n";
        fileNew1 += fileEnd;

        rtc.setTime(newSecond.toInt(), newMinute.toInt(), newHour.toInt(), 1 ,newDate.toInt(), newMonth.toInt(), newYear.toInt());
        rtc.updateTime();

        dataFile = sd.open("time.txt", FILE_WRITE);
        dataFile.print(fileNew1);
        dataFile.close(); 
      }else{
        dataFile.close();  
      }
  }

  //generate the file name
  //name mmddhhmmss.csv
  String s_name = sensorName;
  if(rtc.getMonth()<10){s_name += "0";}
  s_name += String(rtc.getMonth() + "_");
  if(rtc.getDate()<10){s_name += "0";}
  s_name += String(rtc.getDate());
  if(rtc.getHours()<10){s_name += "0";}
  s_name += String(rtc.getHours());
  if(rtc.getMinutes()<10){s_name += "0";}
  s_name += String(rtc.getMinutes());
  if(rtc.getSeconds()<10){s_name += "0";}
  s_name += String(rtc.getSeconds());

  //change file extension here to OST for Osteosense
  filename = s_name + ".OST";
  
  // Set the analog reference 
  analogReference(AR_INTERNAL1V0);
  // Set the resolution to 12-bit (0..4095)
  analogReadResolution(12); // Can be 8, 10, 12 or 14

  //Software reset LSM6DSO32
  digitalWrite(cSelect2, LOW);
    mySPI.transfer(0x12); //CTRL3_C
    mySPI.transfer(0x05);
  digitalWrite(cSelect2, HIGH); 

  delay(100);


//default accelerometer config

//    //Accelerometer ODR selection
//    //Accelerometer full-scale selection
//    //No second low-pass filter
  digitalWrite(cSelect2, LOW);
    mySPI.transfer(0x10); //CTRL1_XL
    mySPI.transfer(0xA4); //6.66 kHz ±32 g no filter    to enable 6.66 kHz at +-16g => 0xAC => 0xA4 for +-32g and disabled filter
  digitalWrite(cSelect2, HIGH);  

// default gyroscope config
  digitalWrite(cSelect2, LOW);
    mySPI.transfer(0x11); //CTRL2_G
    mySPI.transfer(0xAC); 
  digitalWrite(cSelect2, HIGH);


  // deals with setting the 2nd filter (low pass or high pass)
  digitalWrite(cSelect2, LOW);
    mySPI.transfer(0x17); //CTRL8_XL (17h)  /selects the register
    //Low-pass filter settings
    //mySPI.transfer(0x00); //odr/4
    //mySPI.transfer(0x20); //odr/10
    //mySPI.transfer(0x40); //odr/20
    //mySPI.transfer(0x60); //odr/45
    //mySPI.transfer(0x80); //odr/100
    //mySPI.transfer(0xA0); //odr/200
    //mySPI.transfer(0xC0); //odr/400
    mySPI.transfer(0xE0); //odr/800 
  digitalWrite(cSelect2, HIGH); 
  
  tcConfigure(); //configure the timer to run at <sampleRate>Hertz
  tc3StartCounter(); //starts the timer

  if(hasUSB == 0){
     strip.setPixelColor(0, 0x00FF00); // think this is blue
     strip.show();
  }
}

//************************************************************************************
/*
 * User provided date time callback function.
 * See SdFile::dateTimeCallback() for usage.
 */
void dateTimeSD(uint16_t* date, uint16_t* time) {
  
  // return date using FAT_DATE macro to format fields
  *date = FAT_DATE(rtc.getYear(), rtc.getMonth(), rtc.getDate());

  // return time using FAT_TIME macro to format fields
  *time = FAT_TIME(rtc.getHours(), rtc.getMinutes(), rtc.getSeconds());
}
//************************************************************************************

// Serial interface 

//comands
enum cmd {SET_ACCEL_RANGE, SET_SAMPLE_FREQUENCY,  IDENTIFY, START_STREAM, STOP_STREAM, GET_SENSOR_NAME};

bool is_streaming = 0; // flag to control streaming in the loop

int parseCommand(String message) {
  if (message.startsWith("SET_ACCEL_RANGE")) {
    return SET_ACCEL_RANGE;
  }
  if(message.startsWith("SET_SAMPLE_FREQUENCY")){
    return SET_SAMPLE_FREQUENCY;
  }
  if(message.startsWith("START_STREAM")){
    return START_STREAM;
  }
  if(message.startsWith("STOP_STREAM")){
    return STOP_STREAM;
  }
  if(message.startsWith("IDENTIFY")){
    return IDENTIFY;
  }
  if(message.startsWith("GET_SENSOR_NAME")){
    return GET_SENSOR_NAME;
  }
  // Add more commands here
  return -1;
}

// re write this so that commands can have values or not
void executeCommand(int command, int value) {
  switch (command) {
    case SET_ACCEL_RANGE:
      setAccelRange(value);
      break;
    case SET_SAMPLE_FREQUENCY:
      setSampleFrequency(value);
      break;
    case START_STREAM:
       if(value == 1){
          startStream();
       }else {
        Serial.println("Error: START_STREAM value incorrect.");
       }
       break;
    case STOP_STREAM:
      if(value == 0){
        stopStream();
      }else{
        Serial.println("Error: STOP_STREAM value incorrect");
      }
      break;
    case IDENTIFY:
      indentify(value);
      break;
    case GET_SENSOR_NAME:
      if(value == 1){
        getSensorName();
      }
      break;
    default:
      Serial.println("Error: Command execution not defined.");
  }
}

void handleCommand(String message) {
  
  int command = parseCommand(message);
  //if the message is known command get the value
  if (command != -1) {
    String valueString = message.substring(message.indexOf(' ') + 1);
    valueString.trim();

    if (valueString.length() > 0 && isNumeric(valueString)) {
      int value = valueString.toInt();
      //Serial.print("Command: ");
      //Serial.print(command);
      //Serial.print(", Value: ");
      //Serial.println(value);
      executeCommand(command, value);
    } else {
      Serial.println("Error: Invalid value for command.");
    }
  } else {
    Serial.println("Error: Unknown command received.");
  }
}

// checks if the value is a number
bool isNumeric(String str) {
  for (byte i = 0; i < str.length(); i++) {
    if (!isDigit(str.charAt(i))) {
      return false;
    }
  }
  return true;
}

// *****************************************************

void getSensorName (){
  Serial.println(sensorName);
}
// functions to set command values
void setAccelRange(int value) {
  //Serial.print("Range has been set to: ");
  //Serial.println(value);
  uint8_t register_value;
  uint8_t range_replacement;
  // keep the first 4 bits
  uint8_t mask = 0xF0;

  //read the register
  digitalWrite(cSelect2, LOW);
    mySPI.transfer(0x10 | 0x80); //CTRL1_XL with read bit set
    register_value = mySPI.transfer(0x00);
    //Serial.print("range currently set is: ");
    //Serial.println(register_value, HEX);  // curently set to A4
  digitalWrite(cSelect2, HIGH); 
  
  register_value &= mask;
  Serial.println(register_value, HEX);  

  // 00 4g, 01 32g 10 8g 11 16g
  if(value == 32){
   range_replacement =  0b0100; // filter remains disabled
   register_value |= range_replacement; // Combine
  }
  else if (value == 16){
    range_replacement = 0b1100;
    register_value |= range_replacement;
  }
  else if(value == 8){
    range_replacement = 0b1000;
    register_value |= range_replacement;
  }
  else if(value == 4){
    range_replacement = 0b0000;
    register_value |= range_replacement;
  }
  else{
    // set to 32g as default
    range_replacement =  0b0100; // filter remains disabled
    register_value |= (range_replacement << 4);
  }
  
  // write the new range to the register
  digitalWrite(cSelect2, LOW);
    mySPI.transfer(0x10); //CTRL1_XL
    mySPI.transfer(register_value);
  digitalWrite(cSelect2, HIGH);  

  // read the register to check what has been written
  /*digitalWrite(cSelect2, LOW);
    mySPI.transfer(0x10 | 0x80); //CTRL1_XL with read bit set
    register_value = mySPI.transfer(0x00);
    //Serial.print("range now set is: ");
    //Serial.println(register_value, HEX);  // curently set to A4
  digitalWrite(cSelect2, HIGH); */
}

//FIX
void setSampleFrequency(int value){
  Serial.print("Sample Frequency set to: ");
  Serial.println(value);
}

void startStream(){
  //Serial.println("starting stream");
  is_streaming = 1;
}

void stopStream(){
  is_streaming = 0;
  //Serial.println("stopping stream");
  
}

void indentify(int value){
  //Serial.print("Indentifying sensor");
  unsigned long startTime = millis(); // Record the start time
  while (millis() - startTime < 5000) { // Loop for 5 seconds (5000 milliseconds)
    strip.setPixelColor(0, 0xFF00FF);   //green 0x00FF00 purple 0xFF00FF
    strip.show();
    delay(100);
    strip.setPixelColor(0, 0x000000);
    strip.show();
    delay(100);

  }
  //Serial.print("Indentifying complete");
  
}

// function to clear all the data from the serial port when the serial command to stop stream is sent
void clearBuffer() {
    while (Serial.available() > 0) {
        //Serial.println("clearing");
        Serial.read();  // Discard all remaining data
        delay(1000);
    }
    //Serial.println("Buffer cleared");
}
//************************************************************************************
void loop()
{

  //First run?
  if (enableInt == 0){
   
    //Create the log file
    if (hasSD and !hasUSB){dataFile = sd.open(filename,FILE_WRITE);}

    //Watchdog.reset();
    blinkTime = millis() + OffTime;
    enableInt = 1;  // stops interrupt accessing SPI if set to 0
  }


  if (blinkTime < millis()){
    //Watchdog.reset();
    if (hasUSB == 0){
      if(oldState == 0){
         blinkTime = blinkTime + OnTime;
         strip.setPixelColor(0, 0x00FF00);
         strip.show();
         oldState = 1;
      }else{
         blinkTime = blinkTime + OffTime;
         strip.setPixelColor(0, 0x000000);
         strip.show();
         oldState = 0;
         
      }
    }
  }
  
  rtc.updateTime();

  //check for button press
  Wire.beginTransmission(RV3028_ADDR);
  Wire.write(RV3028_COUNT_TS);
  Wire.endTransmission();
  Wire.requestFrom(RV3028_ADDR,1);
  regValue = Wire.read();
  
  //button press?
  if(RV3028COUNT!=regValue){
        
        if (hasUSB == 0){
          //putton press detected. turn off.
          shutDown = 1;
          offM = "User";
          enableInt = 0;
        }else{
          //Connected to USB. just clear the RTC starus register. 
          Wire.beginTransmission(RV3028_ADDR);
          Wire.write(RV3028_STATUS);
          Wire.write(0);
          Wire.endTransmission();
        }
  }

  //logging mode
  if (hasUSB == 0){
    if (hasSD){
      while( dBufferIn != dBufferOut){
              
          byte outputA[17];  // 11 bytes 4 for time, 2 each for x,y,z accel (6) + 1 to end the packet. - add 6 bytes for gyro x,y,z
          
          //Generate output;
          outputA[0] = ptrTimeBuffer[dBufferOut * 4 + 3];
          outputA[1] = ptrTimeBuffer[dBufferOut * 4 + 2];
          outputA[2] = ptrTimeBuffer[dBufferOut * 4 + 1];
          outputA[3] = ptrTimeBuffer[dBufferOut * 4 ];
  
          outputA[4] = highByte(accelerationx[dBufferOut]);
          outputA[5] = lowByte(accelerationx[dBufferOut]);
          
          outputA[6] = highByte(accelerationy[dBufferOut]);
          outputA[7] = lowByte(accelerationy[dBufferOut]);
          
          outputA[8] = highByte(accelerationz[dBufferOut]);
          outputA[9] = lowByte(accelerationz[dBufferOut]);

          outputA[10] = highByte(gyrox[dBufferOut]);
          outputA[11] = lowByte(gyrox[dBufferOut]);

          outputA[12] = highByte(gyroy[dBufferOut]);
          outputA[13] = lowByte(gyroy[dBufferOut]);

          outputA[14] = highByte(gyroz[dBufferOut]);
          outputA[15] = lowByte(gyroz[dBufferOut]);
  
          outputA[16] = (0x0B);
  
          if(!dataFile.isOpen()){  dataFile = sd.open(filename,FILE_WRITE);}
          dataFile.write(outputA,sizeof(outputA)); 
              
          dBufferOut ++;
          if (dBufferOut == bufferSize){dBufferOut = 0;}
              
      }
    }

  }else{      

      // messages are structured as a command and a value e.g SET_ACCEL_RANGE 16
      
      if (Serial.available() > 0) {
        String incomingMessage = Serial.readStringUntil('\n');
        incomingMessage.trim();
        
        //Serial.print("Received message: ");
        //Serial.println(incomingMessage);

        handleCommand(incomingMessage);
      }

      //*************** USB STREAM CODE *****************    
      //Usb connected. Stream the data.
      //Send data out 20 lines at time to avoid USB delays.
      if(is_streaming){
          uint16_t Xout = dBufferIn / 20;
          if( Xout * 20 != dBufferOut){
            int16_t  outBuffer[140];
            uint8_t * ptrOutBuffer = (uint8_t *) &outBuffer;
        
            for(uint8_t i = 0; i < 20; i++){
        
              uint8_t outPos = i * 7;//4;
        
              outBuffer[0 + outPos] = (0x0B0B);
              outBuffer[1 + outPos] = accelerationx[dBufferOut + i];
              outBuffer[2 + outPos] = accelerationy[dBufferOut + i];
              outBuffer[3 + outPos] = accelerationz[dBufferOut + i];
              outBuffer[4 + outPos] = gyrox[dBufferOut + i];
              outBuffer[5 + outPos] = gyroy[dBufferOut + i];
              outBuffer[6 + outPos] = gyroz[dBufferOut + i];
            }
        
            Serial.write(ptrOutBuffer,280); //160
            
            dBufferOut = dBufferOut + 20;
            if (dBufferOut == bufferSize){dBufferOut = 0;}
          }

      }
    
  }

      //Shuting down
    if(shutDown == 1){
     strip.setPixelColor(0, 0x000000);
     strip.show();
     if( dataFile.isOpen()){dataFile.close();}
      delay(500);
      Wire.beginTransmission(RV3028_ADDR);
      Wire.write(RV3028_STATUS);
      Wire.write(0);
      Wire.endTransmission();
      delay(500);
    }
}
