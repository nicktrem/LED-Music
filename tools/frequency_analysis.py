import pyaudio
import struct
import numpy as np
from scipy.fftpack import fft
#import matplotlib.pyplot as plt

# %plt tk

CHUNK = 1024 * 2 # was 2
FORMAT = pyaudio.paInt16 # was paInt18
CHANNELS = 1
RATE = 44100 # was 44100

p = pyaudio.PyAudio()

stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=True,
    frames_per_buffer=CHUNK
)

#plt.ion()
#fig, (ax, ax2) = plt.subplots(2, figsize=(15,8))

x = np.arange(0, 2 * CHUNK, 2)
x_fft = np.linspace(0, RATE, CHUNK)
print(x_fft[int(len(x_fft)/2)])

#line, = ax.plot(x, np.random.rand(CHUNK))
#line_fft, = ax2.semilogx(x_fft, np.random.rand(CHUNK), '-', lw=2)
#ax.set_ylim(-256, 256)
#ax.set_xlim(0, CHUNK)

#ax2.set_xlim(20, RATE / 2)
i = 0
x_fft = x_fft[:len(x_fft) // 2]
while True:
    # print("Hello")
    data = stream.read(CHUNK, exception_on_overflow = False)
#    print("Done reading: " + str(i))
    data_int = np.array(struct.unpack(str(2 * CHUNK) + "B", data), dtype='b')[::2] #+ 127
#    line.set_ydata(data_int)

    y_fft = fft(data_int)
    # was temp_fft = np.abs(y_fft[0:CHUNK]) * 2 / (256 * CHUNK)
    y_fft = np.abs(y_fft[0:CHUNK]) * 2 / (256 * CHUNK)
#    print(len(y_fft))
    #editedMagnitude = np.append(temp_fft[:70], temp_fft[-20000:])
#    frequencies = np.append(x_fft[:70], x_fft[-20000:])

    y_fft = y_fft[:len(y_fft)//2]
    max = 0.0
    l = 0
    """
    for j in range(CHUNK):
        if max < y_fft[j]: # was editedMagnitude[j]:
            max = y_fft[j] # was editedMagnitude[j]
            l = j
    """
    frequencyIndexes = np.argsort(y_fft)    # will have the positions of the highest to lowest frequency
#    print(frequencyIndexes)
#    print(len(frequencyIndexes))
    low = 0
    mid = 0
    high = 0
 #   print(len(frequencyIndexes))
    #credit = 100
    for j in range(int(len(x_fft) / 8)):
        if x_fft[frequencyIndexes[-1 * j]] > 20 and x_fft[frequencyIndexes[-1 * j]] < 500:
            low = low + y_fft[frequencyIndexes[-1 * j]] # was (len(x_fft) - j ) #* credit
        elif x_fft[frequencyIndexes[-1 * j]] >= 500 and x_fft[frequencyIndexes[-1 * j]] < 3000:
            mid = mid + y_fft[frequencyIndexes[-1 * j]] # 1 # was (len(x_fft) - j) #* credit
        elif x_fft[frequencyIndexes[-1 * j]] >= 3000 and x_fft[frequencyIndexes[-1 * j]] < 17000:
            high = high + y_fft[frequencyIndexes[-1 * j]] #1 # was (len(x_fft) - j) #* credit

    low = round(low, 5)
    mid = round(mid, 5)
    high = round(high, 5)
    #print("low = " + str(low) + " mid = " + str(mid) + " high = " + str(high) + " Highest: " + str(x_fft[frequencyIndexes[-1]]))
    total = low + mid + high
    if total > 0:
        lowPercentage = round((low / total) * 100.0, 2)
        midPercentage = round((mid / total) * 100.0, 2)
        highPrecentage = round((high / total) * 100.0, 2)
        print(str(lowPercentage) + "%\t" + str(midPercentage) + "%\t" + str(highPrecentage) + "%")

    i = i + 1
