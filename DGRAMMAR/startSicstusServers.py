#!/usr/bin/python

import subprocess, sys, re

if not "/Users/ramsay/python" in sys.path:
    sys.path.append("/Users/ramsay/python")
    
from useful import *

def startSicstusServer(port):
    with safeout("../locked%s"%(port)) as out:
        out("")
    subprocess.Popen(("sicstus -r server.sav --goal startSicstusServer(%s)."%(port)).split(" "))

def startSicstusServers(i=60000, di=10):
    for p in range(i, i+di):
        startSicstusServer(p)

if "startSicstusServers" in sys.argv[0]:
    startSicstusServers()
    
