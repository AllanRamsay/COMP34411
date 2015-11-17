import sys
import re
import os
from useful import *
from word import WORD, isword

LABEL = 0
DTRS = 1
METERING = False

def gettag(x):
    if isword(x):
	return x.tag
    else:
	return x[LABEL]

sp = re.compile("\s")

def showPSTree(tree, indent=0, initial=False):
    s = ""
    if not initial:
        s += '\n'
        for i in range(0, indent):
            s += ' '
    if isstring(tree) or isword(tree):
        s += '%s'%(tree,)
    else:
        l = gettag(tree)
        s += '[%s '%(l)
        initial = True
        for d in tree[DTRS:]:
            s += showPSTree(d, indent=indent+len(l)+2, initial=initial)
            initial = False
        s += ']'
    if indent == 0:
        s += '\n'
    return s

def showDTree(tree, indent=0, initial=False):
    s = ""
    if not initial:
        s += '\n'
        for i in range(0, indent):
            s += ' '
    word = tree[0]
    if type(word) == "WORD":
        if word.form:
            label = "%s:%s"%(word.form, word.tag)
        else:
            label = "%s:%s"%(word.tag, word.position)
    else:
        label = word
    s += '[%s '%(label, )
    initial = True
    for d in tree[DTRS:]:
	s += showDTree(d, indent=indent+len(label)+2, initial=initial)
	initial = False
    s += ']'
    if indent == 0:
        s += '\n'
    return s

def pretty(tree):
    print showPSTree(tree)

def toCONLL(tree):
    irelns = {}
    for x in tree.relns.values():
        irelns[x.dtr] = x
    s = []
    for leaf in tree.leaves[1:-1]:
        x = [leaf.position, leaf.form, leaf.tag]
        try:
            x += [irelns[leaf.position].hd]
        except:
            x += [0]
        s.append(x)
    return s

def getRelations(conll, relations=False):
    if relations == False:
        relations = {}
    conll = [[0, 'TOP', 'DUMMY', -1]]+conll
    for i in range(1, len(conll)):
        x = conll[i]
        j = x[-1]
        if j > i:
            s = conll[1:][i:j-1]
        else:
            s = conll[1:][j:i-1]
        incTable(str((x[2], j-i, conll[x[-1]][2], [y[2] for y in s])), relations)
    return relations
                    
class SENTENCE:

    def __init__(self, source, file, localcounter, overallcounter):
        self.source = source
        self.file = file
        self.localcounter = localcounter
        self.overallcounter = overallcounter

    def showBaseTree(self):
        print showPSTree(self.basetree)

    def showFixedTree(self):
        print showPSTree(self.fixed)

    def showDTree(self):
        print showDTree(self.dtree)

    def bareDTree(self, f=lambda x: '%s:%s'%(x.tag, x.form)):
        return bareDTree(self.dtree, f)
        
    def sentence(self):
        s = ""
        for l in self.leaves[1:-1]:
            s += "%s "%(l.form)
        return s
    
def readsentence(s0):
    while sp.match(s0):
        s0 = s0[1:]
    if len(s0) == 0:
        return False, s0
    else:
        n = 0
        if not s0[0] == "(":
            raise Exception("%s doesn't start with '('")
        s1 = s0[0]
        s0 = s0[1:]
        n = 1
        while n > 0:
            c = s0[0]
            s1 += c
            if c == "(":
                n += 1
            elif c == ")":
                n -= 1
            s0 = s0[1:]
    return s1, s0

tagpattern = re.compile("(?P<form>\S*)/(?P<tag>\S*)")

def intersect(x0, x1):
    for x in x0:
        if x in x1:
            return True
    return False

def inserttags(tree0, tags):
    if isstring(tree0):
        if '*' in tree0:
            return tree0, tags
        tags01 = tags[0][1].replace("\\", "")
        if not tree0 == tags01 and not intersect(["sq", "dq", "-LCB-", "-RCB-", "-LRB-", "-RRB-"], tree0) and not tags[0][0] == "CD":
            raise Exception("Mismatch when assigning tags: %s doesn't match %s"%(tree0, tags[0]))
            return tree0, tags
        return tags[0], tags[1:]
    elif istuple(tree0[0]):
        return inserttags(tree0[0], tags)
    elif len(tree0) == 2 and 'WH' in tree0[LABEL] and tree0[1] == "0":
        return (tree0[LABEL].split("-")[0], "*"), tags
    else:
        tree1 = [tree0[LABEL]]
        for dtr in tree0[1:]:
            dtr, tags = inserttags(dtr, tags)
            tree1.append(dtr)
        return tree1, tags

labelpattern = re.compile("(-\d+)|(=.*)")
labelpattern1 = re.compile("((?P<g1>(ADJP|S|PP|VP|UCP|SBAR|NAC|SBARQ|X))-.*)|((?P<group3>JJ).*)|((?P<advp>ADVP).+)|((?P<frag>FRAG).+)|(?P<group1>[^-]*-[^-]*)(-.*)")
def fixlabels(tree0):
    if isstring(tree0):
        return tree0
    label = labelpattern.split(tree0[LABEL])[0]
    m = labelpattern1.match(label)
    if m:
      for g in labelpattern1.groupindex:
          if m.group(g):
              label = m.group(g)
              break
    tree1 = [label]
    for dtr in tree0[DTRS:]:
        tree1.append(fixlabels(dtr))
    return tree1

corpus = "/Users/ramsay/nltk_data/corpora/treebank"
def readsents(corpus=corpus):
    n = 0
    trees = []
    sbarPattern = re.compile("SBAR(\S*\s+)?\s*\d+")
    starbPattern = re.compile("\*(?P<starb>.CB)\*")
    for f in os.listdir("%s/parsed"%(corpus)):
        if f[-4:] == ".prd":
            l = 0
            if METERING:
                print f
            tags = [[i.group("tag"), i.group("form")] for i in tagpattern.finditer(open("%s/tagged/%s.pos"%(corpus, f[:-4])).read())]
            s0 = open("%s/parsed/%s"%(corpus, f)).read()
            s0 = sbarPattern.sub("SBAR", s0)
            s0 = starbPattern.sub("-\g<starb>-", s0)
            s0 = s0.replace("S-1", "S")
            s0 = s0.replace("\\", "")
            while not s0 == "":
                s, s0 = readsentence(s0)
                if s == False:
                    break
                sentence = SENTENCE(s, f, l, n)
                trees.append(sentence)
                l += 1
                n += 1
                s = s.replace('``', "dq").replace("'", "sq").replace('"', "dq").replace("`", "sq")
                s1 = wpattern.sub('"\g<0>",', s).replace(')', '),')
                try:
                    tree = eval(s1)
                    tree, tags = inserttags(tree, tags)
                    sentence.basetree = tree
                except Exception as e:
                    print s
                    print s1
                    raise e
                    return
    return trees

def countwords(tree):
    if isstring(tree):
        return 1
    else:
        return sum([countwords(dtr) for dtr in tree[DTRS:]])

def countallwords(trees):
    return sum([countwords(tree) for tree in trees])

tracepattern = re.compile('.*\*.*-(?P<trace>\d*)')

def istrace(tree):
    return (len(tree) == 2 and isstring(tree[1]) and tracepattern.match(tree[1])) or tree == "*U*" or tree == "*?*" or tree == "*"

def fixtraces(tree0):
    if isstring(tree0):
        return tree0
    tree1 = [tree0[LABEL]]
    for dtr in tree0[DTRS:]:
        if not istrace(dtr):
            tree1.append(fixtraces(dtr))
    return tree1

def removeFullStops(tree):
    if isstring(tree):
	return tree
    else:
	tree1 = [tree[0]]
	for dtr in tree[DTRS:]:
	    if not (islist(dtr) and dtr[0] == "."):
		tree1.append(removeFullStops(dtr))
        return tree1

def removeEmptySubtrees(tree):
    if isstring(tree):
        return tree
    else:
        dtrs = [removeEmptySubtrees(d) for d in tree[DTRS:]]
        dtrs = [d for d in dtrs if isstring(d) or len(d) > 1]
        return [tree[LABEL]]+dtrs

def fixpositions(tree, leaves, n=0):
    if isword(tree):
	tree.position = n
        leaves.append(tree)
        return n+1
    else:
        for d in tree[1:]:
            n = fixpositions(d, leaves, n)
        return n

def isleaf(x):
    return islist(x) and len(x) == 2 and isstring(x[1])
    
def fixleaves(tree):
    if isword(tree):
	return tree
    for i in range(1, len(tree)):
	dtr = tree[i]
	if isleaf(dtr):
	    tree[i] = WORD(dtr[1], dtr[0])
	else:
	    fixleaves(dtr)
	    
def fixtree(sentence):
    tree = fixlabels(fixtraces(sentence.basetree))
    sentence.fixed = removeEmptySubtrees(removeFullStops(tree))
    fixleaves(sentence.fixed)
    sentence.leaves = []
    fixpositions(sentence.fixed, sentence.leaves)

def fixall(sentences):
    t = float(len(sentences))
    n = 0.0
    for s in sentences:
        if METERING:
            print "fixall: %.2f"%(n/t)
        fixtree(s)
        n += 1.0
    patchallpsts(sentences)

def findsublabels(tree, labels):
    label = tree[LABEL]
    dtrs = tree[DTRS:]
    for dtr in dtrs:
        if islist(dtr):
            if not label in labels:
                labels[label] = {}
            labels[label][dtr[LABEL]] = True
            findsublabels(dtr, labels)
    return labels

def getalllabels(trees):
    labels = {}
    for tree in trees:
        findsublabels(tree.fixed, labels)
    labels = [(label, sorted([sublabel for sublabel in labels[label]])) for label in labels]
    return sorted(labels)

def exportlabels(labels, out=sys.stdout):
    with safeout(out) as write:
        write("HPT = {")
        for label, sublabels in labels:
            write('"%s": %s,\n          '%(label, sublabels))
        write("\n}\n")

def findexamples(label, trees, examples=False):
    if examples == False:
        examples = []
    if islist(trees):
        if trees[LABEL] == label:
            if not trees in examples:
                pretty(trees)
                examples.append(trees)
        else:
            for tree in trees:
                findexamples(label, tree, examples=examples)

def findembedded(label, tree):
    if islist(tree):
	if tree[0] == label:
	    return True
        for dtr in trees[DTRS:]:
            if findembedded(label, dtr):
		return True
    return False

def findpstexamples(label, sentences, n=-1):
    for s in sentences:
	if findembedded(label, s.fixed):
	    s.showFixedTree()
	    n -= 1
	    if n == 0:
		return

def chooseHead(l, dtrs, hpt):
    for x in hpt[l]:
        for d in dtrs:
            if x == gettag(d):
                return d
    for d in dtrs:
        pretty(d)
    raise Exception('No hd found for %s in %s: options were %s'%(l, dtrs, hpt[l]))
wpattern = re.compile("""(\w|[.,-:;=@!#\|]|\*|'|"|\?|&|%|\$)+""", re.DOTALL)
    
HPT = {"ADJP": ['JJ', 'ADJP', 'VBD', 'VBG', 'VBN', 'DT', 'NN', 'PCT', 'QP', 'IN', 'T2', 'RB', 'NNS', '$', 'UH', 'NNP', 'BE', 'VB', 'RBR', 'CC'],
       "ADVP": ['ADVP', 'T2', 'RB', 'IN', 'JJ', 'RP', 'NN', 'PCT', 'DT', 'RBR', 'CD', 'NNP', 'PDT', 'NP-ADV', 'VBN', 'CC'],
       "CONJP": ['T2', 'RB', 'IN', 'CC'],
       # "FRAG": ["''", ',', '.', ':', 'ADJP', 'ADVP', 'FRAG', 'IN', 'INTJ', 'NP', 'NP-LOC', 'NP-SBJ', 'NP-TMP', 'NP-VOC', 'PP', 'PRN', 'T2', 'RB', 'S', 'SBAR', 'VP', 'WHADVP', 'WHNP', '``', 'CC'],
       "INTJ": ['UH', 'T2', 'RB', 'BE', 'VB', 'NN', 'PCT', 'CC'],
       "LST": [')', 'LS', ':', 'CC'],
       # "NAC": [',', 'CD', 'DT', 'NAC', 'NN', 'PCT', 'NNP', 'NNPS', 'NNS', 'PP', 'CC'],
       "NP": ['POS', 'NN', 'PCT', 'NNP', 'NNPS', 'NNS', 'PRN', 'THAT', 'PRP', 'PRP$', 'NP', 'CD', 'DT', 'EX', 'QP', 'T2', 'RB', 'JJ', 'WDT', 'NX', 'IN', 'RBS', 'RBR', 'FW', 'NX-TTL', 'NAC', 'NP-TTL', 'BE', 'VB', 'VBG', 'VBZ', 'PP', 'NP-LOC', 'SBAR', 'S', 'CC'],
       "NX": ['NN', 'PCT', 'NNP', 'NNS', 'NP', 'NX', 'CC'],
       "NX-TTL": ['NNP', 'NNPS', 'NP', 'CC'],
       "PP": ['IN', 'TO', 'PP', 'VBG', 'JJ', 'RP', 'T2', 'RB', 'NNP', 'NN', 'PCT', 'RBR', 'CC'],
       "PRN": ['(', ',', ':', 'SINV', 'S', 'SBAR'],
       "PRT": ['IN', 'RP', 'T2', 'RB', 'RBR', 'JJ', 'CC'],
       "QP": ['IN', 'JJ', '$', 'CD', 'T2', 'RB', 'CC'],
       "RRC": ['VP', 'PP', 'ADJP', 'CC'],
       "S": ['VP', 'S', 'SBAR', 'SBARQ', 'SINV', 'SINV-TPC', 'NP-PRD', 'ADJP', 'ADVP', 'NP-TMP', 'PP', 'NP-SBJ', 'NP-TTL', 'CC'],
       "SBAR": ['IF', 'S', 'SBAR', 'SINV', 'SQ', 'IN', 'FRAG', 'CC'],
       "SBARQ": ['S', 'SBAR', 'SBARQ', 'SQ', 'RP', 'CC'],
       "SINV": ['BE', 'VB', 'VBD', 'VBP', 'VBZ', 'VP', 'CONJP', 'CC'],
       "SINV-TPC": ['VBP', 'VP', 'CC'],
       "SQ": ['MD', 'BE', 'VB', 'MD', 'VBD', 'VBP', 'VBZ', 'VP', 'FRAG', 'CC'],
       "SQ-TPC": ['VBP', 'VP', 'CC'],
       "UCP": [':', 'SBAR', 'PP', 'CC'],
       "VP": ['TO', 'MD', 'BE', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'VP', 'PP', 'IN', 'JJ', 'ADVP', 'NP', 'NN', 'PCT', 'POS', ',', 'CC'],
       "WHADJP": ['WRB', 'CC'],
       "WHADVP": ['WRB', 'THAT', 'IN', 'T2', 'RB', 'CC'],
       "WHNP": ['THAT', 'WDT', 'WHADJP', 'WHNP', 'WHPP', 'WP', 'WP$', 'WRB', 'IN', 'DT', 'QP', 'PRP', 'CC'],
       "WHPP": ['WHNP', 'CC'],
       "X": ['.', 'CD', 'IN', 'NN', 'PCT', 'NNP', 'NP-LGS', 'PP'],
}
    
def pst2dt(ptree, hpt=HPT, n=0, top=False):
    if isword(ptree):
        """
        If it's a list with two elements where the second is a string, then it's a preterminal
        and we just want the head (changed 10/02/2012 to return whole thing)
        """
        return [ptree]
    else:
        """
        Otherwise it's a proper tree: hd (ptree[LABEL]) is the label, tl (ptree[DTRS:]) is the dtrs
        """
        cat = gettag(ptree).split("-")[0]
        dtrs = ptree[DTRS:]
        hd = chooseHead(cat, dtrs, hpt)
        if not hd:
            raise Exception('No dtr found for %s in \n%s\nLabels for possible dtrs of %s are \n%s'%(cat, showPSTree(ptree), cat, hpt[cat]))
        others = [d for d in dtrs if not d == hd]
        hd = pst2dt(hd, hpt, n=n)
        hd, newdtrs = hd[0], hd[1:]
        for d in others:
            l = gettag(d)
            if "-" in l:
                l = l.split("-")[1]
            else:
                l = "mod"
            if islist(d) and len(d) == 1:
                continue
            d = pst2dt(d, hpt, n=n)
	    d[0].label = l
            newdtrs.append(d)
        newdtrs.sort(cmp=lambda t1, t2: -1 if t1[0].position < t2[0].position else 1)
        hd = [hd]+newdtrs
        if top:
            hd[0].label = "top"
        return hd

def allpst2dt(trees, hpt=HPT):
    t = float(len(trees))
    for n in range(len(trees)):
        if METERING:
            print "allpst2dt %.2f"%(n/t)
        sentence = trees[n]
        try:
            sentence.dtree = pst2dt(sentence.fixed, hpt=hpt, top=True, n=n)
        except KeyError as e:
            if e.args[0] in ['NAC', 'FRAG']:
                sentence.dtree = False
            else:
                raise e
    patchalldts(trees)

def matches(x, y):
    if isstring(y):
        try:
	    return x[0] == y
        except:
            return x.tag == y
    elif len(y) == 1:
	return x[1][0] == y[0]
    else:
	return (x[0][:len(y[0])], x[1][0]) == (y[0], y[1])

def containssubtree(tree, hd, dtr):
    if istuple(tree):
        return False
    if matches(tree[0], hd):
        for d in tree[1:]:
            if matches(d[0], dtr):
                return True
    try:
        for d in tree[1:]:
            if containssubtree(d, hd, dtr):
                return True
    except:
        pass
    return False

def finddtrees(trees, hd, dtr, n=-1):
    for tree in trees:
        if containssubtree(tree.dtree, hd, dtr):
            print tree.overallcounter
            tree.showDTree()
	    n -= 1
	    if n == 0:
		return

def contains(tree, x):
    if matches(tree[0], x):
	return True
    for d in tree[1:]:
	if contains(d, x):
	    return True
    return False

def finddtexamples(trees, x, n=-1):
    for tree in trees:
	if contains(tree.dtree, x):
	    print tree.overallcounter
	    tree.showDTree()
	    n -= 1
	    if n == 0:
		return

def findanomalies(trees, used):
    for hd in used:
        for dtr in used[hd]:
            if len(used[hd][dtr]) < 4:
                print "********* %s > %s (%s) ******************"%(hd, dtr, used[hd][dtr])
                for i in used[hd][dtr]:
                    trees[i].showFixedTree()

def checkuppercaseforms(tags):
    mismatches = []
    for u in tags:
        l = u.lower()
        if not l == u and l in tags:
            mismatch = False
            for t in tags[u]:
                if not t in tags[l]:
                    mismatch = True
                    break
            if mismatch:
                mismatches.append([u, tags[u], tags[l]])
    for x in sorted(mismatches):
        print x

def trickytags(tags):
    openclass = re.compile('N.*|V.*|JJ')
    tt = []
    n = 0
    for w in tags:
        print n, float(n)/float(len(tags))
	t = {}
	found = False
        n += 1
        if w[0].isupper():
            if w.lower() in tags:
                for x in tags[w]:
		    t[x] = tags[w][x]
		    if not openclass.match(x):
			found = True
		w = w.lower()
                for x in tags[w]:
		    try:
			t[x] += tags[w][x]
		    except:
			t[x] = tags[w][x]
		    t[x] = tags[w][x]
		    if not openclass.match(x):
			found = True
            else:
                for x in tags[w]:
		    t[x] = tags[w][x]
		    if not openclass.match(x):
			found = True
        else:
            for x in tags:
                if x[0].isupper() and x.lower() == w:
                    break
            else:
                for x in tags[w]:
		    t[x] = tags[w][x]
		    if not openclass.match(x):
			found = True
        if found and len(t) > 1:
            tt.append((w, t))
    return sorted(tt)
            
def exportdtrees(sentences, out=sys.stdout):
    patchalldts(sentences)
    s = "["
    for sent in sentences:
        s += "%s\n"%(sent.dtree)
    s += "]"
    with safeout(out) as write:
        write(s)

def patchpst(form, tag, tree):
    if islist(tree):
	if len(tree) == 2 and istuple(tree[1]):
	    if tree[1][0] == form:
		return [tag, tree[1]]
	    else:
		return tree
	else:
	    tree1 = [tree[0]]
	    for d in tree[1:]:
		tree1.append(patchpst(form, tag, d))
	    return tree1
    else:
	return tree

"""
Treating words that have special properties specially can be
worthwhile: just marking "that" as a special case improves parsing
accuracy by 0.7%--not an immense improvement, but given that "that" is
only 0.8% of the total number of words it does show that this is a
useful thing to do: it's not that "that" is given the wrong head or
dtr almost every time, but that giving it the wrong hd or dtr has
knock on effects for other words.

But you have to be judicious about it: marking the critical verbs
("be", "have") as special cases and distinguishing subject and object
pronouns makes things worse rather than better, whilst generating a
larger set of rules (tagging accuracy is very very slightly increased,
(0.03%!), but parsing accuracy is down by the same amount and the number of
rules is up from 13402 to 15888. Even 13402 is a lot, given that there were
only 90K words originally, which means that on average a rule covers 6.7 cases).
"""

PATCHES=[("that", "THAT"),
         ("up", "IN"), ("the", "DT"), ("and", "CC"), ("in", "IN"),
         ("more", "MORE"), ("much", "MORE"), ("so", "SO"), ("to", "TO"), ("ago", "AGO"),
         ("if", "IF"),
         ("not", "NOT"),
         ("%", "PCT"),
         ("who", "WH"), ("what", "WH"), ("which", "WH"),
         ("its", "DT"), ("my", "DT"), ("your", "DT"), ("our", "DT"), ("their", "DT"),
         # ("am", "BE"), ("is", "BE"), ("are", "BE"), ("be", "BE"), ("was", "BE"), ("were", "BE"), ("being", "BE"), ("been", "BE"),
         # ("I", "SUBJ"), ("i", "SUBJ"),("he", "SUBJ"),("she", "SUBJ"),("we", "SUBJ"),("they", "SUBJ"),
         # ("me", "OBJ"), ("him", "OBJ"),("her", "OBJ"),("us", "OBJ"),("them", "OBJ"),
         # If the first item is all upper-case then it's a tag, not a form
         ("NNP", "PN"),
    ]

def patchallpsts(trees, patches=PATCHES):
    for form, tag in patches:
	for tree in trees:
	    tree.fixed = patchpst(form, tag, tree.fixed)

def patchdt(form, tag, tree):
    x0 = tree[0]
    if form.isupper():
        if x0.tag == form:
            x0.tag = tag
    else:
        if x0.form.lower() == form:
            if not x0.tag == tag:
                x0.tag = tag
    tree1 = [x0]
    for dtr in tree[1:]:
	tree1.append(patchdt(form, tag, dtr))
    return tree1

def patchalldts(trees, patches=PATCHES):
    for form, tag in patches:
	for tree in trees:
            if tree.dtree:
                tree.dtree = patchdt(form, tag, tree.dtree)
	
def extractAllRelations(trees):
    relations = {}
    for tree in trees:
        extractRelations(tree.dtree, relations)
    normalise2(relations)
    return relations

def extractRelations(tree, relations):
    label = tree[0][0]
    for dtr in tree[1:]:
        incTable2(dtr[0][0], label, relations)
        extractRelations(dtr, relations)
 
def getsubtrees(tree, subtrees):
    label = tree[0][0]
    dtrs = []
    for dtr in tree[1:]:
        getsubtrees(dtr, subtrees)
        dtrs.append(dtr[0][0])
    incTable2(label, join(dtrs, "+"), subtrees)
    
def getallsubtrees(trees):
    subtrees = {}
    for tree in trees:
        getsubtrees(tree.dtree, subtrees)
    return subtrees

def readtb():
    trees = readsents()
    fixall(trees)
    allpst2dt(trees)
    trees = [tree for tree in trees if len(tree.leaves) > 1 and tree.dtree]
    tags = []
    for tree in trees:
        tags.extend(tree.leaves)
    return trees, tags

def forsardar(tree):
    hd = tree[0]
    hd = [(hd.form, hd.tag, hd.label, hd.position)]
    for d in tree[1:]:
        hd.append(forsardar(d))
    return hd

def bareDTree(tree0, f):
    tree1 = [f(tree0[0])]
    for d in tree0[1:]:
        tree1.append(bareDTree(d, f))
    return tree1

