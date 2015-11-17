from useful import *
from malt import RELATION

POSITION = 0
TAG = 1

HD = 0
TL = 1

def abstractTree(t, f=lambda x: (x.position, x.tag)):
    if type(t) == "WORD":
        return f(t)
    else:
        return [abstractTree(d, f=f) for d in t]

def sortAbstractTree(t, subtrees=False):
    at = [t[HD]]+sorted([sortAbstractTree(d, subtrees=subtrees) for d in t[TL:]])
    if not subtrees == False:
        subtrees[t[HD][POSITION]] = at
    return at

def dense(l):
    l.sort()
    return l == range(l[0], l[-1]+1)

def getStart(t, start=False):
    thdpos = t[HD][POSITION]
    if type(start) == 'bool':
        start = thdpos
    else:
        if thdpos < start:
            start = thdpos
    for d in t[TL:]:
        start = getStart(d, start)
    return start
    
def renumber(t, start=False, words=False):
    if words == False:
        words = []
    if type(start) == 'bool' and start == False:
        start = getStart(t)
    word = (t[HD][POSITION]-start, t[HD][TAG])
    words.append(word)
    t = [word]+[renumber(d, start=start, words=words)[0] for d in t[TL:]]
    return t, words

def dense(words):
    return words[-1][0]-words[0][0] == len(words)-1

def simplifyTree(t, subtrees=False):
    return sortAbstractTree(abstractTree(t), subtrees=subtrees)

def subtrees(t, allst=False):
    if allst == False:
        allst = {}
    if len(t) > 1:
        st, words = renumber(simplifyTree(t))
        words.sort()
        if dense(words):
            incTableN([str([w[1] for w in words]), str((words, st))], allst)
        for d in t[1:]:
            subtrees(d, allst)
    else:
        st = t
    return st

def allsubtrees(trees):
    allst = {}
    for t in trees:
        t.abstractree = subtrees(t.dtree, allst)
    return allst

class DTREE:

    def __init__(self, t):
        self.hd = t[HD]
        self.dtrs = []
        for d in t[TL:]:
            self.dtrs.append(DTREE(d))

    def show(self, indent=''):
        s = '%s%s'%(indent, self.hd)
        for d in self.dtrs:
            s += "\n%s"%(d.show(indent+'  '))
        if indent == '':
            print s
        return s
        
def collectGoodSubtrees(training, threshold=20, precision=0.9):
    allst = allsubtrees(training)
    gst = {}
    for s in allst:
        st = allst[s]
        t = sum(st.values())
        if t > threshold:
            b = getBest(st)
            if float(b[1])/float(t) > precision:
                n = len(eval(b[0])[0])
                if not n in gst:
                    gst[n] = {}
                gst[n][s] = b
    for n in gst:
        for s in gst[n]:
            gst[n][s] = DTREE(eval(gst[n][s][0])[1])
    return gst

"""
training, testing = phrases.makefold(0, 5, sentences)
gst = chunking.collectGoodSubtrees(training, threshold=20, precision=0.99)
c = chunking.CHUNKER(gst)
"""
      
def applyRelations(i, pattern, relations):
    hd = pattern.hd[POSITION]+i
    for d in pattern.dtrs:
        di = d.hd[POSITION]+i
        relations[di] = RELATION(hd, di, "unknown")
        applyRelations(i, d, relations)

class CHUNKER:

    def __init__(self, gst):
        self.gst = gst
    
    def findMatch(self, i, target, relations):
        for n in range(len(self.gst), 1, -1):
            if len(target) >= n:
                starget = str(target[i:i+n])
                """
                try here is test that starget is in gst[n]
                at the same time as actually using it
                """
                try:
                    applyRelations(i, self.gst[n][starget], relations)
                    return
                except:
                    pass

    def findMatches(self, s):
        leaves = [w.tag for w in s.leaves]
        relations = {}
        for i in range(len(leaves)):
            d = self.findMatch(i, leaves, relations)
        s.prels = relations

    def size(self):
        return sum([len(x) for x in self.gst.values()])

