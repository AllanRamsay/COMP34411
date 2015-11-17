#!/usr/bin/python

import socket, sys, re, os
import threading, time, datetime
from useful import *

PYTHONPORTS = 55000
HOST = "localhost"
LOGS = "LOGS"
LOCKS = "LOCKS"

def lockfile(port):
    return "%s/lock%s"%(LOCKS, port)

def lock(msg, port):
    with safeout(lockfile(port)) as out:
        out(msg)

def log(who, msg):
    with safeout("LOGS/log", mode="a") as out:
        msg = "%s at %s: %s\n"%(who, datetime.today().isoformat(' '), msg)
        print msg
        out(msg)
        
def listen(port=PYTHONPORTS):
    me = "LISTENER, port %s"%(port)
    log(me, "getting socket on port %s"%(port))
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, port))
    except Exception as e:
        log(me, e)
        return
    while True:
        converse(me, s, port)

def converse(me, s, port):
    s.listen(port)
    log(me, "listening for client on %s"%(port))
    conn, addr = s.accept()
    lock("%s locked by %s"%(port, conn), port)
    log(me, "contacted by %s"%(addr,))
    rcvd = conn.recv(1024)
    conn.sendall("RESENDING %s"%(rcvd))
    conn.close()
    lock("", port)
    log(me, "done")
    
def askserver(msg):
    me = "client"
    portPattern = re.compile("lock(?P<port>\d+)")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for lockfile in sorted(os.listdir("LOCKS")):
        try:
            port = int(portPattern.match(lockfile).group("port"))
            if open("LOCKS/%s"%(lockfile)).read() == "":
                break
        except:
            pass
    else:
        log(me, "No empty lock files found")
        try:
            port += 1
            startservers(startport=port) 
        except:
            port = startservers()
    s.connect((HOST, port))
    log(me, "connected(%s)"%(port))
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
            
def startservers(startport=PYTHONPORTS, count=5):
    for port in range(startport, startport+count):
        threading._sleep(1)
        threading.Thread(target=lambda:listen(port=port)).start()
    return startport

if "server.py" in sys.argv[0]:
    print askserver(sys.argv[1])
