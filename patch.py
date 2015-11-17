import re
import word
from useful import *

def match(l, pattern, contn, indent=''):
    if l == pattern:
        contn()
    if pattern == []:
        return
    if type(pattern) == "list":
        if type(l) == "list":
            if pattern[0] == "???":
                match(l, pattern[1:], contn, indent+' ')
                if not l == []:
                    match(l[1:], pattern, contn, indent+' ')
            elif not l == [] and not pattern == []:
                match(l[0], pattern[0], (lambda: match(l[1:], pattern[1:], contn)), indent+' ')
    elif type(pattern) == "str" and pattern[0] == "?":
        contn()
        
class Done(Exception):

    def __init__(self, msg):
        self.msg = msg
        
def done():
    raise Done("done")

def MATCH(l, pattern):
    try:
        match(l, pattern, done)
        return False
    except Done:
        if pattern == []:
            return
        return True

def same(t0, t1):
    print "same(%s, %s)"%(t0, t1)
    if t0 == t1:
        return True
    elif type(t0) == "list" and type(t1) == "list" and not t0 == [] and not t1 == [] and t0[0] == t1[0] and len(t0) == len(t1):
        if allsame(t0[1:], t1[1:]):
            return True
    return False

def subtrees(t, d=0, n=0, st=False):
    if st == False:
        st = {}
    st['%s:%s'%(d, n)]=t
    n = 0
    for x in t[1:]:
        subtrees(x, d=d+1, n=n, st=st)
        n += 1
    return st
        
    
