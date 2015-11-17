from useful import *
from word import WORD
from malt import RELATION
from ht import SENTENCE
from tb import showDTree
from forceparse import buildtree
from chunking import simplifyTree, renumber

def abstractTree(t):
    if type(t) == "WORD":
        return WORD(tag=t.tag, position=t.position)
    else:
        return [abstractTree(d) for d in t]

def getOffsets(t, top=False, offsets=False):
    if type(top) == 'bool':
        top = t[0].position
        offsets = []
    if type(t) == "WORD":
        offsets.append([t.position-top, t])
    else:
        for d in t:
            getOffsets(d, top, offsets)
    return offsets

def sortOffsets(offsets):
    left = []
    offsets.sort()
    for i in range(len(offsets)):
        if offsets[i][0] == 0:
            break
        left.append(offsets[i])
    right = offsets[i:]
    offsets = {}
    for i in range(len(left)):
        offsets[left[-(i+1)][1].position] = -(i+1)
    for i in range(len(right)):
        offsets[right[i][1].position] = i
    return offsets
    
def renumber(t, top=False, offsets=False):
    if type(top) == "bool":
        top = t[0].position
        if type(offsets) == "bool":
            offsets = sortOffsets(getOffsets(t))
    if type(t) == "WORD":
        t.position = offsets[t.position]
    else:
        for d in t:
            renumber(d, top=top, offsets=offsets)
    return t

def simplifyTree(t):
    t = abstractTree(t)
    renumber(t)
    return t

def getAncestors(d, relns, ancestors):
    try:
        r = relns[d]
        ancestors.append(r.hd)
        return getAncestors(r.hd, relns, ancestors)
    except:
        return ancestors

def prune(tree, k, ancestors):
    h = [tree[0]]
    if not k == h[0] and h[0].position in ancestors:
        for d in tree[1:]:
            h.append(prune(d, k, ancestors))
    return h
        
def commonancestor(d, r1, r2, leaves):
    ancestors1 = {x:True for x in getAncestors(d, r1, [])}
    ancestors2 = getAncestors(d, r2, [])
    for x in ancestors2:
        if x in ancestors1:
            t1 = abstractTree(prune(subTree(x, r1, leaves), d, ancestors1))
            offsets = sortOffsets(getOffsets(t1))
            t1 = renumber(t1, offsets=offsets)
            d = renumber(abstractTree([leaves[x], [leaves[d]]]), offsets=offsets)
            return (t1, d)
    return False

def commonancestorX(d, r1, r2, leaves):
    ancestors1 = {x:True for x in getAncestors(d, r1, [])}
    ancestors2 = getAncestors(d, r2, [])
    for x in ancestors2:
        if x in ancestors1:
            t1 = subTree(x, r1, leaves)
            d = subTree(x, r2, leaves)
            return (t1, d)
    return False

def subTree(h, relns, words):
    t = [words[h]]
    for r in relns.values():
        if r.hd == h:
            t.append(subTree(r.dtr, relns, words))
    return t

def mismatches(sentence, mismatches=False):
    parsed = sentence.parsed
    goldstandard = sentence.goldstandard
    leaves = sentence.leaves
    for x in parsed:
        if x in goldstandard and not parsed[x].hd == goldstandard[x].hd:
            ca = commonancestor(x, parsed, goldstandard, leaves)
            if ca:
                st1 = showDTree(ca[0])
                rewrite = showDTree(ca[1])
                rule = "%s => %s"%(st1, rewrite)
                cb = commonancestorX(x, parsed, goldstandard, leaves)
                r1 = parsed[x]
                r2 = goldstandard[x]
                positions = [r1.hd, r2.hd, x]
                rule = leaves[min(positions):max(positions)+1]
                for w in rule:
                    if w.position == x:
                        w.mark = "/*"
                    elif w.position == r1.hd:
                        w.mark = "/1"
                    elif w.position == r2.hd:
                        w.mark = "/2"
                    else:
                        w.mark = ""
                rule = " ".join(["%s%s"%(w.tag, w.mark) for w in rule])
                if type(mismatches) == "dict":
                    incTable(rule, mismatches)
                else:
                    print "************************%s%s"%(st1, rewrite)
                                  
                
def allmismatches(sentences):
    mm = {}
    for sentence in sentences:
        mismatches(sentence, mm)
    return sortTable(mm)

class RULE:

    def __init__(self, pattern, d, h1, h2):
        self.pattern = pattern
        self.d = d
        self.h1 = h1
        self.h2 = h2

    def __repr__(self):
        return "%s: %s<%s (%s)"%(" ".join(self.pattern), self.d, self.h2, self.h1)
    
def makerule(pattern):
    tags = []
    pattern = pattern.split(" ")
    for i in range(len(pattern)):
        x = pattern[i].split("/")
        tags.append(x[0])
        if len(x) > 1:
            if x[1] == "*":
                d = i
            elif x[1] == "1":
                h1 = i
            elif x[1] == "2":
                h2 = i
    return RULE(tags, d, h1, h2)

def makerules(sentences):
    rules = {}
    for pattern in allmismatches(sentences):
        if pattern[1] < 11:
            break
        rule = makerule(pattern[0])
        x = rule.pattern[0]
        try:
            rules[x].append(rule)
        except:
            rules[x] = [rule]
    return findGoodRules(sentences, rules)

def scoreRules(sentence, rules, scores=False):
    leaves = sentence.leaves
    tags = [w.tag for w in leaves]
    for i in range(len(tags)):
        w0 = tags[i]
        if w0 in rules:
            for rule in rules[w0]:
                if rule.pattern == tags[i:i+len(rule.pattern)]:
                    d = i+rule.d
                    h2 = i+rule.h2
                    if type(scores) == 'dict':
                        if d in sentence.goldstandard:
                            incTableN([str(rule), str(sentence.goldstandard[d].hd == h2)], scores)
                    else:
                        print sentence.goldstandard[d].hd == h2
                        

def findGoodRules(sentences, rules):
    scores = {}
    for sentence in sentences:
        scoreRules(sentence, rules, scores)
    patterns = {}
    for k in scores:
        sk = scores[k]
        if 'True' in sk:
            t = sk['True']
            if 'False' in sk:
                f = sk['False']
            else:
                f = 0
            if t > 0.7*(f+t):
                patterns[k] = True
    goodrules = {}
    for h in rules:
        gr = []
        for rule in rules[h]:
            if str(rule) in patterns:
                gr.append(rule)
        if not gr == []:
            goodrules[h] = gr
    return goodrules

def applyRulesToSentence(sentence, rules):
    sentence.tbr = {x:sentence.parsed[x] for x in sentence.parsed}
    leaves = sentence.leaves
    tags = [w.tag for w in leaves]
    for i in range(len(tags)):
        w0 = tags[i]
        if w0 in rules:
            for rule in rules[w0]:
                if rule.pattern == tags[i:i+len(rule.pattern)]:
                    d = i+rule.d
                    h2 = i+rule.h2
                    sentence.tbr[d] = RELATION(h2, d)

def applyRulesToSentences(sentences, rules):
    for sentence in sentences:
        applyRulesToSentence(sentence, rules)

def scoreSentence(sentence, whichrels):
    whichrels = whichrels(sentence)
    right = 0
    for r in sentence.goldstandard:
        if r in whichrels and whichrels[r].hd == sentence.goldstandard[r].hd:
            right += 1
    return float(right), float(len(sentence.goldstandard))

def scoreSentences(sentences):
    r0 = 0.0
    t0 = 0.0
    for sentence in sentences:
        r, t = scoreSentence(sentence, lambda x: x.parsed)
        r0 += r
        t0 += t
    r1 = 0.0
    t1 = 0.0
    for sentence in sentences:
        r, t = scoreSentence(sentence, lambda x: x.tbr)
        r1 += r
        t1 += t
    return r0, t0, r1, t1, r0/t0, r1/t1

def errors(r0, r1, leaves):
    s = ""
    for x in r0:
        if not x in r1:
            s += "-> %s<%s,\n"%(leaves[x].form, leaves[r0[x].hd].form)
        elif not r0[x].hd == r1[x].hd:
            s += "%s<%s -> %s<%s,\n"%(leaves[x].form, leaves[r1[x].hd].form, leaves[x].form, leaves[r0[x].hd].form)
    return s.strip()
            
def showChanged(sentences):
    for sentence in sentences:
        if not sentence.tbr == sentence.parsed:
            x0 = scoreSentence(sentence, lambda x: x.tbr)
            x1 = scoreSentence(sentence, lambda x: x.parsed)
            print "**************************************"
            print "Change in accuracy %.3f (%s)"%((x0[0]/x0[1])-(x1[0]/x1[1]), x0[0]-x1[0])
            print showDTree(buildtree(sentence.goldstandard, sentence.leaves))
            print showDTree(buildtree(sentence.tbr, sentence.leaves))
            print errors(sentence.tbr, sentence.goldstandard, sentence.leaves)
            print showDTree(buildtree(sentence.parsed, sentence.leaves))
            print errors(sentence.parsed, sentence.goldstandard, sentence.leaves)

def showErrors(sentences):
    for sentence in sentences:
        if not sentence.goldstandard == sentence.parsed:
            print "**************************************"
            print "GOLD STANDARD"
            print showDTree(buildtree(sentence.goldstandard, sentence.leaves))
            print "PARSED"
            print showDTree(buildtree(sentence.parsed, sentence.leaves))
            print errors(sentence.parsed, sentence.goldstandard, sentence.leaves)
