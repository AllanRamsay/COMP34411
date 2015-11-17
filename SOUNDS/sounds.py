from useful import *
import wave
import struct
from numpy.fft import rfft, irfft
import pylab
import math 
import cv2
from play import play

class SOUND():

    def __init__(self, signal, name="sound", params=False):
        self.signal = signal
        self.name = name
        if params:
            self.params = params
        else:
            self.params = [1, 2, 44100, len(signal), 'NONE', 'not compressed']
            
    def __repr__(self):
        return "SOUND(%s, %s)"%(self.name, self.signal)

    def normalise(self, n=60, dtype="int8"):
        signal = pylab.array(self.signal)-(pylab.ones(len(self.signal))*min(self.signal))
        mx = max(signal)
        return pylab.array(map(lambda x: n*x/float(mx), signal), dtype=dtype)
        
    def save(self, wavfile="temp.wav"):
        self.params[3] = len(self.signal)/2
        bytes = "".join(map(lambda x: chr(int(x)), self.normalise()))
        w = wave.open(wavfile, "w")
        w.setparams(self.params)
        w.setnchannels(1)
        w.writeframes(bytes)
        w.close()

    def play(self):
        self.save("%s.wav"%(self.name))
        play("%s.wav"%(self.name))
        
    def plot(self, show=True, save=False, N=False):
        signal = self.normalise(n=255, dtype="float")
        if N:
            signal = signal[:N]
            print signal[:N]
        ymin, ymax = min(signal), max(signal)
        pylab.ylim(min(ymin-1, int(-0.1*ymin)), max(ymax+1, int(1.1*ymax)))
        pylab.plot(pylab.linspace(0, len(signal), len(signal)), signal)
        if save:
            pylab.savefig("%s.eps"%(self.name))
        if show:
            pylab.show()

def readsound(wavfile="sound1.wav"):
    w = wave.open(wavfile, "r")
    params = list(w.getparams())
    f = w.readframes(w.getnframes())
    w.close()
    return SOUND(pylab.array([ord(b) for b in f], dtype="int8"),
                  name=wavfile,
                  params=params)
  
def zeroxs(l0):
    zeroxs = []
    for i in range(1, len(l0)):
        if (l0[i-1] < 128 and l0[i] >= 128):
            if i%2 == 1:
                i += 1
            zeroxs.append(i)
    return zeroxs

def raisepitch(l0, p=10):
    l1 = []
    for i in range(len(l0)/2):
        if i%p > 0:
            l1.append(l0[2*i])
            l1.append(l0[2*i+1])
    return l1

def lowerpitch(l0, p=10):
    l1 = []
    for i in range(len(l0)/2):
        l1.append(l0[2*i])
        l1.append(l0[2*i+1])
        if i%p == 0:
            l1.append(l0[2*(i-1)])
            l1.append(l0[2*(i-1)+1])
    return l1

def stretch(l0, p=10, g=1000):
    l1 = []
    for i in range(len(l0)/g):
        l1 += l0[i*g:(i+1)*g]
        if i%p == 0:
            l1 += l0[i*g:(i+1)*g]
    return l1

def writecsv(l, out="temp.csv"):
    with safeout(out) as write:
        for x in l:
            write("%s\n"%(x))

def spec(l, g=256):
    """
    Ignore the last element of the result of rfft, because it
    contains general information about the transform, rather than
    an actual value
    """
    return [rfft(l[i:i+g])[:-1] for i in range(0, len(l), g)]

def toPicture(fft, out=sys.stdout, maxheight=False):
    I = len(fft)
    J = len(fft[0])
    if maxheight == False:
        maxheight = J
    a = []
    best = 0
    for i in range(I):
        r = []
        for j in range(maxheight):
            try:
                p = fft[i][j]
                v = math.sqrt(p.real**2+p.imag**2)
                v = abs(p.real)
            except:
                v = 0
            if v > best:
                best = v
            r.append(v)
        a.append(r)
    for r in a:
        for j in range(len(r)):
            r[j] = 255-int(255*r[j]/best)
    a = pylab.array(a)
    return a
    pylab.imshow(a, "gray")
    pylab.show()

def showWav(wav):
    best = 0
    for x in wav:
        if x > best:
            best = x
    wav = [float(10*x)/float(best) for x in wav]
    pylab.plot(wav)
    pylab.show()
        
def testsine(n=64):
    sin = []
    for i in range(n):
        sin.append(math.sin(2*i*math.pi/n)*100)
    return sin

def plotpoints(points):
    img = pylab.zeros((512, 512, 1), pylab.uint8)
    for i in range(1, len(points)):
        p0 = int(points[i-1])+200
        p1 = int(points[i])+200
        cv2.line(img, (i-1, p0), (i, p1), 255,1)
    cv2.imshow('image', img)
    return img

def nontrivial(fft):
    for x in fft:
        for y in x:
            if y.real > 0.001:
                print y
                
