#!/usr/bin/python

import sys
if not '..' in sys.path:
    sys.path.append('..')
if not '/Users/ramsay/python' in sys.path:
    sys.path.append('/Users/ramsay/python')
    
import cgi, cgitb, os, Cookie, re
import socket
from useful import *
import ports, client

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

def saveSettings(page, fields, settings={"start":"0", "end":"10"}):
    for k in fields:
        if k in POST:
            settings[k] = checkPOST(k)
    pattern = 'name="%s" value="%s"'
    for k in settings:
        page = re.compile(pattern%(k, ".*?")).sub(pattern%(k, settings[k]), page)
    return page

def fixChecked(s):
    stage = '<input name="stages" value="%s"'
    for checked in checkPOST("stages").split("&"):
        s = s.replace(stage%(checked), stage%(checked)+' checked="checked"')
    return s

def fixedLayout(s):
    return "<pre>%s</pre>"%(s.replace("\n", "<br>").replace(" ", "&nbsp;"))

if 'parser.py' in sys.argv[0]:
    cgitb.enable()
    global POST, SESSION
    POST = cgi.FieldStorage()
    SESSION = checkCookie()
    data = ""
    if not checkPOST("parseOneSentence") == "":
        text = checkPOST("parseThisSentence")
        if checkPOST("pretag") == "on":
            text = client.askserver("""justTag\txxx
parseThisSentence\t%s"""%(text), ports.PYTHONPORTS)
        else:
            text = "%s.\n"%(text.split(" "))
        ports.log(0, "about to parse %s"%(text))
        data += client.askserver(text, ports.SICSTUSPORTS)
    page = open("parser.html").read()
    page = fixChecked(page)
    page = saveSettings(page, ["parseThisSentence", "start", "end"])
    print """Content-type: text/html

%s
<p>
%s
<p>%s
</body></html>
"""%(page, fixedLayout(data), POST)
