"""
FORCEPARSE.PY

Includes stuff that would do the coursework, so DO NOT EXPORT TO WALDORF

To train a parser on the English PTB, do

trees, tags = forceparse.tb.tb()

forceparse.forceparseall(trees)
n = 3000
clsf = forceparse.makeclassifier(trees[:n])

#Then you can test it with

forceparse.testparser(trees[n:], clsf)

#You can do nfold-X-validation by doing

forceparse.nfold(trees, n=5)

To use it on unseen text, you're going to need a tagger.
Use the tags from the training data (might as well use all
of it, because you're going to be applying it to fresh
data) (you might want to cPickle the tagger because it
takes a while to build, especialy if we're going to Brill
it)

print forceparse.parse("I saw the man in the park with a telescope", clsf, forceparse.mxltag)

There's a collection of Arabic trees in patb.txt, which can be read by
the things in patb.py. Because these have traces, I can't actually do
them. If/when I get round to it, I am going to look for systematic
patches--I don't want to do it training on proper trees with traces
in, because I think it's too hard. But doing it very fast and a bit
roughly and then patching it sounds interesting.

"""

from useful import *
import useful

import malt
reload(malt)

import id3
reload(id3)

import tb
reload(tb)

import chunking
reload(chunking)

import sys
import os
import cPickle
import datetime

METERING = True

try:
    tagger = cPickle.load(open('tagger.pck'))
except:
    print "No 'tagger.pck' available"

"""
Just to make sure that the thing isn't broken
"""
def cwtest():
    s = malt.STATE('I know she loves me')
    s.shift()
    s.leftArc('subj')
    s.shift()
    s.shift()
    s.leftArc('subj')
    s.shift()
    s.rightArc('obj')
    s.rightArc('comp')
    return s

def satisfied(relns, s):
    srelns = s.relations
    for r in relns:
        r = relns[r]
        for s in srelns:
            if s.hd == r.hd and s.dtr == r.dtr:
                break
        else:
            return False
    return True

def alldtrsfound(d, irelns, srelns):
    if d in irelns:
        for x in irelns[d]:
            unfound = True
            if x in srelns:
                unfound = False
            if unfound:
                return False
    return True

def forceparse(s, goldstandard=False, irelns=False, top=False):
    if top:
        malt.SILENT = True
        s.actions = []
        if goldstandard == False:
            if s.dtree:
                x, goldstandard = malt.dtree2state(s)
                s.goldstandard = goldstandard
                s = x
            else:
                goldstandard = s.goldstandard
                s = malt.STATE(queue=s.leaves)
                s.words = [w for w in s.queue]
        else:
            for r in goldstandard:
                r = goldstandard[r]
                (s.words[r.dtr]).label = r.rel
        if irelns == False:
            irelns = {}
            for d in goldstandard:
                h = goldstandard[d].hd
                if not h in irelns:
                    irelns[h] = {}
                irelns[h][d] = True
    malt.REPLAY = False
    queue = s.queue
    stack = s.stack
    if queue == []:
        return s
        if not len(stack) == 1:
            return False
        if satisfied(goldstandard, s):
            return s
        else:
            return False
    if not stack == [] and not queue == []:
        q0 = queue[0]
        s0 = stack[0]
        """
        leftArc: hd of the queue is hd, top of the stack is dtr.
        We want to check that this is indeed a targeted relation, i.e. that

            goldstandard[s[0].position] = q[0].position > s[0].position

        AND that all q[0] daughters have already been found
        
        """
        for i in range(len(stack)):
            # Comment this out for LDD (currently broken)
            if i > 0: break  
            d = stack[i]
            if d.position in goldstandard and goldstandard[d.position].hd == q0.position and alldtrsfound(d.position, irelns, s.relations):
                s.leftArc(d.label, i=i)
                r = forceparse(s, goldstandard=goldstandard, irelns=irelns)
                if r:
                    return r
                else:                    
                    s.undo()
        """
        rightArc: top of the stack is hd, hd of the queue is dtr.
        We want to check that this is indeed a targeted relation, i.e. that

            goldstandard[q[0].position] = s[0].position > q[0].position

        AND that all q[0] daughters have already been found
        """
        for i in range(len(queue)):
            # Comment this out for LDD (currently broken)
            if i > 0: break
            d = queue[i]
            if d.position in goldstandard and goldstandard[d.position].hd == s0.position and alldtrsfound(d.position, irelns, s.relations):
                s.rightArc(d.label, i=i)
                r = forceparse(s, goldstandard=goldstandard, irelns=irelns)
                if r:
                    return r
                else:
                    s.undo()
    s.shift()
    r = forceparse(s, goldstandard=goldstandard, irelns=irelns)
    if r:
        return r
    else:
        s.undo()
        return False

def reducetags(leaves, tagsize=2):
    for word in leaves:
        word.tag = word.tag[:tagsize]
        
def forceparseall(trees, stackwindow=2, qwindow=2, tagsize=2):
    print "forceparseall, tagsize=%s"%(tagsize)
    malt.SILENT = True
    t = float(len(trees))
    for i in range(len(trees)):
        tree = trees[i]
        reducetags(tree.leaves, tagsize=tagsize)
        if METERING:
            print "forceparseall %.2f"%(i/t)
        s = forceparse(tree, top=True)
        tree.state = s
        s.replay(stackwindow=stackwindow, qwindow=qwindow)
        
import re
def savetrainingdata(trees, tagsize=2, out=sys.stdout):
    spattern = re.compile("(?P<tag2>([A-Z]|-){%s})\S+"%(tagsize))
    with safeout(out) as write:
        for tree in trees:
            if tree.state.text:
                write(spattern.sub("\g<tag2>", tree.state.text))

def getinstances(trees, tagsize=2):
    sw = stringwriter()
    savetrainingdata(trees, tagsize=tagsize, out=sw)
    return id3.csvstring2data(sw.txt, separator="\t")

def makeclassifier(training, stackwindow=2, qwindow=2, doTest=False, tagsize=2):
    print "makeclassifier, tagsize=%s"%(tagsize)
    t0 = now()
    if training[0].dtree:
        training[0].showDTree()
    d = getinstances(training, tagsize=tagsize)
    c = d.id3()
    c.instances = d
    print "making the classifier took %s (%s datapoints)"%(int(timeSince(t0)), len(d.instances))
    if doTest:
        c.testclassifier(d)
        print "classifier accuracy %.3f (%s states out of %s right)"%(float(c.accuracy), c.right, c.right+c.wrong)
    c.instances = d
    c.stackwindow = stackwindow
    c.qwindow = qwindow
    c.training = training
    return c

def incConfusion(confusion, relations, goldstandard, leaves):
    good, bad = confusion[0], confusion[1]
    for r in relations.values():
        if r.dtr in goldstandard and goldstandard[r.dtr].hd == r.hd:
            incTableN([leaves[r.dtr].tag, leaves[r.hd].tag], good)
        else:
            incTableN([leaves[r.dtr].tag, leaves[r.hd].tag], bad)

def getConfusion(sentences):
    confusion = [{}, {}]
    for sentence in sentences:
        incConfusion(confusion, sentence.parsed, sentence.goldstandard, sentence.leaves)
    return confusion

def showConfusion(confusion, out=sys.stdout):
    with safeout(out) as write:
        good, bad = confusion[0], confusion[1]
        alltags = {}
        for tag in good:
            alltags[tag] = True
        for tag in bad:
            alltags[tag] = True
        for tag in sorted(alltags.keys()):
            write("\n%s: "%(tag))
            if tag in good:
                g = sortTable(good[tag])
            else:
                g = {}
            if tag in bad:
                b = bad[tag]
            else:
                b = {}
            for x in g:
                if x[0] in b:
                    write("%s (%s: %.2f), "%(x[0], x[1], float(x[1])/(x[1]+b[x[0]])))
            
def testparser(sentences, parser, msg="", keepscore=True):
    R = 0
    T = 0
    LT = float(len(sentences))
    M = 0
    i = 0
    start = datetime.datetime.now()
    malt.SILENT = False
    for sentence in sentences:
        i += 1
        r, t, m = parser.parse(sentence, keepscore=keepscore, justParse=False)
        R += r
        T += t
        M += (m-1)
        if METERING:
            print "testparser %s, %.2f, %.3f%s"%(i, float(i)/LT, float(R)/float(T), msg)
    return R, T, M, float('%.3f'%(float(R)/float(T))), (datetime.datetime.now()-start).total_seconds()

def timeparser(sentences, parser, msg=""):
    start = datetime.datetime.now()
    malt.SILENT = True
    for sentence in sentences:
        parser.parse(sentence, keepscore=False)
    return (datetime.datetime.now()-start).total_seconds()

def makefold(i, n, l):
    training = []
    testing = []
    for j in range(len(l)):
        if j%n == i:
            testing.append(l[j])
        else:
            training.append(l[j])
    return training, testing

def makeParser(i, training, testing, stackwindow=2, qwindow=3, tagsize=5, doforceparse=False, precision=0.97, threshold=500):
    print "len(training) %s, len(testing) %s"%(len(training), len(testing))
    try:
        x = training[0].state
    except:
        forceparseall(training+testing, stackwindow=stackwindow, qwindow=qwindow, tagsize=tagsize)
    c = makeclassifier(training, stackwindow=stackwindow, qwindow=qwindow, tagsize=tagsize)
    if testing == []:
        c.accuracy = 1.0
        c.right = 0
        c.wrong = 0
    else:
        c.testclassifier(getinstances(testing, tagsize=tagsize))
    p1 = PARSER(c, chunker=False, stackwindow=stackwindow, qwindow=qwindow,tagsize=tagsize)
    if testing == []:
        p1.parseraccuracy = 1.0
    else:
        x = testparser(testing, p1, msg=" (fold %s)"%(i))
        c = p1.classifier
        print "classifier accuracy for fold %s was %.3f (%s out of %s)"%(i, c.accuracy, c.right, c.right+c.wrong)
        print "parsing accuracy for fold %s was %.3f (%s out of %s) @ %s words/sec"%(i, float(x[3]), x[0], x[1], int(x[1]/x[4]))
        p1.parseraccuracy = x[3]
    if precision < 1:
        p2 = PARSER(c, chunking.CHUNKER(chunking.collectGoodSubtrees(training, threshold=threshold, precision=precision)),stackwindow=stackwindow, qwindow=qwindow,tagsize=tagsize)
        print "chunker has %s rules"%(p2.chunker.size())
        if testing == []:
            p2.parseraccuracy = 1.0
        else:
            y = testparser(testing, p2, msg=" (fold %s)"%(i))
            print "accuracy for fold %s was %.3f (%s out of %s) (with chunker, using precision %s)"%(i, float(y[3]), y[0], y[1], precision)
            print "improvement using chunker %.3f"%(y[3]-x[3])
            p2.parseraccuracy = y[3]
    else:
        p2 = p1
    return p2

def onefold(i, n, training, testing, stackwindow=2, qwindow=3, tagsize=5, doforceparse=False, precision=0.95, threshold=500):
    return makeParser(i, training, testing, stackwindow=stackwindow, qwindow=qwindow,tagsize=tagsize, doforceparse=doforceparse, precision=precision, threshold=threshold)
    
def nfold(trees, n=5, stackwindow=2, qwindow=2, tagsize=2, precision=0.95, threshold=500):
    print "nfold, tagsize=%s"%(tagsize)
    a = 0
    ca = 0
    for i in range(0, n):
        training, testing = makefold(i, n, trees)
        if training == []:
            training, testing = testing, training
        print "makeclassifier(%s)"%(i)
        parser = onefold(i, n, training, testing, stackwindow=stackwindow, qwindow=qwindow, tagsize=tagsize, precision=precision, threshold=threshold)
        print "testing[0].dtree before testparser"
        testing[0].showDTree()
        print "testing[0].parsed"
        print tb.showDTree(malt.buildtree(testing[0].parsed, testing[0].leaves))
        a += parser.parseraccuracy
        c = parser.classifier
        ca += c.accuracy
    return a/n, ca/n, c, parser, training, testing
            
def testforce1():
    goldstandard = {}
    for r in [malt.RELATION(1, 0, 'det'),
              malt.RELATION(2, 1, 'subj'),
              malt.RELATION(2, 3, 'ppmod'),
              malt.RELATION(5, 4, 'det'),
              malt.RELATION(3, 5, 'ppcomp')]:
        goldstandard[r.dtr] = r
    s = malt.STATE("a cat sat on the mat")
    forceparse(s, goldstandard, top=True)
    return s

def testforce2():
    goldstandard = {}
    for r in [malt.RELATION(1, 0, 'subj'),
              malt.RELATION(1, 4, 'scomp'),
              malt.RELATION(3, 2, 'det'),
              malt.RELATION(4, 3, 'subj'),
              malt.RELATION(4, 7, 'obj'),
              malt.RELATION(7, 6, 'adjmod'),
              malt.RELATION(7, 5, 'det')]:
        goldstandard[r.dtr] = r
    s = malt.STATE("I know the woman ate a ripe peach")
    forceparse(s, goldstandard, top=True)
    return s

def testforce3():
    goldstandard = {}
    for r in [malt.RELATION(2, 0, 'det'),
              malt.RELATION(2, 1, 'adjmod'),
              malt.RELATION(4, 3, 'subj'),
              malt.RELATION(4, 2, 'obj')]:
        goldstandard[r.dtr] = r
    s = malt.STATE("the main course I enjoyed")
    forceparse(s, goldstandard, top=True)
    return s

def testforce(s, rlist):
    goldstandard = {}
    for r in rlist:
        goldstandard[r.dtr] = r
    s = malt.STATE(s)
    forceparse(s, goldstandard, top=True)
    return s

def runtrainingexample(ex):
    ex = eval(ex)
    return testforce(ex[0], [malt.RELATION(r[0], r[1], r[2]) for r in ex[1:]])
    
def readtrainingset(ifile='training.txt', stackwindow=2, qwindow=2):
    runtrainingset(src=open(ifile).read(), stackwindow=stackwindow, qwindow=qwindow)
    
def runtrainingset(src, stackwindow=2, qwindow=2):
    trainingdata = [x.strip() for x in src.split("\n\n")]
    trainingdata = [runtrainingexample(x) for x in trainingdata if not x == ""]
    s = ""
    for i in range(2*window):
        s += "f%s,"%(i)
    print s+"a"
    csv = ""
    for t in trainingdata:
        t.text = False
        t.replay(stackwindow=2, qwindow=2)
        csv += t.text
    return csv

"""
End to end: call the Prolog parser with the target strings; call runtrainingset
on what that sends back; convert it to trainingdate by doing id3.csvstring2data,
then do the classification with id3.id3
"""

def end2end():
    stdout = sys.stdout
    sys.stdout = open(os.devnull, 'wb')
    d = runtrainingset(runprocess("sicstus --noinfo --nologo --goal restore('HPSG/hpsg'),train,halt."))
    sys.stdout = stdout
    return id3.csvstring2data(d).id3()

def getWindow(i, w, s, hd):
    if type(s) == "STATE":
        s = [x.tag for x in s.words]
    l = s[max(0, i-1-w):max(0, i-1)]
    while len(l) < w:
        l = ['*']+l
    r = s[i:i+w]
    while len(r) < w:
        r.append('*')
    return "%s_%s: %s < %s"%(l, r, s[i], s[hd-1])

def compstates(s0, s1):
    x = s1.score-s0.score
    if x == 0:
        return 0
    elif x < 0:
        return 1
    else:
        return -1

def scoreState(goldstandard, s, tree):
    if goldstandard:
        """
        goldstandard is the gold standard
        s.relations is what the classifier supplied
        """
        right = 0
        for r in s.relations.values():
            d = r.dtr
            h = r.hd
            try:
                dtag = tree.leaves[d].tag
            except Exception as e:
                print "%s in scoreState"%(e)
                print r, d
                print tree.leaves
                tree.showPSTree()
                tree.showDTree()
                raise(e)
            htag = tree.leaves[h].tag
            if d in goldstandard:
                h0 = goldstandard[d].hd
                h0tag = tree.leaves[h0].tag
            else:
                h0 = -1
                h0tag = "DUMMY"
            if d in goldstandard and h==h0:
                right += 1
        return right
    else:
        return 0

"""
parse can be called in two ways:
-- to parse a string. In that case you have to supply a tagger, and
   what you probably want as a result is a tree
-- to reanalyse an already parsed string (encapsulated as a
   "SENTENCE") and compare it with the existing analysis for testing,
   in which case what you want is some scores
"""

def ss(msg):
    print msg
    sys.stdin.readline()
    
def parse(tree, classifier, tagger=False, tagsize=5, singlestep=False, silent=True, stackwindow=2, qwindow=3, keepscore=True, preclassified=False, justParse=False):
    malt.SILENT = silent
    if type(tree) == "SENTENCE":
        if tree.dtree:
            s, goldstandard = malt.dtree2state(tree)
        else:
            goldstandard = tree.goldstandard
            s = malt.STATE(text=tree.leaves)
        words = s.words
    else:
        words = [malt.WORD(w[0], w[1]) for w in tagger.tag(tree)]
        tree = tb.SENTENCE(False, False, False, False)
        tree.leaves = words
        s = malt.STATE(text=words)
        goldstandard = False
    for w in s.words:
        w.tag = w.tag[:tagsize]
    features = sorted(classifier.features.keys())
    agenda = [s]
    s.score = 0.0
    while not agenda == []:
        s = agenda.pop()
        if s.queue == []:
            """
            What we'd like to do (pace Sardar) is to insist
            that the stack should have only one item on it,
            and if not then we go on to the next task on
            the agenda. That works nicely if we use the
            head percolation table that has CC as the head
            whenever possible; but overall the one that has
            CC as worst choice for the head does better (as
            with Maytham), and in that case trying to
            get to a nice terminal state by choosing other
            options from the agenda gets stuck. So we have
            to do something more simple-minded:
            attaching the things that haven't been attached
            to anything to their neighbours seems to work
            quite nicely. It's not exactly systematic, but
            it gets a surprising number of things right.
            """
            for i in range(len(s.stack)-1):
                hd = s.stack[i+1]
                dtr = s.stack[i]
                s.relations[dtr.position] = malt.RELATION(hd.position, dtr.position, 'mod')
        d = s.stateDescriptor(False, qwindow=classifier.qwindow, stackwindow=classifier.stackwindow)
        t = id3.INSTANCE(features, d)
        """
        The classifier can return several options: it would
        be nice to weigh them up, using influences from the
        grammar, and then order the agenda to pay due
        attention to the confidence of the classifier and
        the constraints from the grammar, but I can't find
        any useful influences. So I'm just choosing the
        best and working with that. I've left it as a loop,
        even though it's currently a pointless loop because
        the list only ever has one item on it, so that I
        can revisit it some time if I have the energy.
        """
        actions = sortTable(classifier.classify(t, printing=False))
        if actions == []:
            print "no action found"
        for action in actions:
            s1 = s.copy()
            s1.score = s.score+10
            if singlestep:
                print '***********************************'
                s1.showState()
                ss("action %s\ns.relations %s\nd %s\n"%(action, s.relations, d))
            action = eval("malt.STATE.%s"%(action[0]))
            WARNINGS = True
            try:
                if action(s1, warnings=WARNINGS, throwException=True):
                    agenda.append(s1)
                    break
            except Exception as e:
                if agenda == []:
                    if not s1.queue == []:
                        malt.STATE.shift(s1, warnings=WARNINGS)
                        agenda.append(s1)
                    else:
                        break
        agenda.sort(cmp=compstates)
    right = 0
    tree.parsed = s.relations
    if justParse:
        return tree
    if type(tree) == "str" or not keepscore:
        return malt.buildtree(s.relations, s.words)
    else:
        right1 = scoreState(goldstandard, s, tree)
        if preclassified:
            usePreclassifiedHDs(preclassified, s.relations)
            right2 = scoreState(goldstandard, s, tree)
            return right2, len(goldstandard), len(s.stack)
        else:
            return right1, len(goldstandard), len(s.stack)

def usePreclassifiedHDs(preclassified, relations):
    for x in preclassified:
        if not (x in relations and relations[x].hd == preclassified[x].hd):
            if x in relations:
                relations[x].hd = preclassified[x].hd
            else:
                try:
                    relations[x] = preclassified[x]
                except Exception as e:
                    print "relations %s, x %s"%(relations, x)
                    raise e
                
def justParse(sentences, classifier):
    for s in sentences:
        parse(s, classifier, justParse=True, tagger=False)
        
def parseexamples(sentences, classifier, tagger=False):
    for s in sentences:
        # s = s.sentence()
        x = pstree(parse(s, classifier, tagger=False))
        print r"""
\BREAK
\VPARA
{\Large
\begin{examples}
\item
%s
\end{examples}

%s
}
"""%(s, x)
     
def subtrees(tree, alltrees):
    t = []
    for d in tree[1:]:
        t.append(d[0].tag)
        subtrees(d, alltrees)
    incTableN([tree[0].tag, str(t)], alltrees)

def allsubtrees(trees):
    alltrees = {}
    for tree in trees:
        subtrees(tree.dtree, alltrees)
    return alltrees

def geterrors(tree, errors):
    goldstandard = tree.goldstandard
    parsed = tree.parsed
    for r in parsed:
        d = r.dtr
        h = r.hd
        if d in goldstandard and goldstandard[d].hd == h:
            incTableN([tree.leaves[d].tag, tree.leaves[h].tag, 'CORRECT'], errors)
            if not 'WRONG' in errors[tree.leaves[d].tag][tree.leaves[h].tag]:
                errors[tree.leaves[d].tag][tree.leaves[h].tag]['WRONG'] = 0
        else:
            incTableN([tree.leaves[d].tag, tree.leaves[h].tag, 'WRONG'], errors)
            if not 'CORRECT' in errors[tree.leaves[d].tag][tree.leaves[h].tag]:
                errors[tree.leaves[d].tag][tree.leaves[h].tag]['CORRECT'] = 0

def allerrors(trees, filter=[]):
    errors = {}
    summaryerrors = {}
    for tree in trees:
        geterrors(tree, errors)
    for x in errors:
        for y in errors[x]:
            incTableN([x, 'CORRECT'], summaryerrors, n=errors[x][y]['CORRECT'])
            incTableN([x, 'WRONG'], summaryerrors, n=errors[x][y]['WRONG'])
    right = 0
    wrong = 0
    for x in summaryerrors:
        if x in filter:
            continue
        right += summaryerrors[x]['CORRECT']
        wrong += summaryerrors[x]['WRONG']
    return errors, summaryerrors, right, wrong

def sorterrortable(t):
    return sortTable({x:(t[x]['WRONG']/float(t[x]['WRONG']+t[x]['CORRECT']), t[x]['WRONG']+t[x]['CORRECT']) for x in t})

class PARSER:

    def __init__(self, classifier, chunker=False, stackwindow=2, qwindow=3, tagsize=5):
        self.chunker = chunker
        self.classifier = classifier
        self.stackwindow = stackwindow
        self.qwindow = qwindow
        self.tagsize = tagsize

    def parse(self, sentence, tagger=False, keepscore=True, justParse=True):
        t = parse(sentence, self.classifier, tagger=tagger, tagsize=self.tagsize, stackwindow=self.stackwindow, qwindow=self.qwindow, keepscore=keepscore, preclassified=False, justParse=justParse)
        if justParse:
            t.dtree = malt.buildtree(t.parsed, t.leaves)
        return t

    def dump(self, dfile):
        self.classifier.training = False
        self.classifier.instances = False
        self.classifier.classification = False
        useful.dump(self, dfile)
