import re, sys, os
from terms import *

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

def parseOpSeq(opseq):
    if len(opseq) == 1:
        return opseq[0]
    best = 10000
    top = False
    for x in opseq:
        if x in ops and ops[x] < best:
            best = ops[x]
            top = x
    seq1 = []
    while True:
        x, opseq = opseq[0], opseq[1:]
        if x in ops and ops[x] == best:
            break
        seq1.append(x)
    seq2 = opseq
    if top == "==>":
        return RULE(top, [parseOpSeq(seq1), parseOpSeq(seq2)])
    elif top == "&":
        return CONJUNCTION(top, [parseOpSeq(seq1), parseOpSeq(seq2)])
    else:
        return makeTerm(top, [parseOpSeq(seq1), parseOpSeq(seq2)], vars=vars)
        
ops = {"&":5, "or":6, "==>":4}
atomPattern = re.compile("\s*(?P<atom>(\w+))\s*(?P<rest>.*)", re.DOTALL)

def readAtom(s, indent="", debug=False):
    if debug:
        print "%sreadAtom: s='%s'"%(indent, s)
    m = atomPattern.match(s)
    return m.group("atom"), m.group("rest").strip()

def readTerm(s, brackets=[], indent="", closer=".", debug=False, vars={}):
    if debug:
        print "%sreadTerm: s ='%s', vars=%s"%(indent, s, vars)
    if len(s) > 0 and (s[0] == "(" or s[0] == "["):
        terms, brackets, s = readTerms(s[1:], brackets+[s[0]], indent=indent+" ", closer=s[0], debug=debug, vars=vars)
        if debug: print "bracketed term: terms='%s', brackets='%s', s='%s'"%(terms, brackets, s)
        return terms, brackets, s
    else:
        term, s = readAtom(s, indent=indent+" ", debug=debug)
    if debug:
        print "%sf='%s', s='%s'"%(indent, term, s)
    if s[:len(closer)] == closer:
        if brackets == []:
            return makeTerm(term, [], vars=vars), brackets, s
        raise TermException("End of input: closing bracket required (brackets = %s)"%(brackets))
    if s[0] == "(" or s[0] == "[":
        terms, brackets, s = readTerms(s[1:], brackets+[s[0]], closer=closer, indent=indent+" ", debug=debug, vars=vars)
    else:
        terms = []
    term = makeTerm(term, terms, vars=vars)
    if s[0] in [")", ",", "]"]:
        return term, brackets, s
    return term, brackets, s.strip()

def readTermsAndOps(s, brackets=[], indent="", closer=".", debug=False, vars={}):
    readNextOp = True
    termsandops = []
    while readNextOp:
        if debug: print "%sreadNextOp: s='%s'"%(indent, s)
        term, brackets, s = readTerm(s, brackets=[], indent=indent+" ", closer=closer, debug=debug, vars=vars)
        termsandops.append(term)
        readNextOp = False
        for op in ops:
            if s[:len(op)] == op:
                readNextOp = True
                termsandops.append(op)
                s = s[len(op):].strip()
                break
    if len(termsandops) == 1:
        term = termsandops[0]
    else:
        term = parseOpSeq(termsandops)
    return term, brackets, s
            
def readTerms(s, brackets, closer=".", indent="", debug=False, vars={}):
    if debug:
        print "%sreadTerms s ='%s', vars=%s"%(indent, s, vars)
    terms = []
    while True:
        if debug:
            print "%sread more terms s ='%s'"%(indent, s)
        term, brackets1, s = readTermsAndOps(s, brackets, closer=closer, indent=indent+" ", debug=debug, vars=vars)
        if debug:
            print "%sTerm read: term='%s', s='%s'"%(indent, term, s)
        terms.append(term)
        if s[:len(closer)] == closer:
            raise TermException("End of input: closing bracket or comma required")
        if s[0] == ",":
            s = s[1:].strip()
            continue
        if s[0] == ")" or s[0] == "]":
            if debug:
                print "%slast arg found: terms=%s, s='%s'"%(indent, terms, s)
            return terms, brackets[:-1], s[1:].strip()
        raise TermException("Closing bracket or comma expected, %s found"%(s[0]))

def readterm(s, closer=".", debug=False):
    vars = {}
    t, brackets, s = readTermsAndOps(s, [], closer=closer, debug=debug, vars=vars)
    t.vars = vars
    if not s[:len(closer)] == closer:
        raise TermException("'%s' expected at end of term, '%s' found"%(closer, s))
    if not brackets == []:
        raise TermException("Closing bracket required: %s"%(brackets))
    return t, s
