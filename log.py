
import datetime
from useful import *
import sys

LOGS = "LOGS"
LOCKS = "LOCKS"

def lockfile(port):
    return "%s/lock%s"%(LOCKS, port)

def lock(msg, port):
    with safeout(lockfile(port)) as out:
        out(msg)

def log(who, msg):
    with safeout("%s/log"%(LOGS), mode="a") as out:
        msg = "%s at %s: %s\n"%(who, datetime.today().isoformat(' '), msg)
        if sys.argv[0] == "":
            print msg
        out(msg)
