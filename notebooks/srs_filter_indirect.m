% srs_filter_indirect

% The procedures are based on Unit 26. Indirect Saturation Removal of Tom Irvine's "Shock and Vibration
% Response Spectra course"

close all
clear accFluctOut
clear accMotionOut

% Assign constants
FSAMP = 2048; % sensor recording frequency in Hz
FSLP = 25; % lowpass filter frequency in Hz, used to remove sensor body motion
FSHP = 20; % highpass filter frequency in Hz, should be <= 20 Hz
FSNYQUIST = FSAMP / 2; % Nyquist sampling frequency in Hz
FSALIAS = 0.6*FSNYQUIST; % Cutoff frequency in Hz <= 0.6FSNYQUIST
SCALE = 0.95; % multiplier used to rescale accelerometer signal data after low pass filter is applied

% Select input data
% BDS
% dataIn = acc_x;
% dataInTime = ts;

%EDF V1
% dataIn = rapid.az;
% dataInTime = ((0:1:size(rapid.tr,1)-1)')./FSAMP;
% N = length(dataIn);

acc_x = edf.ax;
acc_y = edf.ay;
acc_z = edf.az;

% BDS
for it = 1:3

    switch(it)
        case(1)
        dataIn = acc_x;
        case(2)
        dataIn = acc_y;
        case(3)
        dataIn = acc_z;
    end

% Create time data
dt = 1/FSAMP; % time interval size in seconds
timeStop = (size(dataIn,1)-1)/FSAMP;
dataInTime = (0:dt:timeStop)';

% Apply time reversal to signal for phase correction
dataInRev = flip(dataIn,1);

%% STEP 0: Run anti-aliasing filter 
[b,a] = butter(6,FSALIAS/(FSNYQUIST));

[h,w] = freqz(b,a,[],FSAMP);
freqz(b,a,[],FSAMP)

dataInAntiAliasRev = filter(b,a,dataInRev); % apply lowpass filter to reversed signal
dataInAntiAlias = filter(b,a,flip(dataInAntiAliasRev,1)); % flip data along time axis, apply lowpass filter
%%

%% STEP 1: Lowpass filter the acceleration signal with passband set by FSLP
[b,a] = butter(6,FSLP/(FSAMP/2));

[h,w] = freqz(b,a,[],FSAMP);
freqz(b,a,[],FSAMP)
subplot(2,1,1)
ylim([-100 20])

dataOutRev = filter(b,a,flip(dataInAntiAlias,1)); % apply to reversed data for phase correction
dataOut = filter(b,a,flip(dataOutRev)); % invert and refilter
%%

%% STEP 2: Multiply the lowpass filtered data by the scale factor SCALE
dataOut_scaled = SCALE .* dataOut;
%%

%% STEP 3: Substract the scaled data from the original
dataOut_scaled_diff = dataIn - dataOut_scaled;
%%

%% STEP 4: Correct for pre-shock by detrending so that data begins and ends as close to zero as possible
dataOut_scaled_diff_cor = detrend(dataOut_scaled_diff); 
%%

%% STEP 5: Apply highpass filter with passband set by FSHP
dataOut_final = highpass(dataOut_scaled_diff_cor,FSHP,FSAMP);
%%

accFluctOut(:,it) = dataOut_final; % save channel results of fluctuations as array
accMotionOut(:,it) = dataOut_scaled; % save channel results of motion as array

%% Create time, filtered data for SRS
% dataSRS = [dataInTime,dataOut_final];
% timeShockStart = 9.3;
% timeShockStop = 10;
% idxShockStart = find(dataInTime>timeShockStart);
% idxShockStart = idxShockStart(1);
% idxShockStop = find(dataInTime>timeShockStop);
% idxShockStop = idxShockStop(1);
% dataSRS = dataSRS(idxShockStart:idxShockStop,:);
%%

end % end running over all three channels

% figure()
% plot(dataInTime,dataIn,'r');
% hold on
% % plot(dataInTime,dataOut,'r');
% plot(dataInTime,dataOut_scaled,'b','LineWidth',2);
% % plot(dataInTime,dataOut_final,'g');
% plot(dataInTime,dataOut_final,'k','LineWidth',2);
% legend('Raw Signal','Body Motion','Signal Out');
% xlabel('Time (s)');
% ylabel('Acceleration (ms^-2)')

figure()
subplot(2,1,1)
plot(dataInTime,accFluctOut(:,1),'k','LineWidth',2);
hold on
plot(dataInTime,accFluctOut(:,2),'r','LineWidth',2);
plot(dataInTime,accFluctOut(:,3),'b','LineWidth',2);
xlabel('Time (s)');
ylabel('Acceleration (g)');
legend('Acc X Filtered','Acc Y Filtered','Acc Z Filtered')
grid on

subplot(2,1,2)
plot(dataInTime,accMotionOut(:,1),'k','LineWidth',2);
hold on
% plot(dataInTime,acc_x,'k','LineWidth',0.5);
plot(dataInTime,accMotionOut(:,2),'r','LineWidth',2);
% plot(dataInTime,acc_y,'r','LineWidth',0.5);
plot(dataInTime,accMotionOut(:,3),'b','LineWidth',2);
% plot(dataInTime,acc_z,'b','LineWidth',0.5);

xlabel('Time (s)');
ylabel('Acceleration (g)');
grid on
%%

