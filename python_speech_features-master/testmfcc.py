from features import mfcc
from features import logfbank
import scipy.io.wavfile as wav

def testmfcc(wavfile="../thecatsatonthemat.wav"):
    (rate,sig) = wav.read(wavfile)
    print "rate %s, len(sig) %s"%(rate, len(sig))
    mfcc_feat = mfcc(sig,rate)
    fbank_feat = logfbank(sig,rate)
    return fbank_feat
