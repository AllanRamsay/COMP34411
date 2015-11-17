#!/usr/bin/python

import socket, sys, re, os, subprocess
import threading, time, datetime
from useful import *
import log

PYTHONPORTS = 55000
HOST = "localhost"

def getPort():
    portPattern = re.compile("lock(?P<port>\d+)")
    for lockfile in sorted(os.listdir(log.LOCKS)):
        try:
            port = int(portPattern.match(lockfile).group("port"))
            if open("%s/%s"%(log.LOCKS, lockfile)).read() == "":
                return(port)
        except:
            pass
    
def askserver(msg):
    me = "client"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for retry in range(20): 
        port = getPort()
        if port:
            break
    if not port:
        return "Could not get server"
    s.connect((HOST, port))
    log.log(me, "connected(%s)"%(port))
    s.sendall(msg)
    wholething = ""
    while True:
        data = str(s.recv(1024))
        if len(data) > 0:
            wholething += str(data)
        else:
            break
    s.close()
    return wholething
    
if "askserver.py" in sys.argv[0]:
    try:
        print askserver(sys.argv[1])
    except:
        print "No query asked"
