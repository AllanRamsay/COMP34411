#!/usr/bin/python
import sys
if not '..' in sys.path:
    sys.path.append('..')
if not '/Users/ramsay/python' in sys.path:
    sys.path.append('/Users/ramsay/python')
import cgi, cgitb, os, Cookie, re
import socket
import ports
from useful import *

def checkCookie():
    cookie = Cookie.SimpleCookie()
    cookie_string = os.environ.get('HTTP_COOKIE')
    if cookie_string:
        cookie.load(cookie_string)
    return cookie

def checkPOST(field):
    if field in POST:
        x = POST[field]
        if isinstance(x, tuple):
            x = list(x)
        if isinstance(x, list):
            x = "&".join(map(lambda i: i.value, x))
        else:
            x = x.value
        return x.strip()
    else:
        return ""

def checkSESSION(field):
    if SESSION and field in SESSION:
        x = SESSION[field].value
        if isinstance(x, tuple):
            x = x[0]
        return x.strip()
    else:
        return ""

def tsvPOST():
    return "\n".join(["%s\t%s"%(x, checkPOST(x)) for x in POST])

def checklockfile(f):
    try:
        return open(f).read() == ""
    except:
        return False
        
def askserver(msg, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = 'localhost'    # The remote host
    while not checklockfile("../locked%s"%(port)):
        port += 1
    ports.log(port, "askserver(%s, %s)"%(port, msg))
    s.connect((host, port))
    ports.log(port, "connected(%s, %s)"%(host, port))
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
