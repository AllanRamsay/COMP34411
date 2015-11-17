#!/usr/bin/python
import subprocess
import sys, os

def play(f0):
    d = os.getcwd()
    p = subprocess.Popen(('/Applications/Praat.app/Contents/MacOS/Praat /Users/ramsay/bin/play.praat %s/%s'%(d, f0)).split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if not p[1] == "":
        print p[1]
    p = subprocess.Popen(('lame %s/%s'%(d, f0)).split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

if 'play.py' in sys.argv[0]:
    play(sys.argv[1])
