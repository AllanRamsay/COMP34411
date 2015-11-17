#!/usr/bin/python

import sys
if not '/Users/ramsay/python' in sys.path:
    sys.path.append('/Users/ramsay/python')
    
import cgi, cgitb, os, Cookie, re
import socket
from useful import *
from askserver import askserver
from cgiutilities import *

if 'tagger.py' in sys.argv[0]:
    cgitb.enable()
    global POST, SESSION
    POST = cgi.FieldStorage()
    SESSION = checkCookie()
    data = ""
    data += "<p>POST %s"%(POST)
    data += askserver(tsvPOST(POST))
    page = open("tagger.html").read()
    page = fixChecked(page, POST)
    page = saveSettings(page, ["parseThisSentence", "start", "end"], POST)
    print """Content-type: text/html

%s
<p>
%s
</body></html>
"""%(page, data)
