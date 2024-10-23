#include <Arduino.h>
#include "timers.h"


CTimers::CTimers()
{
}



//************************************************************************************************************
//Configures the TC to generate output events at the sample frequency.
//Configures the TC in Frequency Generation mode, with an event output once
//each time the audio sample frequency period expires.
 void CTimers::tcConfigure(const uint32_t sampleRate) const
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
 //set prescaler and enable TC3
 //TC3->COUNT16.CTRLA.reg |= TC_CTRLA_PRESCALER_DIV256 | TC_CTRLA_ENABLE;
 //set TC3 timer counter based off of the system clock and the user defined sample rate or waveform
 //TC3->COUNT16.CC[0].reg = (uint16_t) (187500 / sampleRate - 1);
 
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

bool CTimers::tc3IsSyncing(void) const
{
#if defined(__SAMD51__)
  return TC3->COUNT16.SYNCBUSY.reg > 0;
#else
  return (TC3->COUNT16.STATUS.reg & TC_STATUS_SYNCBUSY);
#endif
}
//************************************************************************************************************
//This function enables TC3 and waits for it to be ready
void CTimers::tc3StartCounter(void) const
{
  TC3->COUNT16.CTRLA.reg |= TC_CTRLA_ENABLE; //set the CTRLA register
  while (tc3IsSyncing()); //wait until snyc'd
}
//************************************************************************************************************
//Reset TC3 
void CTimers::tc3Reset(void) const
{
  TC3->COUNT16.CTRLA.reg = TC_CTRLA_SWRST;
  while (tc3IsSyncing());
  while (TC3->COUNT16.CTRLA.bit.SWRST);
}
//************************************************************************************************************
//disable TC3

void CTimers::tc3Disable() const
{
  TC3->COUNT16.CTRLA.reg &= ~TC_CTRLA_ENABLE;
  while (tc3IsSyncing());
}
