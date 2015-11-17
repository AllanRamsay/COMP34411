
import Cookie, os, re

def checkCookie():
    cookie = Cookie.SimpleCookie()
    cookie_string = os.environ.get('HTTP_COOKIE')
    if cookie_string:
        cookie.load(cookie_string)
    return cookie

def checkPOST(field, POST):
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

def checkSESSION(field, SESSION):
    if SESSION and field in SESSION:
        x = SESSION[field].value
        if isinstance(x, tuple):
            x = x[0]
        return x.strip()
    else:
        return ""

def tsvPOST(POST):
    return "<P>POSTARGS"+" ".join([x for x in POST])
    return "\n".join(["%s\t%s"%(x, checkPOST(x, POST)) for x in POST])

def saveSettings(page, fields, POST, settings={"start":"0", "end":"10"}):
    for k in fields:
        if k in POST:
            settings[k] = checkPOST(k, POST)
    pattern = 'name="%s" value="%s"'
    for k in settings:
        page = re.compile(pattern%(k, ".*?")).sub(pattern%(k, settings[k]), page)
    return page

def fixChecked(s, POST):
    stage = '<input name="stages" value="%s"'
    for checked in checkPOST("stages", POST).split("&"):
        s = s.replace(stage%(checked), stage%(checked)+' checked="checked"')
    return s
