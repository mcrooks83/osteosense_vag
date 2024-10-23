#ifndef __TIMERS_H__
#define __TIMERS_H__

class CTimers
{
    public:
        CTimers(void);

        void tcConfigure(const uint32_t sampleRate) const;
        void tc3StartCounter(void) const;
        void tc3Disable(void) const;
    private:
        bool tc3IsSyncing(void) const;
        void tc3Reset(void) const;
};

#endif //__TIMERS_H__
