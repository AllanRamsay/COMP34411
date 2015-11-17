"""
Stuff for making transfer rules out of parse trees.

We assume that the parse trees have been converted to a form where a
terminal node is a pair [FORM, TAG]: simplify will convert the output
of fp.parse to this form, tree2pattern produces a string without any
quote marks in it from the simplified form of the tree:

>>> tree = COMP34411.fp.parse("X is a man", clsf, tagger)
>>> tree
[word(is, VB, position=1), [word(X, PN, position=0)], [word(man, NN, position=3), [word(a, DT, position=2)]]]
>>> makerules.tree2pattern(tree)
'[[is, VB], X, [[man, NN], a]]'

We can take this and edit it to be a rule: replace things that you
don't care about by pattern variables (not to be confused with logical
variables), replace sequences of stuff that isn't to be changed by
..., construct the RHS by hand.

[[is, VB], ?X, [[?N, NN], ...]] ==> [[?N, NN], ..., ?X]

(this will turn "X is a man" into [man, a, X], which might be a better form for
making actual inference rules with because we can then index it on "man")

This can then be turned into a rule that can be applied to a tree to
produce a new tree. Rules are applied recursively to subtrees before
they are applied to trees, and are applied in priority order. For MT,
we need a set of lexical rules of the same kind, but there's no reason
why you couldn't make those from a bilingual dictionary. Patterns with
sequence-variables have to be dealt with non-deterministically, but
that's a price you have to pay if you want to do complicated things.

>>> r = makerules.PATTERN("man ==> homme")
>>> r.match([['man']])
[['homme']]

To convert a complete set of rules like the ones in testrules below, do

>>> rdict, rlist = makerules.makeRules(makerules.testrules)

rdict is a collection of lexical rules, indexed on the lexical
item. rlist is a set of structural rules.
"""

from COMP34411 import fp
import re, sys
from useful import *

def simplify(tree, top=True):
    tree = [[tree[0].root, tree[0].tag]] + [simplify(subtree, False) for subtree in tree[1:]]
    return tree


"""
A pattern looks like

[?A, ..., [?B, ??C, ?D], ...] ==> [?B, ??C, [?A, ..., ?D, ...]]

where ?X denotes a named single item to be matched, ??Y denotes a named arbitrary sequence of items to be matched,
... denotes an unnamed arbitrary sequence of items. ... patterns are renamed in tree traversal order.

"""

itemPattern = re.compile("(?P<item>(\?\?[a-zA-Z0-9]*)|(\?[a-zA-Z0-9]*)|(\.\.\.)|\w*)\s*(?P<rest>.*)$", re.DOTALL)
def readList(s, brackets="", indent=""):
    s = s.strip()
    if s[0] == "[":
        terms = []
        s = s[1:]
        while not s[0] == "]":
            term, s = readList(s, brackets+"[", indent+" ")
            terms.append(term)
        s = s[1:]
        if s == "" or s[0] == ",":
            s = s[1:].strip()
        return terms, s
    else:
        m = itemPattern.match(s)
        if m:
            item = m.group("item")
            s = m.group("rest").strip()
            if s == "" or s[0] == ",":
                s = s[1:].strip()
            return item, s
        else:
            raise Exception("pattern item expected: %s"%(s))

def fixAnonSequences(l0, n=0):
    if type(l0) == "list":
        l1 = []
        for x in l0:
            x, n = fixAnonSequences(x, n)
            l1.append(x)
        return l1, n
    else:
        if l0 == "...":
            return "??V%s"%(n), n+1
        else:
            return l0, n

def tree2pattern(tree):
    s = str(simplify(tree))
    return s.replace("'", "").replace('"', '')

def bind(v, x, vars, contn):
    if v in vars:
        if vars[v] == x:
            contn()
    else:
        vars[v] = x
        contn()
        del vars[v]
        
vpattern = re.compile('\?\w*')
def match(pattern, tree, vars, contn, indent=''):
    print "%smatch(%s, %s, %s)"%(indent, pattern, tree, vars)
    if pattern == tree:
        contn()
        return
    if pattern == [] or tree == []:
        return
    if type(pattern) == "str":
        vpattern.match(pattern) and bind(pattern, tree, vars, contn)
        return
    if type(tree) == "list" and type(pattern) == "list":
        hd = pattern[0]
        if hd[:2] == "??":
            for i in range(len(tree)+1):
                prefix = tree[:i]
                remainder = tree[i:]
                bind(hd, prefix, vars, lambda:match(pattern[1:], remainder, vars, contn, indent=indent+' '))
        else:
            match(hd, tree[0], vars, lambda:match(pattern[1:], tree[1:], vars, contn, indent=indent+' '), indent=indent+' ')

class SUCCESS(Exception):

    def __init__(self):
        pass

def succeeded():
    raise SUCCESS()
    
def doMatch(pattern, tree):
    vars = {}
    try:
        match(pattern, tree, vars, succeeded)
    except SUCCESS as success:
        return vars
    return False

def applyvars(vars, tree):
    if type(tree) == "list":
        tree1 = []
        for t in tree:
            if isstring(t) and t[:2] == "??":
                tree1 += vars[t]
                continue
            if isstring(t) and t[:2] == "?":
                tree1.append(vars[t])
                continue
            tree1.append(applyvars(vars, t))
        return tree1
    else:
        try:
            return vars[tree]
        except:
            return tree

def getVars(tree, vars=False):
    if vars == False:
        vars = {}
    if type(tree) == "list":
        for dtr in tree:
            getVars(dtr, vars)
    elif type(tree) == "str" and tree[0] == "?":
        vars[tree] = True
    return vars

class PATTERN:

    def __init__(self, p):
        p = p.split("==>")
        self.pattern = fixAnonSequences(readList(p[0])[0])[0]
        self.result = fixAnonSequences(readList(p[1])[0])[0]
        self.checkVars(self.result, getVars(self.pattern))

    def checkVars(self, t, vars):
        if type(t) == "list":
            for x in t:
                self.checkVars(x, vars)
        elif type(t) == "str" and t[0] == "?":
            if not t in vars:
                raise Exception("%s in result (%s) not in target (%s)"%(t, self.result, self.pattern))

    def __repr__(self):
        return "%s ==> %s"%(self.pattern, self.result)

    def match(self, tree):
        if type(tree) == "list":
            tree = [self.match(dtr) for dtr in tree]
        vars = doMatch(self.pattern, tree)
        if not vars == False:
            return applyvars(vars, self.result)
        else:
            return tree

def makeRules(rules):
    rdict = {}
    rlist = []
    for r in rules.split(";"):
        r = PATTERN(r)
        p = r.pattern
        if type(p) == "str":
            try:
                rdict[p].append(r)
            except:
                rdict[p] = [r]
        else:
            rlist.append(r)
    return rdict, rlist

testrules = """
[[is, VB], ?X, [[?N, NN], ...]] ==> [[?N, NN], ..., ?X];
man ==> homme
"""
