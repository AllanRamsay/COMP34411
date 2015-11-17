
import scipy.io.wavfile as wav
import base
import sigproc
import pylab
reload(base)
reload(sigproc)

def test(wavfile="../../thecatsatonthemat.wav"):
    (rate, sig) = wav.read(wavfile)
    print "rate %s, len(sig) %s"%(rate, len(sig))
    presig = sigproc.preemphasis(sig)
    print len(presig)
    wav.write("temp.wav", rate, pylab.array(presig, dtype='int16'))
    mfcc_feat = base.mfcc(sig, rate)
    return mfcc_feat
    fbank_feat = base.logfbank(sig,rate)
    return fbank_feat

def gensig(n):
    s = 1.0/float(n)
    return [i for i in range(n)]+[n-i for i in range(n)]
