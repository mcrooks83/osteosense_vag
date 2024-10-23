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
#include "timers.h"
#include "wiring_private.h" // pinPeripheral() function
//              sercom    miso sck  mosi  tx               rx 
SPIClass mySPI (&sercom0, A5,   A1,  A4,   SPI_PAD_0_SCK_1, SERCOM_RX_PAD_2);

CTimers timers = CTimers();

//#define settings SPISettings(10000000, MSBFIRST, SPI_MODE0)
#define settings2 SPISettings(10000000, MSBFIRST, SPI_MODE0)

//const int chipSelect = 4;

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

#define DOTSTAR_NUM        1
#define PIN_DOTSTAR_DATA   8
#define PIN_DOTSTAR_CLK    6
Adafruit_DotStar strip(DOTSTAR_NUM, PIN_DOTSTAR_DATA, PIN_DOTSTAR_CLK, DOTSTAR_BGR);


RV3028 rtc;

uint32_t sampleRate = 6000; // hZ 
//const int led2 = 13;
//const int debugPin = 5;
byte enableInt = 0;
//byte channel = 0;

const uint16_t bufferSize = 3000;

uint32_t  timeForBuffer = 1;
unsigned long timeBuffer[bufferSize];
uint8_t * ptrTimeBuffer = (uint8_t *) &timeBuffer;

int16_t   accelerationx[bufferSize];
int16_t   accelerationy[bufferSize];
int16_t   accelerationz[bufferSize];

//int16_t   accelerationx2[bufferSize];
//int16_t   accelerationy2[bufferSize];
//int16_t   accelerationz2[bufferSize];

int16_t  spiBuffer[3];
uint8_t * ptrspiBuffer = (uint8_t *) &spiBuffer;

uint16_t dBufferIn = 0;
uint16_t dBufferOut = 0;


uint8_t regValue;
uint8_t RV3028COUNT;
uint8_t RV3028STATUS;

bool hasUSB = 0;
bool hasSD = 0;
byte shutDown = 0;
byte firstRun = 1;
String offM;

const int detectUSB = 12;
const int capControl = 7;

uint32_t long blinkTime;
uint16_t OnTime = 50;
uint16_t OffTime = 450;
byte oldState = 0;

String filename;

String sensorName = "B02";

//************************************************************************************************************
void TC3_Handler (void) {

  //Serial.println(analogRead(A1));

  if(enableInt == 1){
    

  //LSM6DSO32 read
  digitalWrite(cSelect2, LOW);
  
    mySPI.transfer(0xA8);
    
    ptrspiBuffer[0] = mySPI.transfer(0x00);
    ptrspiBuffer[1] = mySPI.transfer(0x00);
    ptrspiBuffer[2] = mySPI.transfer(0x00);
    ptrspiBuffer[3] = mySPI.transfer(0x00);
    ptrspiBuffer[4] = mySPI.transfer(0x00);
    ptrspiBuffer[5] = mySPI.transfer(0x00);


  digitalWrite(cSelect2, HIGH);   

    timeBuffer[dBufferIn] = timeForBuffer;
    accelerationx[dBufferIn] = spiBuffer[0];
    accelerationy[dBufferIn] = spiBuffer[1];
    accelerationz[dBufferIn] = spiBuffer[2];


    timeForBuffer++;
    
    dBufferIn++;
    if (dBufferIn == bufferSize){dBufferIn = 0;}

    //digitalWrite(debugPin, LOW);
    //digitalWrite ( led2, !digitalRead(led2) );
  }
  TC3->COUNT16.INTFLAG.bit.MC0 = 1; //don't change this, it's part of the timer code
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

  //digitalWrite(LED_BUILTIN, HIGH);

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

void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite ( LED_BUILTIN, 0 );
  pinMode ( cSelect1, OUTPUT );
  digitalWrite ( cSelect1, 1 );
  pinMode ( cSelect2, OUTPUT );
  digitalWrite ( cSelect2, 1 );
  pinMode ( A2, INPUT );
  pinMode ( detectUSB, INPUT );
  pinMode ( capControl, OUTPUT );
  digitalWrite ( capControl, LOW );



  pinMode ( A5, INPUT ); //miso
  pinMode ( A1, OUTPUT ); //sck
  pinMode ( A4, OUTPUT ); //mosi



    // Set the analog reference 
  analogReference(AR_INTERNAL2V5);
  // Set the resolution to 12-bit (0..4095)
  analogReadResolution(12); // Can be 8, 10, 12 or 14



  strip.begin(); // Initialize pins for output
  //strip.setBrightness(10);

  //Check for the bat.
  float batV = analogRead(A2) * 1.22L;
  if(batV < 2200){
    //Battery to low.
    strip.setPixelColor(0, 0xFF0000);
    strip.show();
    digitalWrite ( LED_BUILTIN, 1 );
    while ( !Serial ) delay(10);   // wait for native usb
  }else{
    digitalWrite ( capControl, HIGH );
    strip.setPixelColor(0, 0x0000FF);
    strip.show();
  }

  
  
  Serial.begin(115200);
  
  //while ( !Serial ) delay(10);   // wait for native usb

  Wire.begin();




  
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
  



  
  
  //Function to uppdate file timestamps
  SdFile::dateTimeCallback(dateTimeSD);
  
  // Set disk vendor id, product id and revision with string up to 8, 16, 4 characters respectively
  usb_msc.setID("Adafruit", "SD Card", "1.0");

  // Set read write callback
  usb_msc.setReadWriteCallback(msc_read_cb, msc_write_cb, msc_flush_cb);


  if(digitalRead(detectUSB) == 1){
     hasUSB = 1;
  }



    if (sd.begin(cSelect1, SD_SCK_MHZ(10)) )
  {
      //Sdcard working.
      hasSD = 1;
  }


  if(hasUSB == 1 and hasSD == 1)  {
      // Still initialize MSC but tell usb stack that MSC is not ready to read/write
      // If we don't initialize, board will be enumerated as CDC only
      usb_msc.setUnitReady(false);
      usb_msc.begin();
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
    dataFile.setTimeout(100);
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
  if(rtc.getMonth()<10){sensorName += "0";}
  sensorName += String(rtc.getMonth());
  if(rtc.getDate()<10){sensorName += "0";}
  sensorName += String(rtc.getDate());
  if(rtc.getHours()<10){sensorName += "0";}
  sensorName += String(rtc.getHours());
  if(rtc.getMinutes()<10){sensorName += "0";}
  sensorName += String(rtc.getMinutes());
  if(rtc.getSeconds()<10){sensorName += "0";}
  sensorName += String(rtc.getSeconds());


  filename = sensorName + ".HIG";

  

    //Read the config file
    int rectime;
    if (sd.exists("config.txt")) {
      String row;
      dataFile = sd.open("config.txt");
        dataFile.setTimeout(10);
        while (dataFile.available()) {
          row = dataFile.readStringUntil('\n');
          row.trim();
          byte fistOne = row.charAt(0);






          
        }
      dataFile.close();

      row += "FF=";
      row.toLowerCase();
      row.replace(";", "");
      row.replace(" ", "");
      row.replace("\n", "");
      row.replace("\r", "");
      row.replace("\t", "");
      row.replace("-", "");
      row.replace("recordtime(min):","RT=");
      row.replace("triggervalue(g):","TV=");

      //deBug = row;
      
      String varName;
      int varStart;
      int varEnd;
      String varValue;
      //int varInt;
      
      varName = "RT=";
      varStart = row.indexOf(varName);
      if( varStart != -1){
        varStart = varStart + 3;
        varEnd = row.indexOf("=",varStart);
        varEnd = varEnd - 2;
        varValue = row.substring(varStart, varEnd);
        rectime = varValue.toInt();
        //recordTime = rectime;
        //recordTime = recordTime * sampleRate4 * 60;
      }

      varName = "TV=";
      varStart = row.indexOf(varName);
      if( varStart != -1){
        varStart = varStart + 3;
        varEnd = row.indexOf("=",varStart);
        varEnd = varEnd - 2;
        varValue = row.substring(varStart, varEnd);
        //triggerValue = varValue.toInt();
      }

    }


    
  //Software reset LSM6DSO32
  digitalWrite(cSelect2, LOW);
    mySPI.transfer(0x12); //CTRL3_C
    mySPI.transfer(0x05);
  digitalWrite(cSelect2, HIGH); 

  delay(10);


//    //Accelerometer ODR selection
//    //Accelerometer full-scale selection
//    //No second low-pass filter
//  digitalWrite(cSelect2, LOW);
//    mySPI.transfer(0x10); //CTRL1_XL
//    mySPI.transfer(0xA4); //6.66 kHz ±32 g
//  digitalWrite(cSelect2, HIGH); 


//    //Accelerometer ODR selection
//    //Accelerometer full-scale selection
//    //Enable second low-pass filter
//  digitalWrite(cSelect2, LOW);
//    mySPI.transfer(0x10); //CTRL1_XL
//    mySPI.transfer(0xA6); //6.66 kHz ±32 g
//  digitalWrite(cSelect2, HIGH); 

//    //Accelerometer ODR selection
//    //Accelerometer ±4 g selection
//    //Enable second low-pass filter
//  digitalWrite(cSelect2, LOW);
//    mySPI.transfer(0x10); //CTRL1_XL
//    mySPI.transfer(0xA2); //6.66 kHz ±4 g
//  digitalWrite(cSelect2, HIGH); 

    //Accelerometer ODR selection
    //Accelerometer ±4 g selection
    //No second low-pass filter
  digitalWrite(cSelect2, LOW);
    mySPI.transfer(0x10); //CTRL1_XL
    mySPI.transfer(0xA0); //A0 6.66 kHz ±4 g AC 16g A4 32 g
  digitalWrite(cSelect2, HIGH); 
//
//
// //delay(100);
// 
  digitalWrite(cSelect2, LOW);
    mySPI.transfer(0x17); //CTRL8_XL (17h)
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
  

  
  timers.tcConfigure(sampleRate); //configure the timer to run at <sampleRate>Hertz
  timers.tc3StartCounter(); //starts the timer

    rtc.setBackupSwitchoverMode(1);
    rtc.disableTrickleCharge();
  //rtc.enableTrickleCharge(TCR_3K);




  //int countdownMS = Watchdog.enable(10000);
    
}

//************************************************************************************







//************************************************************************************
void loop()
{


  //First run?
  if (firstRun == 1){
   
    //Create the log file
    if (hasSD and !hasUSB){dataFile = sd.open(filename,FILE_WRITE);}

    //Watchdog.reset();
    firstRun = 0;
    blinkTime = millis() + OffTime;


   
    enableInt = 1;
  }


  if (blinkTime < millis()){
    //Watchdog.reset();
      rtc.updateTime();
      //if(oldState == 0){
      if(bitRead(oldState, 0)){
         blinkTime = blinkTime + OnTime;
         float batV = analogRead(A2) * 1.22L;
         if (digitalRead(detectUSB) == 1){
            //running on USB power. Blink blue
            strip.setPixelColor(0, 0x0000FF);
            strip.show();
         }else{
            if(batV > 2400){
              //Running on Battery and logging. Blink green
              strip.setPixelColor(0, 0x00FF00);
              strip.show();;  
            }else{
              //Battery is running low. Still logging. Blink red
              strip.setPixelColor(0, 0xFF0000);
              strip.show();
            }
            if(batV < 2200){
              //Battery to low or switched off.
              enableInt = 0;
              shutDown = 1;
              oldState = 19;
              //digitalWrite ( LED_BUILTIN, 1 );
            }
         }
         oldState ++;
         if (oldState == 20){
            oldState = 0;
            //this runs on 10 blink.
            //Save log.
            if(hasSD and !hasUSB){
              //String lfHeader;
              //if (!sd.exists(bootLogName.c_str())) {lfHeader = "Filename,Time,RecordTime,Pressure,Temp,BatVoltage,End";}
              if( dataFile.isOpen()){dataFile.close();}
//              dataFile = sd.open("LogFile.txt",FILE_WRITE);
//                //dataFile.println(lfHeader);
//                //dataFile.print(sensorName);
//                //dataFile.print(",");
//                dataFile.print(rtc.getYear());
//                dataFile.print("/");
//                dataFile.printf("%02d", rtc.getMonth());
//                dataFile.print("/");
//                dataFile.printf("%02d", rtc.getDate());
//                dataFile.print(" ");
//                dataFile.printf("%02d", rtc.getHours());
//                dataFile.print(":");
//                dataFile.printf("%02d", rtc.getMinutes());
//                dataFile.print(":");
//                dataFile.printf("%02d", rtc.getSeconds());
//                dataFile.print(" ");
//                dataFile.print(batV);
//                dataFile.println("");
//              dataFile.close();
            }
            
         }
         //oldState = 0;
      }else{
         blinkTime = blinkTime + OffTime;
         strip.setPixelColor(0, 0x000000);
         strip.show();
         oldState ++;
         //oldState = 1;
         
      }
  }

  



  if(shutDown == 1){
     strip.setPixelColor(0, 0xFF0000);
     strip.show();
     if( dataFile.isOpen()){dataFile.close();}
     delay(100);
     digitalWrite(capControl,LOW);
     delay(1000);

     while ( !Serial ) delay(10);   // wait for native usb
  }
 


  if (hasUSB == 0){

    if (hasSD){
      while( dBufferIn != dBufferOut){
              
          byte outputA[11];
          
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
  
          outputA[10] = (0x0B);
  
          if(!dataFile.isOpen()){  dataFile = sd.open(filename,FILE_WRITE);}
          dataFile.write(outputA,sizeof(outputA)); 
              
          dBufferOut ++;
          if (dBufferOut == bufferSize){dBufferOut = 0;}
              
      }
    }

              
  }else{  

//        //print time
//        Serial.println("");
//        Serial.print(rtc.getYear());
//        Serial.print("/");
//        Serial.printf("%02d", rtc.getMonth());
//        Serial.print("/");
//        Serial.printf("%02d", rtc.getDate());
//        Serial.print(" ");
//        Serial.printf("%02d", rtc.getHours());
//        Serial.print(":");
//        Serial.printf("%02d", rtc.getMinutes());
//        Serial.print(":");
//        Serial.printf("%02d", rtc.getSeconds());
    
      //Usb connected. Stream the data.
      //Send data out 20 lines at time to avoid USB delays.
      uint16_t Xout = dBufferIn / 20;
      if( Xout * 20 != dBufferOut){
    
     
        int16_t  outBuffer[80];
        uint8_t * ptrOutBuffer = (uint8_t *) &outBuffer;
    
        for(uint8_t i = 0; i < 20; i++){
    
          uint8_t outPos = i * 4;
    
          outBuffer[0 + outPos] = (0x0B0B);
    
          outBuffer[1 + outPos] = accelerationx[dBufferOut + i];
          outBuffer[2 + outPos] = accelerationy[dBufferOut + i];
          outBuffer[3 + outPos] = accelerationz[dBufferOut + i];
    
        }
    
        Serial.write(ptrOutBuffer,160); 
        
        dBufferOut = dBufferOut + 20;
        if (dBufferOut == bufferSize){dBufferOut = 0;}
      }
    
  }




    

    





}
