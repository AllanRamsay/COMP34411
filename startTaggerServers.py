#!/usr/bin/python

import sys
sys.path.append('..')
import socket, threading, time
import regexchunker
reload(regexchunker)
from useful import *
import ports

HOST = ''                 # Symbolic name meaning all available interfaces

def splitTSV(s):
    return {y[0]:y[1] for y in [x.split("\t") for x in s.split("\n")]}
    
def listen(port, mxltagger, sentences):
    print "getting socket on port %s"%(port)
    with safeout("LOCKS/locked%s"%(port)) as out:
        out("setting up port %s\n"%(port))
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, port))
    except Exception as e:
        print e
        return
    while True:
        talkto(s, port, mxltagger, sentences)

def talkto(s, port, mxltagger, sentences):
    s.listen(port)
    ports.log(port, "listening for client on %s"%(port))
    with safeout("LOCKS/locked%s"%(port)) as out:
        out("")
    conn, addr = s.accept()
    with safeout("LOCKS/locked%s"%(port)) as out:
        out("locked")
    ports.log(port, '%s contacted by %s'%(port, addr))
    args = splitTSV(conn.recv(1024))
    try:
        stages = map(int, args['stages'].split("&"))
    except:
        stages = [1,2,3,4,5]
    if 'showWNEntries' in args:
        try:
            start = int(args['start'])
        except:
            start = 0
        try:
            end = int(args['end'])
        except:
            end = 20
        ports.log(port, "analysing sentences from %s to %s"%(start, end))
        sw = stringwriter()
        regexchunker.checksentences(sentences[start:end], mxltagger, outfile=sw, stages=stages)
        conn.sendall(sw.txt)
    elif 'parseOneSentence' in args:
        sentence = args['parseThisSentence']
        ports.log(port, "tagging with HTML output %s"%(sentence))
        sw = stringwriter()
        with safeout(sw) as out:
            regexchunker.checksentence(sentence, out, mxltagger, stages=stages)
        conn.sendall(sw.txt)
    elif 'justTag' in args:
        sentence = args['parseThisSentence']
        ports.log(port, "just tagging %s"%(sentence))
        sw = stringwriter()
        with safeout(sw) as out:
            out("%s.\n"%(regexchunker.justTag(sentence, mxltagger)))
        conn.sendall(sw.txt)
    conn.close()
    print "done"

def testlisten(port):
    print "getting socket on port %s"%(port)
    with safeout("LOCKS/locked%s"%(port)) as out:
        out("setting up port %s\n"%(port))
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, port))
    except Exception as e:
        print e
        return
    while True:
        testtalk(s, port)

def testtalk():
    s.listen(port)
    ports.log(port, "listening for client on %s"%(port))
    with safeout("LOCKS/locked%s"%(port)) as out:
        out("")
    conn, addr = s.accept()
    with safeout("LOCKS/locked%s"%(port)) as out:
        out("locked")
    ports.log(port, '%s contacted by %s'%(port, addr))
    rcvd = conn.recv(1024)
    ports.log(port, "TEST %s"%(rcvd))
    sw = stringwriter()
    regexchunker.checksentences(sentences[start:end], mxltagger, outfile=sw, stages=stages)
    conn.sendal("RESENDING %s"%(rcvd))
    conn.close()
    print "done"
    
def initialiseServer(tagger=False, sentences=False):
    if not tagger:
        print "getting tagger"
        tagger = regexchunker.tag.mxltagger(regexchunker.tag.BNC+"/A/A0", tagsize=2)
        print "tagger OK"
    if not sentences:
        print "getting sentences"
        sentences = regexchunker.allsynsets()
        print "sentences OK"
    return lambda port:listen(port, tagger, sentences)

def initialiseTest():
    return testlisten
    
def startServers(smax=10, setTarget=initialiseServer):
    target=setTarget()
    for port in range(ports.PYTHONPORTS, ports.PYTHONPORTS+smax):
        threading.Thread(lambda:target(port)).start()

if "startTaggerServers" in sys.argv[0]:
    startServers()
