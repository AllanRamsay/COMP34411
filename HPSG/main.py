#!/usr/bin/python

from useful import *
import subprocess
import re

termpattern = re.compile("(?P<term>\w+)")
def prolog2python(s):
    s = s.replace("\n", "").replace("=", ":")
    return termpattern.sub("'\g<term>'", s)
    
def dparse(text):
    p = runprocess(["/usr/local/bin/sicstus", "--goal", "restore('main'), python('%s'), halt."%(text)])
    return rootTree(eval(prolog2python(p[0])))

def rootTree(tree):
    hd = tree[0]['root']
    dtrs = [rootTree(dtr) for dtr in tree[1:]]
    return [hd]+dtrs
