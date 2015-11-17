#!/usr/bin/python

import socket, sys, re, os
import threading
from useful import *
import log

PYTHONPORTS = 55000
HOST = "localhost"
        
def listen(port=PYTHONPORTS, respond=lambda x: "!!! %s\n"%(x)):
    me = "LISTENER, port %s"%(port)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, port))
    except Exception as e:
        log.log(me, e)
        return
    print "getting socket on port %s"%(port)
    log.log(me, "getting socket on port %s"%(port))
    while True:
        converse(me, s, port, respond)

def converse(me, s, port, respond):
    log.lock("", port)
    s.listen(port)
    log.log(me, "listening for client on %s"%(port))
    conn, addr = s.accept()
    log.lock("%s locked by %s"%(port, conn), port)
    log.log(me, "contacted by %s"%(addr,))
    rcvd = conn.recv(1024)
    conn.sendall(respond(rcvd))
    conn.close()
    log.lock("", port)
    log.log(me, "done")
            
def startservers(startport=PYTHONPORTS, count=5, respond=lambda x: "!!! %s |||"%(x)):
    for port in range(startport, startport+count):
        threading._sleep(1)
        threading.Thread(target=lambda:listen(port=port, respond=respond)).start()
    return startport

if "startservers.py" in sys.argv[0]:
    startservers()
    print "Servers started: lockfiles are %s"%(os.listdir(log.LOCKS))
