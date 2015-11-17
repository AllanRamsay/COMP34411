import sys
if not '/Users/ramsay/python' in sys.path:
    sys.path.append('/Users/ramsay/python')

from useful import *

SICSTUSPORTS = 60000
PYTHONPORTS = 55000

def log(port, msg):
    with safeout("/tmp/logserver", "a") as out:
        out("%s: %s\n"%(port, msg))
    
