import pyaudio
import struct
import subprocess
import math
import numpy as np
from scipy.fftpack import fft
import RPi.GPIO as GPIO

CHUNK = 1024 * 2
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

p = pyaudio.PyAudio()
PinLowFreq = 27
PinMidFreq = 14 
PinHighFreq = 17

micVolume = 8 

maxVolume = 120

dutyCycle = 100

GPIO.setmode(GPIO.BCM)
GPIO.setup(PinLowFreq, GPIO.OUT)
GPIO.setup(PinMidFreq, GPIO.OUT)
GPIO.setup(PinHighFreq, GPIO.OUT)

PWMControllerLow = GPIO.PWM(PinLowFreq, dutyCycle)
PWMControllerMid = GPIO.PWM(PinMidFreq, dutyCycle)
PWMControllerHigh = GPIO.PWM(PinHighFreq, dutyCycle)

PWMControllerLow.start(dutyCycle)
PWMControllerMid.start(dutyCycle)
PWMControllerHigh.start(dutyCycle)

stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=True,
    frames_per_buffer=CHUNK
)

x = np.arange(0, 2 * CHUNK, 2)
x_fft = np.linspace(0, RATE, CHUNK)
print(x_fft[int(len(x_fft)/2)])

pastFiveMicSamples = [0,0,0,0,0]

i = 0
x_fft = x_fft[:len(x_fft) // 2]
while True:
    data = stream.read(CHUNK, exception_on_overflow = False)
    data_int = np.array(struct.unpack(str(2 * CHUNK) + "B", data), dtype='b')[::2] #+ 127

    y_fft = fft(data_int) # core algorithm 
    # was temp_fft = np.abs(y_fft[0:CHUNK]) * 2 / (256 * CHUNK)
    y_fft = np.abs(y_fft[0:CHUNK]) * 2 / (256 * CHUNK)

    y_fft = y_fft[:len(y_fft)//2]
    maxVolumeOccurances = np.count_nonzero(data_int >= maxVolume)
    pastFiveMicSamples.pop(4)
    pastFiveMicSamples.insert(0, maxVolumeOccurances)
    mean = 0.0
    for i in range(len(pastFiveMicSamples)):
        mean = mean + pastFiveMicSamples[i]
    mean = mean / 10.0
    if mean >= 10.0 and micVolume != 1:
        pastFiveMicSamples = [0,0,0,0,0]
        micVolume = micVolume - 1
        print("Lowering volume to: " + str(micVolume) + "%")
        subprocess.Popen(['amixer', 'set', 'Micro', str(micVolume) + '%', '>', '/dev/null'], cwd="./")
    elif mean == 0 and micVolume < 8:
        pastFiveMicSamples = [0,0,0,0,0]
        micVolume = micVolume + 1
        print("Increasing volume to: " + str(micVolume) + "%")
        subprocess.Popen(['amixer', 'set', 'Micro', str(micVolume) + '%', '>', '/dev/null'], cwd="./")
    
    frequencyIndexes = np.argsort(y_fft)    # will have the positions of the lowest to highest frequency

    low = 0
    mid = 0
    high = 0
    # now add up the fft values
    for j in range(int(len(x_fft)/8)):
        # now split the frequencies
        if x_fft[frequencyIndexes[-1 * j]] > 20 and x_fft[frequencyIndexes[-1 * j]] < 600:
            low = low + y_fft[frequencyIndexes[-1 * j]] # was (len(x_fft) - j ) #* credit
        elif x_fft[frequencyIndexes[-1 * j]] >= 600 and x_fft[frequencyIndexes[-1 * j]] < 1100:
            mid = mid + y_fft[frequencyIndexes[-1 * j]] # 1 # was (len(x_fft) - j) #* credit
        elif x_fft[frequencyIndexes[-1 * j]] >= 1100 and x_fft[frequencyIndexes[-1 * j]] < 2000:
            high = high + y_fft[frequencyIndexes[-1 * j]] #1 # was (len(x_fft) - j) #* credit

    low = round(low, 5)
    mid = round(mid, 5)
    high = round(high, 5)
    total = low + mid + high
    if total > 0:
        # get the percentage and make the percentage relative to the highest one
        lowPercentage = round((((low / total) * 100.0 * 1) ** 1), 2)
        midPercentage = round((((mid / total) * 100.0 * 1) ** 1), 2)
        highPercentage = round((((high / total) * 100.0 * 1) ** 1), 2)
        if lowPercentage > midPercentage and lowPercentage > highPercentage:
            lowPercentage = (lowPercentage / lowPercentage) * 100
            midPercentage = (midPercentage / lowPercentage) * 100
            highPercentage =  (highPercentage / lowPercentage) * 100

        elif midPercentage > lowPercentage and midPercentage > highPercentage:
            lowPercentage = (lowPercentage / midPercentage) * 100
            midPercentage = (midPercentage / midPercentage) * 100
            highPercentage = (highPercentage / midPercentage) * 100
    
        elif highPercentage > lowPercentage and highPercentage > midPercentage:
            lowPercentage = (lowPercentage / highPercentage) * 100
            midPercentage = (midPercentage / highPercentage) * 100
            highPercentage = (highPercentage / highPercentage) * 100
        
        if lowPercentage < midPercentage and lowPercentage < highPercentage:
            lowPercentage = 0
        elif midPercentage < lowPercentage and midPercentage < highPercentage:
            midPercentage = 0
        elif highPercentage < lowPercentage and highPercentage < midPercentage:
            highPercentage = 0
        

        i = i + 1

        PWMControllerLow.ChangeDutyCycle(lowPercentage)
        PWMControllerMid.ChangeDutyCycle(midPercentage)
        PWMControllerHigh.ChangeDutyCycle(highPercentage)
