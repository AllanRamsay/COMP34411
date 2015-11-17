import scipy
import scipy.fftpack
import pylab
from scipy import pi as PI
from useful import *
import sounds
reload(sounds)

def half(fft):
    return fft[:len(fft)/2]

def normalise(a):
    return (a/float(max(a)))*100

"""
F is period: sample rate is 44100, so f=441 means 100hz
"""

def squarewave(N=44100, f=100, g=10):
    wave = []
    v = False
    w = float(N)/float(f)
    print "frequency = %.2f, wavelength = %.2f"%(f, w)
    for i in range(N):
        if type(v) == "bool":
            v = g
        else:
            if i%(w/2) == 0:
                if v == g:
                    v = 0
                else:
                    v = g
        wave.append(v)
    return sounds.SOUND(wave, name="squarewave-%s-%s"%(f, g))

def square1(N=44100, f=100, g=9):
    w = float(N)/float(f)
    signal = []
    print "frequency = %.2f, wavelength = %.2f"%(f, w)
    for i in range(N):
        x = PI*i/w
        t = 0
        for j in range(1, g+1, 2):
            t += pylab.sin(j*x)/j
        signal.append(10+t*10)
    return sounds.SOUND(signal, name="square1-%s-%s"%(f, g))

def combination(l, N=44100, f=100, g=9):
    w = float(N)/float(f)
    signal = pylab.zeros(N)
    print "frequency = %.2f, wavelength = %.2f"%(f, w)
    for g, a in l:
        t = pylab.linspace(0, f, N)
        acc = lambda t: a*pylab.sin(2*PI*g*t)
        signal += acc(t)
    return sounds.SOUND(signal, name="combination-%s"%("-".join(map(lambda x:"%s-%s"%(x[0], x[1]), l))))
    
def hmax(l):
    h = l[0]
    for x in l:
        h = max(h, x)
    return h

def lastnonzero(l, t=0.05):
    last = len(l)-1
    for i in range(len(l)):
        if l[i] > t:
            last = i
    return l[0:last+1]

def histogram(l, show=True, save=False):
    pylab.xlim(min(-1, int(-0.1*len(l))), max(len(l), int(1.1*len(l))))
    setylimits(l)
    for i in range(len(l)):
        pylab.plot([i, i], [0, int(l[i])], 'k-')
    if save:
        pylab.savefig(save)
    if show:
        pylab.show()

def histograms(l):
    pylab.figure(num=1,figsize=(28,10))
    ffts = []
    for i in range(len(l)):
        pylab.subplot(len(l), 1, i)
        histogram(l[i], show=False)
    pylab.show()

def peaks(l, threshold=10):
    p = []
    for i in range(len(l)):
        if l[i] > threshold:
            p.append(i)
    return p

def setylimits(l):
    ymin = 0
    ymax = 0
    for y in l:
        ymin = min(ymin, y.real)
        ymax = max(ymax, y.real)
    pylab.ylim(min(ymin-1, int(-0.1*ymin)), max(ymax+1, int(1.1*ymax)))

def synth(l=[(1, 100)], n=44000, f=50):
    signal = numpy.zeros(n, dtype='int8')
    for g, a in l:
        t = scipy.linspace(0, f, n)
        acc = lambda t: a*pylab.sin(2*PI*g*t)
        signal = signal+acc(t)
    m = min(signal)
    print "M %s"%(m)
    print signal[:40]
    signal = [int(x-m) for x in signal]
    print signal[:40]
    return pylab.array(signal, dtype="int8")

def multisignals(specs, f=50, n=500):
    signals = []
    pylab.subplots_adjust(hspace=0.4)
    for spec in specs:
        signal = pylab.zeros(n)
        for g, a in spec:
            t = pylab.linspace(0, f, n)
            acc = lambda t: a*pylab.sin(2*PI*g*t)
            signal += acc(t)
        signals.append(signal)
    pylab.figure(num=1,figsize=(28,10))
    ffts = []
    for i in range(len(signals)):
        pylab.subplot(len(l), 2, 2*i+1)
        setylimits(signals[i])
        pylab.plot(t, signals[i])
        pylab.xlabel("plot for %s"%(specs[i],))
        pylab.subplot(len(l), 2, 2*i+2)
        k = half(abs(pylab.fft(signals[i])))
        histogram(k, show=False)
        ffts.append(k)
    pylab.show()
    return signals, ffts

def chunk(fft, f=3):
    m = sum(fft)
    return [sum(fft[i:i+f])/m for i in range(0, len(fft), f)]

def chunks(ffts, f=3):
    return [chunk(x, f=f) for x in ffts]

def csv(ffts):
    for i in range(len(ffts[0])):
        print ("%.2f\t"*len(ffts))%(tuple([x[i] for x in ffts]))

def avFFT(signal, n=256):
    if type(signal) == "SOUND":
        signal = signal.signal
    for i in range(0, len(signal)-n, n):
        ffti = abs(pylab.fft(signal[i:i+n]))
        print sum(ffti)
        try:
            fft += ffti
        except:
            fft = ffti
    return fft
                    
def plotAndSaveandPlaySignal(signal, N, show=False, ofile=False, playIt=False):
    plotsignal(signal[:N], show=show, plotfile=ofile)
    if ofile:
        writeWavFile(signal, wavfile="%s.wav"%(ofile))
        if playIt:
            play("%s.wav"%(ofile))
    
def plotsignals(signals, show=False, plotfile=False):
    l = pylab.sqrt(len(signals))
    x = int(l)+1
    y = int(len(signals)/x)+1
    pylab.subplots_adjust(hspace=0.4)
    for i in range(len(signals)):
        print x, y, i+1
        ax = pylab.subplot(x, y, i+1)
        ax.set_aspect('equal')
        ax.set_xlim(0,10)
        ax.set_ylim(0,10)
    if show:
        pylab.show()
    if plotfile:
        pylab.savefig(plotfile)
    
def thereAndBackAgain(l, n=500, f=50, k=50, showplots=True, save=False):
    fftsum = False
    if showplots or save:
        pylab.figure(num=1,figsize=(18,10))
        """
        subplots_adjust(left, bottom, right, top, wspace, hspace)

        left  = 0.125  # the left side of the subplots of the figure
        right = 0.9    # the right side of the subplots of the figure
        bottom = 0.1   # the bottom of the subplots of the figure
        top = 0.9      # the top of the subplots of the figure
        wspace = 0.2   # horizontal space between subplots
        hspace = 0.5   # vertical space between subplots
        """
        pylab.subplots_adjust(hspace=0.4)
    i = 0
    for g, a in l:
        t = pylab.linspace(0, f, n)
        acc = lambda t: a*pylab.sin(2*PI*g*t)
        signal = acc(t)
        FFT = scipy.fft(signal)
        """
        If there were N points in the signal, then
        there will be N points in the transformed signal
        (if there weren't you wouldn't be able to 
        reconstruct the signal)

        The signal was N points in time T, i.e. scale was
        time. But transform is frequencies: so scale for
        points in transform is 0, ..., 2*PI*N. 

        Why do we get two values? 

        Because sin(A) = sin(2*PI-A), and the FFT doesn't know which it was.
        But actually only the positive one is meaningful, so you can throw away
        the second half.
        """
        if showplots or save:
            pylab.subplot(len(l)+1, 3, 3*i+1)
            setylimits(signal)
            pylab.plot(t, signal)
            pylab.xlabel("input signal %s (f=%.2f, a=%s)"%(i, float(g*f), a))
            pylab.subplot(len(l)+1, 3, 3*i+2)
            absfft = abs(FFT)
            histogram(absfft[:50], show=False)
            pylab.xlabel("FFT for input signal %s (peaks %s)"%(i, peaks(absfft, threshold=1000)))
            pylab.subplot(len(l)+1, 3, 3*i+3)
            IFFT = scipy.ifft(FFT)
            setylimits(IFFT)
            pylab.plot(t,IFFT)
            pylab.xlabel("reconstructed signal from FFT for input signal %s"%(i))
        if i == 0:
            fftsum = FFT
            mixedsignal = signal
        else:
            fftsum += FFT
            mixedsignal += signal
        i += 1
    mixedfft = pylab.ifft(half(fftsum))
    if showplots or save:
        pylab.subplot(len(l)+1, 3, 3*i+1)
        setylimits(mixedsignal)
        pylab.plot(t,mixedsignal, color='r')
        pylab.xlabel("sum of the input signals")
        pylab.subplot(len(l)+1, 3, 3*i+2)
        absfftsum = half(abs(fftsum))
        p = peaks(absfftsum, threshold=hmax(absfftsum)/2)
        # absfftsum = absfftsum[:p[-1]+1]
        histogram(absfftsum[:50], show=False)
        if len(p) < 6:
            pylab.xlabel("sum of the individual FFTs (peaks %s ...)"%(p))
        else:
            pylab.xlabel("sum of the individual FFTs (%s peaks)"%(len(p)))
        pylab.subplot(len(l)+1, 3, 3*i+3)
        setylimits(mixedfft)
        pylab.plot(t[:len(mixedfft)],mixedfft, color='r')
        pylab.xlabel("reconstructed signal from sum of the individual FFTs")
        if save:
            pylab.savefig(save)
        if showplots:
            pylab.show()
  
