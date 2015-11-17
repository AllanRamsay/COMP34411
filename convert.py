import re, sys, os
from ptp import factsAndRules
from readrules import readterm, ops
from terms import proving, failed, VARIABLE, unify, toList
from useful import *
         
def groupRules(rules):
    functors = {}
    for rule in rules:
        f = rule.consequent.functor
        try:
            functors[f].append(rule)
        except:
            functors[f] = [rule]
    s = ""
    for f in functors:
        print f, functors[f]
        l = functors[f]
        if len(l) > 1:
            for i in range(len(l)):
                l[i].consequent.functor += "_%s"%(i)
        for r in l:
            defn = r.defn()
            print defn
            s += "%s\n"%(defn)
            exec defn in globals()
        if len(l) > 1:
            defn = "def %s(A, CONT, INDENT, RULES):\n    %s\n"%(f, " or ".join(["%s(A, CONT, INDENT, RULES)"%(x.consequent.functor) for x in l]))
            print defn
            exec defn in globals()
        fn = globals()['%s'%(f)]
        fn.src = functors[f]
        fn.defn = defn
        functors[f] = fn
    return functors, s
    
def readFactsAndRules(s=factsAndRules, debug=False):
    factsandrules = []
    while not s == "":
        t, s = readterm(s, ".", debug=debug)
        s = s.strip()[1:]
        factsandrules.append(t)
    return factsandrules

from terms import SUCCESS

def success(g):
    raise SUCCESS(str(g))

def prove(g, r):
    g, s = readterm("%s."%(g))
    if not s == ".":
        raise TermException("XXX")
    print "Proving %s"%(g)
    try:
        r[g.functor](tuple([toList(a) for a in g.args]), (lambda:success(g.args)), '', r)
    except SUCCESS as s:
        print "Proved %s: %s"%(g, s.msg)
        return 
    print "no"
