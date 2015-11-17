#!/usr/bin/python
import re, sys, os
from useful import *
import cgi, cgitb
import Cookie

def checkCookie():
    cookie = Cookie.SimpleCookie()
    cookie_string = os.environ.get('HTTP_COOKIE')
    if cookie_string:
        cookie.load(cookie_string)
    return cookie

header = """
<head>
<meta content="text/html; charset=ISO-8859-1" http-equiv="Content-Type">
<title></title></head>
<body>
<h2 align="center">Test page</h2>
<br>

</body>
"""
if "test" in sys.argv[0]:
    cgitb.enable()
    post = cgi.FieldStorage()
    session = checkCookie()
    print """Content-type: text/html\n%s\n\n%s"""%(session.output(), header)
    sys.stdout.close()

for z in range(100):
    for i in range(1000000):
        j = i
