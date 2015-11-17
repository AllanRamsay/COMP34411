from useful import *

def abstractTree(t):
    if type(t) == "WORD":
        return (t.position, t.tag)
    else:
        return [abstractTree(d) for d in t]

def sortAbstractTree(t):
    return [t[0]]+sorted([sortAbstractTree(d) for d in t[1:]])

def allwords(t):
    if type(t) == "list":
        s = [t[0][0]]
        for x in t[1:]:
            s += allwords(x)
    return s

def dense(l):
    l.sort()
    return l == range(l[0], l[-1]+1)

def renumber(t, start=0):
    if start == 0:
        start = t[0][0]
    return [(start-t[0][0], t[0][1])]+[renumber(d, start) for d in t[1:]]

def subtrees(t, allst=False):
    if allst == False:
        allst = {}
    if len(t) > 1:
        st = str(renumber(sortAbstractTree(abstractTree(t))))
        incTable(st, allst)
        for d in t[1:]:
            subtrees(d, allst)
    return allst

def allsubtrees(trees):
    allst = {}
    for t in trees:
        subtrees(t.dtree, allst)
    return allst
