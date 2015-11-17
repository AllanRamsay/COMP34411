import re
import sys
import os
from useful import *

"""
sentences, pretagged = ht.alltrees()
"""

METERING = True
PATB = "/Users/ramsay/LDC/ArabicTreeBankPart1V3/data"
class SENTENCE:

    def __init__(self, src, pstree=False, file=False, position=False):
        self.src = src
        self.pstree = pstree
        self.file = file
        self.position = position

    def __repr__(self):
        return "pstree(%s, %s, %s, %s)"%(self.src, self.pstree, self.file, self.position)

    def showPSTree(self):
        print showPSTree(self.pstree)
        
    def showDTree(self):
        print showDTree(self.dtree)

class WORD:

    def __init__(self, form=False, tag=False, position=False, label="unknown"):
        self.form = form
        self.tag = tag
        self.root = form
        self.position = position
        self.label = label

    def __repr__(self):
	s = 'word("%s", %s'%(self.form, self.tag)
	if type(self.position) == 'int':
	    s += ", position=%s"%(self.position)
	return s+")"

    def short(self):
        return '%s:%s:%s'%(self.position,self.form,self.tag)

    """
    Two words match if they have the same form (or the first one
    doesn't have a form, in which case it's an element of a pattern,
    so we're not specifying the form) and its tagPattern matches the
    other word's tag. 
    """
    def match(self, other):
        if self.form and not self.form == other.form:
            return False
        if self.tag:
            return self.tagPattern.match(other.tag)
        return True

def islist(x):
    return x.__class__.__name__ == 'list'

def isstring(x):
    return x.__class__.__name__ == 'str'

def istable(x):
    return x.__class__.__name__ == 'dict'

def countTable(t):
    l = [(t[x], x) for x in t]
    l.sort()
    l.reverse()
    return l

def showPSTree(tree, indent=''):
    if type(tree) == "WORD":
        return tree.short()
    s = tree[0]
    n = len(s)+1
    first = True
    indent = indent+n*(" ")
    for d in tree[1:]:
        if first:
            s += " %s"%(showPSTree(d, indent))
            first = False
        else:
            s += "\n%s%s"%(indent, showPSTree(d, indent))
    return s

def showDTree(tree, indent=''):
    if type(tree) == "WORD":
        return tree.short()
    s = tree[0].short()
    n = 4
    first = False
    indent = indent+n*' '
    for x in tree[1:]:
        x = showDTree(x, indent)
        if first:
            s += '%s'%(x)
            first = False
        else:
            s += "\n%s%s"%(indent, x)
    return s

def getsubtrees(tree, subtreetable={}):
    hd = '%s'%tree[0]
    dtrs = []
    for subtree in tree[2:]:
        dtrs.append('%s'%subtree[0])
        getsubtrees(subtree, subtreetable)
    incTable2(hd, '%s'%(dtrs), subtreetable)

def getallsubtrees(trees):
    subtreetable = {}
    for tree in trees:
        getsubtrees(tree.dtree, subtreetable)
    return subtreetable

sample = 'with-vowel/20000715_AFP_ARB.0001.tree'

def readFile(file):
    return open(file, 'r').read()

"""
Stuff for reading the pos file
"""

wordPattern = re.compile("INPUT STRING(?P<word>.*?)\\n\\n", re.DOTALL)

lemmaPattern = re.compile('.*?INDEX: (?P<index>\S+)\s.*\* SOLUTION.*?\((?P<dform>\S*)\) \[(?P<lemma>.*?)\].*', re.DOTALL)
lemmaPattern1 = re.compile('.*?INDEX: (?P<index>\S+)\s.*?SOLUTION.*?\[(?P<lemma>.*?)\].*', re.DOTALL)
lemmaPattern2 = re.compile('.*LOOK-UP WORD: (?P<lemma>\S+)\s.*', re.DOTALL)

def getWords(s):
    l = [i.group('word') for i in wordPattern.finditer(s)]
    w = []
    for x in l:
        m = lemmaPattern.match(x)
        if m:
            lemma = m.group('lemma')
            if lemma == 'clitics' or lemma == 'DEFAULT':
                lemma = m.group('dform')
                if lemma == '':
                    lemma = "EMPTYSTRING"
            w.append(lemma)
        else:
            """
            words with no preferred sense
            """
            if m:
                m = lemmaPattern1.match(x)
                lemma = m.group('lemma')
                if lemma == 'clitics':
                    lemma = 'YYY'
                w.append(lemma)
            else:
                """
                words with no lemma
                """
                m = lemmaPattern2.match(x)
                if m:
                    w.append(m.group('lemma'))
                else:
                    """
                    words with no preferred sense, no lemma and no surface string! Usually Roman script words
                    """
                    w.append("EMPTYSTRING")
    return w

"""
Read the treebank
"""
terminalPattern = re.compile('(?P<symb>[^\)]*)(?P<rest>\).*)')

labelPattern = re.compile('(?P<label>\S*)\s+(?P<rest>.*)')

def getTrees(f, t=[]):
    s1 = ''
    b = 0
    n = 0
    s0 = readFile(f).replace('"', "Q")
    for i in range(0, len(s0)):
        c = s0[i]
        s1 = s1+c
        if c == '(':
            b = b+1
        elif c == ')':
            b = b-1
            if b == 0:
                s1 = s1.strip()
                if s1[:2] == "(S" and not 'NAC' in s1 and not 'FRAG' in s1:
                    t.append(SENTENCE(s1, file=f, position=n))
                    n += 1
                s1 = ''
    s1 = s1.strip()
    if not s1 == '' and s1[:2] == "(S" and not 'NAC' in s1 and not 'FRAG' in s1:
        t.append(SENTENCE(s1.strip(), file=f, position=n))
    return t

def readTree(s):
    s = s.strip()
    if s[0] == '(':
        s = s[1:]
        l = ''
        while not s[0] == ' ':
            l = l+s[0]
            s = s[1:]
        tree = [l]
        s = s[1:]
        if s[0] == '(':
            while not s[0] == ')':
                dtr, s = readTree(s)
                tree.append(dtr)
            return tree, s[1:]
        else:
            x = ''
            while not s[0] == ')':
                x = x+s[0]
                s = s[1:]
            tree.append(x)
        return tree, s[1:]
    else:
        x = ''
        while not s[0] == ')':
            x = x+s[0]
            s = s[1:]
        return x, s[1:]

def fixICONJ(tree):
    if tree.leaves[0].tag == "CONJ":
        tree.leaves[0].tag = "ICONJ"
                                                        
tracePattern = re.compile('.*-\d+')
def istrace(x):
    return tracePattern.match(x)

def isdummy(x):
    return (islist(x) and len(x) == 1) or (type(x) == "WORD" and "NONE" in x.tag)

def removeDummies(t):
    if islist(t):
        t = [removeDummies(x) for x in t]
        t = [t[0]]+[x for x in t[1:] if not isdummy(x)]
        return t
    else:
        return t

labelPattern = re.compile('(?P<label>.*?)((=\d*)|(\+((NSUFF)|(CASE)|(IV)|(PV)).*))')

reducetagpattern = re.compile("((?P<TAG2>PRON)_.*)|((?P<TAG3>.*NOUN).*)|(.*SUFF.*(?P<TAG4>DO).*)|((?P<TAG1>(I|P|C)V).*)|((?P<TAG5>(POSS|DEM)_PRON).*)|((?P<TAG6>DET+(ADJ|NOUN)).*)")

def reducetag(tag):
    m = reducetagpattern.match(tag)
    if m:
        for g in reducetagpattern.groupindex:
            if m.group(g):
                return m.group(g)
    return tag

def reducetags(tree):
    if isstring(tree):
        return tree
    elif type(tree) == "WORD":
        if tree.form == '.':
            tree.tag = 'FULLSTOP'
        if tree.form == '-LRB-':
            tree.tag = "LRB"
        elif tree.form == '-RRB-':
            tree.tag = "RRB"
        else:
            tree.tag = reducetag(tree.tag)
        return tree
    else:
        rtree = [reducetag(tree[0])]
        for d in tree[1:]:
            rtree.append(reducetags(d))
        return rtree
        
def simplify(x):
    if isstring(x):
        return x
    elif type(x) == "WORD":
        m = labelPattern.match(x.tag)
        if m:
            x.tag = m.group('label')
        return x
    else:
        m = labelPattern.match(x[0])
        if m:
            l = m.group('label')
        else:
            l = x[0]
        t = [l]
        for y in x[1:]:
            t.append(simplify(y))
        return t        

def fixWords(tree, leaves, position=False):
    if not position:
        position = [0]
    if islist(tree) and len(tree) == 2 and type(tree[1]) == "str":
        if tree[0] == "NUM":
            tree[1] = "9999"
        word = WORD(form=tree[1], tag=tree[0], position=position[0])
        leaves.append(word)
        position[0] += 1
        return word
    else:
        if tree == []:
            return []
        else:
            return [tree[0]]+[fixWords(dtr, leaves, position) for dtr in tree[1:]]
        
def fixTrees(trees):
    global W
    W = 0
    n = 0
    for t0 in trees:
        n += 1
        if METERING:
            print "fixtrees %.2f"%(float(n)/float(len(trees)))
        t = readTree(t0.src)[0]
        t0.leaves = []
        t = fixWords(t, t0.leaves)
        t = simplify(t)
        t = removeDummies(t)
        t0.pstree = reducetags(t)
        fixICONJ(t0)

"""
>>> a, b = ht.readAllTrees('treebank/with-vowel', 'pos/after-treebank')
"""
def getAllTrees(treedir=PATB+'/treebank/with-vowel'):
    trees = []
    for path, folders, files in os.walk(treedir):
        for f in files:
            print f
            if f[-5:] == '.tree':
                getTrees('%s/%s'%(treedir, f), trees)
    return trees

TAG = 0
DTRS = 1

def findsublabels(tree, labels):
    label = tree[TAG]
    dtrs = tree[DTRS:]
    for dtr in dtrs:
        if islist(dtr):
            if not label in labels:
                labels[label] = {}
            labels[label][dtr[TAG]] = True
            findsublabels(dtr, labels)
    return labels

def convertToDictOfLists(d0):
    d1 = {}
    for x in d0:
        print "'%s':%s," % (x, [y for y in d0[x]])
    
def findallsublabels(trees):
    d = {}
    for tree in trees:
        findsublabels(tree, d)
    for x in d:
        d[x] = ['CONJ']+[y for y in d[x] if not y == 'CONJ' and not y == '']
    return d

def chooseHead(l, dtrs, labels):
    if len(dtrs) == 1:
        return dtrs[0]
    for x in labels[l]:
        for d in dtrs:
            if type(d) == "WORD":
                l = d.tag
            else:
                l = d[TAG]
            if x == l.split("-")[0]:
                return d
    raise Exception('No hd found for %s in %s'%(l, dtrs))
    
def pst2dt(ptree, labels, n, indent=False, used=False, top=False):
    if not indent == False:
        print showPSTree(ptree, indent=indent)
    if type(ptree) == "WORD":
        """
        If it's a list with two elements where the second is a string, then it's a preterminal
        and we just want the head (changed 10/02/2012 to return whole thing)
        """
        return [ptree]
    else:
        """
        Otherwise it's a proper tree: hd (ptree[0]) is the label, tl (ptree[1:]) is the dtrs
        """
        cat = ptree[0].split("-")[0]
        dtrs = ptree[1:]
        hd = chooseHead(cat, dtrs, labels)
        if istable(used):
            if not cat in used:
                used[cat] = {}
            if type(hd) == "WORD":
                tag = hd.tag
            else:
                tag = hd[0]
            if tag in used[cat]:
                used[cat][tag].append(n)
            else:
                used[cat][tag] = [n]
        if not hd:
            raise Exception('No dtr found for %s in \n%s\nLabels for possible dtrs of %s are \n%s'%(cat, showPSTree(ptree), cat, labels[cat]))
        others = [d for d in dtrs if not d == hd]
        if not indent == False:
            indent += '  '
        hd = pst2dt(hd, labels, n, indent=indent, used=used)
        for d in others:
            if type(d) == "WORD":
                l = d.tag
            else:
                l = d[0]
            if "-" in l:
                l = l.split("-")[1]
            else:
                l = "nolabel"
            d = pst2dt(d, labels, n, indent=indent, used=used)
            hd = hd+[d]
        return hd

"""
>>> alltrees = ht.readAllTrees(PATB+'with-vowel')
>>> d = ht.findallsublabels(alltrees)
>>> for x in d: print "'%s': %s,"%(x, d[x])
"""
oldlabels = {
'ADJP': ['CONJ', 'ADJ', 'ADJP', 'ADV', 'PP', 'NOUN', 'NO_FUNC', 'DET+NOUN', 'ADVP', 'NEG_PART', 'NUM', 'SUB_CONJ', 'NP', 'PUNC', 'DET+ADJ', 'DEM_PRON'],
'ADVP': ['CONJ', 'ADV', 'REL_ADV', 'ADVP', 'INTERJ', 'ADJP', 'PART', 'FOCUS_PART', 'X', 'PP', 'PUNC', 'ABBREV', 'PRT', 'EXCEPT_PART', 'NUM', 'NO_FUNC', 'NEG_PART', 'SUB_CONJ', 'PREP', 'ADJ', 'NOUN', 'REL_PRON', 'DEM_PRON', 'RC_PART', 'V', 'DET+ADJ', 'WHADVP', 'NP'],
'CONJP': ['CONJ', 'ADV', 'NOUN', 'PREP'],
'FRAG': ['CONJ', 'FRAG', 'ADV', 'PP', 'PUNC', 'SBAR', 'UCP', 'NOUN_PROP', 'PRN', 'ADJP', 'PRT', 'S', 'INTERJ', 'SUB_CONJ', 'NP', 'NOUN', 'ADVP', 'VP'],
'INTJ': ['CONJ', 'INTERJ', 'INTJ', 'NEG_PART'],
'NAC': ['CONJ', 'PP', 'PUNC', 'SBAR', 'UCP', 'ADJP', 'PRT', 'S', 'SUB_CONJ', 'NP', 'ADVP'],
'NP': ['CONJ', 'DO', 'DET+NOUN', 'NOUN', 'PRON', 'PRN',  'DEM_PRON', 'REL_PRON', 'NOUN_PROP', 'POSS_PRON', 'NP', 'DET+ADJ', 'ABBREV', 'ADV', 'ADJ', 'NUM', 'NO_FUNC', 'SUB_CONJ', 'DET+NUM', 'X', 'S', 'QP', 'PART', 'INTERJ', 'PUNC', 'PP', 'REL_ADV', 'V'],
'NX': ['CONJ', 'NOUN_PROP', 'DET+NOUN', 'PUNC', 'DET+ADJ'],
'PP': ['CONJ', 'PREP', 'PP', 'SBAR', 'DET+NOUN', 'FOCUS_PART', 'X', 'REL_ADV', 'REL_PRON', 'NOUN', 'PRON', 'DEM_PRON_MS', 'PRN', 'PRT', 'EXCEPT_PART', 'UCP', 'NP', 'DET+ADJ', 'ADV', 'NOUN_PROP', 'VP', 'S', 'ADVP', 'NO_FUNC', 'PUNC', 'NEG_PART', 'SUB_CONJ', 'ADJ'],
'PRN': ['CONJ', 'PP', 'DET+ADJ', 'PUNC', 'SBAR', 'ADJP', 'NEG_PART', 'DET+NOUN_PROP', 'S', 'NUM', 'VERB_PART', 'NOUN_PROP', 'NP', 'NOUN', 'ADVP'],
'PRT': ['CONJ', 'ADV', 'PV', 'NO_FUNC', 'EXCEPT_PART', 'RC_PART', 'PRT', 'NEG_PART', 'VERB_PART', 'INTERJ', 'SUB_CONJ', 'REL_PRON', 'INTERROG_PART', 'V', 'REL_ADV', 'NOUN'],
'QP': ['CONJ', 'NOUN', 'NO_FUNC', 'ABBREV', 'NUM', 'PUNC', 'ADJ', 'PREP', 'NEG_PART'],
'S': ['FULLSTOP', 'CONJ', 'PV', 'IV3MS', 'IV3FS', 'VP', 'S', 'FRAG', 'SBAR', 'NAC', 'ADJP', 'CONJP', 'PART', 'FOCUS_PART', 'X', 'PP', 'LATIN', 'UCP', 'PRN', 'PRT', 'NUM', 'NP', 'DET+ADJ', 'ADV', 'INTJ', 'ADVP', 'SQ', 'SUB_CONJ'],
'SBAR': ['CONJ', 'SUB_CONJ', 'S', 'SBAR', 'SQ'],
'SBARQ': ['CONJ', 'SQ', 'S'],
'SQ': ['CONJ', 'VP', 'ADVP', 'PP'],
'UCP': ['CONJ', 'FRAG', 'PP', 'PUNC', 'SBAR', 'UCP', 'ADJP', 'VP', 'S', 'SUB_CONJ', 'NP', 'ADVP'],
'VP': ['CONJ', 'V', 'FUT', 'ADJ', 'NP', 'NOUN', 'VP', 'NEG_PART', 'PP', 'NO_FUNC', 'PUNC', 'X'],
'WHADVP': ['CONJ', 'REL_ADV', 'SUB_CONJ', 'REL_PRON', 'PREP', 'INTERROG_PART'],
'WHNP': ['CONJ', 'REL_PRON', 'INTERROG_PART', 'SUB_CONJ', 'REL_PRON+PREP', 'X', 'NO_FUNC', 'NEG_PART', 'NOUN'],
'WHPP': ['CONJ', 'PREP', 'REL_PRON', 'ADV', 'PUNC'],
'X': ['CONJ', 'DET+NOUN', 'DET+NOUN_PROP', 'PV', 'ABBREV', 'NUM', 'NOUN_PROP', 'DET+ADJ', 'FRAG', 'NP', 'PUNC', 'ADJ', 'NO_FUNC', 'NOUN', 'NEG_PART', 'SUB_CONJ', 'DEM_PRON_F', 'PREP', 'REL_PRON+PREP', 'X', 'V', 'PART', 'ADV'],
    }

# This set has been hand-pruned and ordered
labels = {
'ADJP': ['ICONJ', 'CONJ', 'LRB', 'ADJ', 'ADJP', 'ADV', 'PP', 'NOUN', 'DET+NOUN', 'NO_FUNC', 'ADVP', 'NEG_PART', 'NUM', 'SUB_CONJ', 'EndmA', 'NP', 'PUNC', 'RRB', 'DET+ADJ', 'DEM_PRON', 'FULLSTOP', 'CONJ'],
'ADVP': ['ICONJ', 'CONJ', 'LRB', 'ADV', 'ADVP', 'INTERJ', 'PART', 'FOCUS_PART', 'X', 'PP', 'PUNC', 'RRB', 'ABBREV', 'EXCEPT_PART', 'NUM', 'NO_FUNC', 'NEG_PART', 'SUB_CONJ', 'EndmA', 'PREP', 'ADJ', 'NOUN', 'DET+NOUN', 'DEM_PRON', 'RC_PART', 'V', 'IV', 'PV', 'CV', 'DET+ADJ', 'WHADVP', 'NP', 'FULLSTOP', 'CONJ'],
'CONJP': ['ICONJ', 'CONJ', 'LRB', 'ADV', 'NOUN', 'DET+NOUN', 'FULLSTOP', 'CONJ'],
'FRAG': ['ICONJ', 'CONJ', 'LRB', 'PUNC', 'RRB', 'PP', 'SBAR', 'PRN', 'PRT', 'NP', 'VP', 'FULLSTOP', 'CONJ'],
'INTJ': ['INTERJ', 'NEG_PART', 'FULLSTOP', 'CONJ'],
'NAC': ['ICONJ', 'CONJ', 'LRB', 'PP', 'PUNC', 'RRB', 'SBAR', 'UCP', 'NP', 'FULLSTOP', 'CONJ'],
'NP': ['ICONJ', 'CONJ', 'LRB', 'DO', 'NOUN', 'DET+NOUN', 'PRON', 'PRN', 'DEM_PRON', 'REL_PRON', 'POSS_PRON', 'NP', 'DET+ADJ', 'ABBREV', 'ADV', 'ADJ', 'NUM', 'NO_FUNC', 'SUB_CONJ', 'EndmA', 'DET+NUM', 'X', 'S', 'QP', 'PART', 'INTERJ', 'PUNC', 'RRB', 'REL_ADV', 'V', 'IV', 'PV', 'CV', 'FULLSTOP', 'CONJ'],
'NX': ['PUNC', 'RRB', 'FULLSTOP', 'CONJ'],
'PP': ['ICONJ', 'CONJ', 'LRB', 'PREP', 'PP', 'SBAR', 'FOCUS_PART', 'X', 'NOUN', 'DET+NOUN', 'PRON', 'PRN', 'PRT', 'EXCEPT_PART', 'NP', 'ADV', 'VP', 'S', 'NO_FUNC', 'PUNC', 'RRB', 'NEG_PART', 'SUB_CONJ', 'EndmA', 'ADJ', 'FULLSTOP', 'CONJ'],
'PRN': ['ICONJ', 'CONJ', 'LRB', 'PP', 'DET+ADJ', 'PUNC', 'RRB', 'SBAR', 'ADJP', 'NEG_PART', 'S', 'VERB_PART', 'NP', 'NOUN', 'DET+NOUN', 'ADVP', 'FULLSTOP', 'CONJ'],
'PRT': ['ICONJ', 'CONJ', 'LRB', 'ADV', 'NO_FUNC', 'EXCEPT_PART', 'RC_PART', 'PRT', 'NEG_PART', 'VERB_PART', 'INTERJ', 'SUB_CONJ', 'EndmA', 'REL_PRON', 'INTERROG_PART', 'V', 'IV', 'PV', 'CV', 'REL_ADV', 'NOUN', 'DET+NOUN', 'FULLSTOP', 'CONJ'],
'QP': ['ICONJ', 'CONJ', 'LRB', 'NOUN', 'DET+NOUN', 'ABBREV', 'NUM', 'ADJ', 'FULLSTOP', 'CONJ'],
'S': ['ICONJ', 'CONJ', 'LRB', 'VP', 'S', 'FRAG', 'SBAR', 'NAC', 'ADJP', 'PART', 'X', 'PP', 'UCP', 'PRT', 'NP', 'FULLSTOP', 'CONJ'],
'SBAR': ['ICONJ', 'CONJ', 'LRB', 'WHNP', 'SUB_CONJ', 'EndmA', 'S', 'SBAR', 'SQ', 'FULLSTOP', 'CONJ'],
'SBARQ': ['SQ', 'S', 'FULLSTOP', 'CONJ'],
'SQ': ['VP', 'PP', 'FULLSTOP', 'CONJ'],
'UCP': ['ICONJ', 'CONJ', 'LRB', 'FRAG', 'PP', 'PUNC', 'RRB', 'SBAR', 'FULLSTOP', 'CONJ'],
'VP': ['ICONJ', 'CONJ', 'LRB', 'V', 'IV', 'PV', 'CV', 'FUT', 'ADJ', 'NP', 'NOUN', 'DET+NOUN', 'VP', 'NEG_PART', 'SUBCONJ', 'PP', 'NO_FUNC', 'X', 'FULLSTOP', 'CONJ'],
'WHADVP': ['ICONJ', 'CONJ', 'LRB', 'REL_ADV', 'SUB_CONJ', 'EndmA', 'REL_PRON', 'PREP', 'INTERROG_PART', 'FULLSTOP', 'CONJ'],
'WHNP': ['REL_PRON', 'INTERROG_PART', 'SUB_CONJ', 'X', 'NO_FUNC', 'NEG_PART', 'NOUN', 'DET+NOUN', 'FULLSTOP', 'CONJ'],
'WHPP': ['ICONJ', 'CONJ', 'LRB', 'PREP', 'FULLSTOP', 'CONJ'],
'X': ['ICONJ', 'CONJ', 'LRB', 'ABBREV', 'NUM', 'DET+ADJ', 'FRAG', 'NP', 'PUNC', 'RRB', 'ADJ', 'NO_FUNC', 'NOUN', 'DET+NOUN', 'NEG_PART', 'SUB_CONJ', 'PREP', 'REL_PRON+PREP', 'V', 'IV', 'PV', 'CV', 'PART', 'ADV', 'FULLSTOP', 'CONJ'],
}

def allpst2dt(trees, pretagged, labels=labels, showtrees=True):
    used = {}
    n = 0
    for tree in trees:
        if showtrees:
            print "**** %s ***************"%(n)
            tree.showPSTree()
        tree.dtree = pst2dt(tree.pstree, labels, n, used=used, indent=False, top=True)
        tree.leaves = [w for w in tree.leaves if not "NONE" in w.tag]
        for i in range(len(tree.leaves)):
            tree.leaves[i].position = i
        if showtrees:
            tree.showDTree()
        pretagged += [WORD('SENTSTART', 'SA')]+tree.leaves+[WORD('SENTEND', 'SZ', len(tree.leaves)+1)]
        n += 1
        print "allpst2dt %.2f"%(float(n)/float(len(trees)))
    return used

def cleanupLabels(labels0, used):
    labels1 = {}
    for l in labels0:
        labels1[l] = [x for x in labels0[l] if x in used[l]]
    return labels1

def outliers(labels):
    for x in labels:
        for y in labels[x]:
            if len(labels[x][y]) == 1:
                print x, y, labels[x][y]

def subtrees(dtree, trees=False):
    if trees == False:
        trees = {}
    if isstring(dtree):
        return trees
    hd = '%s-%s'%(dtree[1], dtree[0])
    hd = dtree[0]
    dtrs = [reducetag(x[0]) for x in dtree[2:]]
    incTable2(hd, '%s'%(dtrs), trees)
    for d in dtree[1:]:
        subtrees(d, trees)
    return trees

def allsubtrees(dtrees):
    trees = {}
    for dtree in dtrees:
        if dtree.__class__.__name__ == 'SENTENCE':
            dtree = dtree.dtree
        trees = subtrees(dtree, trees)
    for x in trees:
        try:
            trees[x] = [(trees[x][y], eval(y)) for y in trees[x]]
            trees[x].sort()
        except Exception as e:
            print trees[x]
            raise e
    return trees
            
def alltrees(treedir=PATB+'/treebank/without-vowel', showtrees=False):
    pretagged = []
    trees = getAllTrees(treedir=treedir)
    print "fixTrees"
    fixTrees(trees)
    print "allpst2dt"
    used = allpst2dt(trees, pretagged, showtrees=showtrees)
    for word in pretagged:
        word.tag = word.tag.replace("-", "")
    return trees, pretagged

def savedtrees(trees, out):
    with safeout(out) as out:
        out('%s'%([t.dtree for t in trees]))
