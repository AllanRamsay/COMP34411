"""
PTP.PY

Prolog-style backward chaining theorem prover, using continuations to
manage the backtracking. The key idea here is you pass "the next thing
to do" in as an argument called the "continuation". If you succeed in
the current step, then you call the continuation. In this paradigm,
returning from the current function = failure.

You have to turn the way you think about function calls upside-down:
f(c) will call c if f succeeds, and will return if it doesn't. It's
neat, because it means we can use the Python calling stack to manage
both the calling stack and the backtracking stack for the theorem
prover, but you do have to get used to it.

"""

import re, sys, os
from useful import *

class VARIABLE:

    def __init__(self, name):
        self.name = name
        self.value = "???"
        
    def __repr__(self):
        d = self.deref()
        try:
            return d.name
        except:
            return str(d)

    def deref(v):
        while type(v) == "VARIABLE" and not v.value == "???":
            v = v.value
        return v
    
def deref(t):
    while type(t) == "VARIABLE":
        if t.value == "???":
            return t
        t = t.value
    return t

class SUCCESS(Exception):

    def __init__(self, msg):
        self.msg = msg
        pass

def makeTerm(functor, args, vars={}):
    if args == []:
        try:
            return int(functor)
        except:
            pass
        if functor[0].isupper():
            try:
                return vars[functor]
            except:
                v = VARIABLE(functor)
                vars[functor] = v
                return v
        else:
            return ATOM(functor)
    else:
        return TERM(functor, args)

def tryit(c):
    try:
        c()
        return False
    except SUCCESS as e:
        return True
    except Exception as e:
        print e
        return e
    
def success(g):
    raise SUCCESS(str(g))

def incIndent(INDENT):
    if isinstance(INDENT, str):
        return INDENT+" "
    else:
        return False
    
def match(t1, t2, cont=lambda: success("OK"), INDENT="", hypernyms=False):
    t1 = deref(t1)
    t2 = deref(t2)
    if isinstance(INDENT, str): print "%smatch(%s (%s), %s (%s))"%(INDENT, t1, type(t1), t2, type(t2))
    if t1 == t2:
        if isinstance(INDENT, str):  print "%sidentity: %s, %s"%(INDENT, t1, t2)
        cont()
        return
    if hypernyms and isinstance(t1, str) and isinstance(t2, str):
        if isinstance(INDENT, str):  print "%sboth are strings; %s, %s"%(INDENT, t1, t2)
        if t1 in hypernyms:
            if t2 in hypernyms[t1]:
                if isinstance(INDENT, str):  print "%s%s is subset of %s"%(INDENT, t1, t2)
                cont()
    elif type(t1) == "VARIABLE":
        if isinstance(INDENT, str):  print "%st1 is a variable"%(INDENT)
        t1.value = t2
        cont()
        t1.value = "???"
    elif type(t2) == "VARIABLE":
        if isinstance(INDENT, str):  print "%st1 is a variable"%(INDENT)
        t2.value = t1
        cont()
        t2.value = "???"
    elif isinstance(t1, list) and isinstance(t2, list):
        if isinstance(INDENT, str):  print "%sBoth are lists: %s, %s"%(INDENT, t1, t2)
        if t2 == []:
            cont()
        elif t1 == []:
            return
        else:
            match(t1[0], t2[0], cont=lambda: match(t1[1:], t2[1:], cont=cont, INDENT=INDENT, hypernyms=hypernyms), INDENT=incIndent(INDENT), hypernyms=hypernyms)
            if len(t1) > len(t2):
                hd, t1 = t1[0], t1[1:]
                if isinstance(INDENT, str):  print "%sSkipping over %s: t1 is now %s"%(INDENT, hd, t1)
                match(t1, t2, cont=cont, INDENT=incIndent(INDENT), hypernyms=hypernyms)

def indexRules(rules, hypernyms):
    rdict = {}
    for r in rules:
        h = r[0][0]
        for x in [h]+hypernyms[h].keys():
            try:
                rdict[x].append(r)
            except:
                rdict[x] = [r]
    return rdict

def prolog(goal, rules, cont=lambda: success("OK"), INDENT="", hypernyms=False):
    for lhs, rhs in rules[goal[0]]:
        match(lhs, 
              goal, 
              cont=lambda: prologAll(rhs, rules, INDENT=incIndent(INDENT), cont=cont, hypernyms=hypernyms),
              INDENT = incIndent(INDENT),
              hypernyms=hypernyms)

def prologAll(goals, rules, cont=lambda: success("OK"), INDENT="", hypernyms=False):
    if goals == []:
        cont()
    else:
        prolog(goals[0], 
               rules, 
               cont=lambda: prologAll(goals[1:], rules, INDENT=incIndent(INDENT), cont=cont, hypernyms=hypernyms),
               INDENT = incIndent(INDENT),
               hypernyms=hypernyms)
    
