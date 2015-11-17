"""
TBL.PY: implementation of Brill retagging. I think it's quite a bit
faster than the NLTK implementation, but more importantly you can
design your own set of templates.

Programs to support COMP34411 Natural Language Systems: these programs
have more comments in them than I put in code that I write for my own use, but
it's unlikely to be enough to make them easy to understand. If you
play with them then I hope they will help with understanding the ideas
and algorithms in the course. If you try to read the source code,
you'll probably just learn what a sloppy programmer I am.
"""

from useful import *
import tag
reload(tag)
import tb
import re
from word import *

"""
Pretagged is assumed to be a list of WORDs: we get that as
the output of tb.readtb()--this is all being
stitched together so that we can do Brill retagging on the
output of MXL tagger when that has been trained on the
English PTB.

To do the whole thing, do

tbl.trainwithmxlandbrill()

or (better, because it separates training the taggers
from getting the training data from the treebank, which
is done as a side-effect of training the dependency
parser on the treebank)

N is the amount of data to be used for learning tagging rules. We have to
chop off another K items for the testset.

N = 10000
K = 10000
instances, pretagged = tbl.tb.readtb()
mxl = tbl.tag.mxltagger(pretagged[:-(N+K)], tagsize=2)
rules = tbl.trainwithmxlandbrill(pretagged=pretagged, mxl=mxl, N=N, K=K, printing=5, tagsize=2, atagsize=2)

The tagsize makes a difference: the shorter (coarser) the tagset, the
less scope there is for mistakes, so the lower the WER. It is worth
looking at what happens of you change the tagsize in different places:

-- you could train the MXL tagger with finer tags than you use in the
   TBL rules
-- you could train the TBL rules with finer tags than you use in the
   application

rules = tbl.trainwithmxlandbrill(mxltagsize=1000, tagsize=1000, atagsize=1000) (fine-grained tags at each stage) gives me

Before retagging 0.8765
After retagging 0.9068

rules = tbl.trainwithmxlandbrill(mxltagsize=1000, tagsize=1000, atagsize=2) (fine-grained for training, coarse for testing) gives

Before retagging 0.898
After retagging 0.9341

rules = tbl.trainwithmxlandbrill(mxltagsize=1000, tagsize=2, atagsize=2) (fine-grained for MXL, coarse for TBL and testing) gives

Before retagging 0.8903
After retagging 0.9503

rules = tbl.trainwithmxlandbrill(mxltagsize=2, tagsize=2, atagsize=2) (coarse for everything) gives

Before retagging 0.8903
After retagging 0.9503

I expected that we would get higher coarse-level accuracy if we
trained with fine-grained tags and then tested with coarse ones, since
there is more information available when doing the training with
fine-grained tags, so it seemed plausible that the underlying rule-set
would be more sensitive to local constraints, and that when we
coarsened it all afterwards then we would get an overall
improvement. But the opposite happens. Why?

It's also worth looking at what happens if we shift more of the
training data from training the MXL tagger to training the TBL
rules. plot lets you see the values before and after retagging for a
various distributions of the training data between the two components
(values are calculated for n0**(p*i)).

Too little data for MXL gives TBL too much work to do. Too little
data for TBL means it can't do the (smaller) amount of work that it
has to do as effectively.

Values plotted by TandD.tbl.plot(pretagged, n0=200, n1=100000, p=1.25)
are shown in tblplot.csv and tblplot.eps (in COMP34411/TEX) (plot puts
the value of n0 on the line between the two scores: too fiddly to do
anything better, just have to hand-edit it before importing it into a
spreadsheet).

"""
METERING = 5 # METERING in here has to be an integer: 5 is a good value
tag.METERING = METERING

def trainwithmxlandbrill(pretagged=False, mxl=False, threshold=0.0005, S=0, N=10000, K=10000, mxltagsize=2, tagsize=2, atagsize=False):
    N += K
    if not atagsize:
        atagsize = tagsize
    if pretagged == False:
        instances, pretagged = tb.readtb()
    for x in pretagged:
        x.tag = x.tag[:tagsize]
    if mxl == False:
        mxl = tag.mxltagger(pretagged[S:-N], tagsize=mxltagsize)
    trainingdata = getTrainingData(pretagged, mxl.tag)
    if METERING:
        print "Accuracy of MXL tagger on the training data (size %s): %s"%(len(trainingdata[S:-N]), accuracy(trainingdata[:-N])[0])
        print "Accuracy of MXL tagger on reserved data (size %s): %s"%(len(trainingdata[-N:]), accuracy(trainingdata[-N:])[0])
    templates = readTemplates()
    if METERING:
        print underline("Extracting TBL rules from half the reserved data (%s - %s)"%(-N, -K))
    rules = findAllInstances(templates, trainingdata[-N:-K], threshold=threshold)
    bt = brilltagger(mxl, rules)
    if METERING:
        print underline("Testing extracted TBL rules on the remainder of the reserved data (%s)"%(-K))
    bt.confusion = applyrules(trainingdata[-K:], rules, tagsize=atagsize, trainingsize=len(trainingdata[S:-N]))
    return bt
    
def getTrainingData(pretagged, tag):
    tagged = tag([x.form for x in pretagged])
    return [(x.form, y[1], x.tag) for x, y in zip(pretagged, tagged)]

def accuracy(trainingdata, tagsize=1000):
    right = 0
    confusion = {}
    for x in trainingdata:
        if x[1][:tagsize] == x[2][:tagsize]:
            right += 1
        incTableN([x[2], x[1]], confusion)
    return float(right)/float(len(trainingdata)), confusion

def showConfusion(confusion):
    t = {}
    for x in confusion:
        t[x] = sortTable(confusion[x])
    for x in t:
        l = t[x]
        n = l[0][1]
        k = 0.0
        for p in l[1:]:
            k += p[1]
        if n+k == 0:
            print x, t[x]
        else:
            print x, t[x], float(n)/float(n+k)
         
templatePattern = re.compile("#(?P<name>.*?)\s*:\s(?P<t1>\w*)\s*>\s*(?P<t2>\w*)\s*if\s+(?P<conditions>.*?);", re.DOTALL)

templates = """
#t0(T1, T2, T3): T1 > T2 if tag[0]=T3;
#t1(T1, T2, T3, T4): T1 > T2 if tag[0]=T3 and tag[1]=T4;
#t2(T1, T2, T3, T4): T1 > T2 if tag[0]=T3 and tag[-1]=T4;
#t3(T1, T2, T3, T4): T1 > T2 if tag[0]=T3 and tag[1, 2]=T4;
#t4(T1, T2, T3, T4): T1 > T2 if tag[0]=T3 and tag[-1, -2]=T4;
#t5(T1, T2, T3, T4, T5): T1 > T2 if tag[0]=T3 and tag[1]=T4 and tag[-1]=T5;
#w0(T1, T2, T3): T1 > T2 if word[0]=T3;
#w1(T1, T2, T3, T4): T1 > T2 if word[0]=T3 and tag[1]=T4;
#w2(T1, T2, T3, T4): T1 > T2 if word[0]=T3 and tag[-1]=T4;
#w5(T1, T2, T3, T4, T5): T1 > T2 if word[0]=T3 and tag[1]=T4 and tag[-1]=T5;
"""

conditionPattern = re.compile("(?P<what>\S*)\[(?P<range>-?\d+(\s*,\s*-?\d+)*)\]\s*=(?P<value>\w*)\s*(and)?")

def makeRange(s):
    return [int(i) for i in re.compile("\s*,\s*").split(s)]

def readCondition(i):
    return [condition(i.group("what").strip(), makeRange(r), i.group("value")) for r in i.group("range").strip().split("and")]

def readConditions(conditions):
    allconditions = []
    for i in conditionPattern.finditer(conditions):
        allconditions += readCondition(i)
    return allconditions

def inrange(i, l):
    return i >= 0 and i < len(l)

class condition:

    @staticmethod
    def getword(i, words):
        return words[i][0]

    @staticmethod
    def gettag(i, words):
        return words[i][1]
    
    @staticmethod
    def checktag(i, r, words, target):
        for j in r:
            if inrange(i+j, words) and words[i+j][1] == target:
                return True
        return False
    
    @staticmethod
    def checkword(i, r, words, target):
        for j in r:
            if inrange(i+j, words) and words[i+j][0] == target:
                return True
        return False
    
    @staticmethod
    def gstag(r, words):
        return words[i][2]
    
    def __init__(self, what, where, value):
        self.what = what
        self.where = where
        self.value = value
        self.func = eval('condition.get%s'%what)

    def __repr__(self):
        return "%s%s=%s"%(self.what, self.where, self.value)

    def get(self, i, words):
        return self.func(i+self.where, words)

    def check(self, i, words, target):
        return self.func(i+self.where, words) == target
        
class template:

    def __init__(self, name, T0, T1, conditions):
        self.name = name
        self.T0 = T0
        self.T1 = T1
        self.conditions = readConditions(conditions)
        
    def __repr__(self):
        return "#%s: %s > %s if %s;"%(self.name, self.T0, self.T1, self.conditions)

    def instantiate(self, d):
        form = str(self)
        for k in d:
            form = form.replace(k, d[k])
        return form

    @staticmethod
    def word(word):
        return word[0]

    @staticmethod
    def tag(word):
        return word[1]
    
    @staticmethod
    def gstag(word):
        return word[2]

    def findInstances(self, words, allinstances):
        for i in range(0, len(words)):
            word = words[i]
            if not template.tag(word) == template.gstag(word):
                options = [[self.T0, [template.tag(word)]],
                           [self.T1, [template.gstag(word)]]]
                for c in self.conditions:
                    cd = []
                    for j in c.where:
                        if inrange(i+j, words):
                            cd.append(c.func(i+j, words))
                    options.append([c.value, cd])
                d = {}
                enumerateall(options, d, (lambda: incTable("%s::%s"%(self.name, d), allinstances)))
                
    @staticmethod
    def tryReset(i, words, tag):
        if words[i][1] == tag and words[i][2] == tag:
            return 0
        elif words[i][2] == tag:
            return 1
        else:
            return -1
        
    @staticmethod
    def doReset(i, words, tag):
        words[i][1] = tag
        return True
        
    def makeInstance(self, dict):
        s = ""
        for c in self.conditions:
            c = """condition.check%s(i, %s, words, "%s")"""%(c.what, c.where, dict[c.value])
            if s == "":
                s = "%s"%(c)
            else:
                s += " and %s"%(c)
        s = """(lambda i, words: template.tryReset(i, words, "%s") if %s else 0)"""%(dict[self.T1], s)
        s = s.replace('"""', """'"'""")
        f = eval(s)
        f.src = s
        return f

    def makeRule(self, dict):
        s = ""
        for c in self.conditions:
            c = """condition.check%s(i, %s, words, "%s")"""%(c.what, c.where, dict[c.value])
            if s == "":
                s = "%s"%(c)
            else:
                s += " and %s"%(c)
        s = """(lambda i, words: template.doReset(i, words, "%s") if %s else 0)"""%(dict[self.T1], s)
        s = s.replace('"""', """'"'""")
        f = eval(s)
        f.src = s
        return f

class rule:

    def __init__(self, template, reset, grossScore, netScore):
        self.template = template
        self.reset = reset
        self.grossScore = grossScore
        self.netScore = netScore

    def __str__(self):
        return "rule(%s, %s, grossScore:%s, netScore: %s)"%(self.template, self.reset.src, self.grossScore, self.netScore)

    def __call__(self, i, text):
        """
        We may have converted reset back into a string in order to pickle it,
        so if this goes wrong we will eval it (and set that as the value of reset)
        """
        try:
            return self.reset(i, text)
        except TypeError:
            r = self.reset
            self.reset = eval(r)
            self.reset.src = r
            return self.reset(i, text)

    def removeFunctions(self):
        self.reset = self.reset.src
        
class brilltagger:

    def __init__(self, basetagger, rules):
        self.basetagger = basetagger
        self.rules = rules

    def tag(self, text):
        text = self.basetagger.tag(text)
        for rule in self.rules:
            for i in range(len(text)):
                rule(i, text)
        return text

    """
    You can't save the tagger while the rules are embodied as compiled functions.
    So we replace them by their source code before we save it, and then recompile
    them on the fly when they're needed
    """
    
    def removeFunctions(self):
        for rule in self.rules:
            rule.removeFunctions()

    def dump(self, dfile):
        self.removeFunctions()
        dump(self, dfile)
    
def enumerateall(options, instance, task):
    if options == []:
        task()
    else:
        x, l = options[0]
        for y in l:
            instance[x] = y
            enumerateall(options[1:], instance, task)
            del instance[x]
            
def checkvar(var, value, table):
    if var in table:
        return table[var] == value
    else:
        table[var] = value
        return True
                    
def readTemplates(templates=templates):
    alltemplates = []
    for t in [template(i.group('name'), i.group('t1'), i.group('t2'), i.group('conditions')) for i in templatePattern.finditer(templates)]:
        alltemplates.append(t)
    return alltemplates
    
def findAllInstances(templates, text, threshold=0.0005):
    text = [list(t) for t in text]
    """
    It makes sense to express the threshold as the minimum percentage
    increase, but it's actually easiest to use it as a simple count
    """
    threshold = threshold*len(text)
    if METERING:
        print "Initial score %.4f\nThreshold %s, dataset %s"%(float(accuracy(text)[0]), threshold, len(text))
    templatetable = {}
    for t in templates:
        templatetable[t.name] = t 
    rules = []
    while True:
        allinstances = {}
        if METERING:
            print underline("Finding initial instances")
        for t in templates:
            t.findInstances(text, allinstances)
        if METERING:
            print "Found--reorganising them"
        instances = []
        for i in allinstances:
            k, d = i.split("::")
            d = eval(d)
            f = templatetable[k].makeInstance(d)
            instances.append([allinstances[i], f, k, d])
        instances.sort()
        instances.reverse()
        if METERING:
            print underline("Top %s candidate rules"%(METERING))
            for x in instances[:METERING]:
                print "Candidate rule %s: gross score %s"%(templatetable[x[2]].instantiate(x[3]), x[0])
        bestscore = 0
        best = False
        if METERING:
            print "Sorted--scoring them"
        l = []
        for i in instances:
            f = i[1]
            if i[0] < bestscore:
                break
            score = 0
            for j in range(len(text)):
                score += f(j, text)
            i.append(score)
            if score > bestscore:
                bestscore = score
                best = i
            if METERING:
                l.append((i[-1], i))
        if bestscore < threshold:
            break
        r = makeRule(best, templatetable)
        if METERING:
            print underline("Top %s net scoring rules")%(METERING)
            l.sort()
            l.reverse()
            for i in l[:METERING]:
                t = makeRule(i[1], templatetable)
                print "rule: %s, gross score %s, net score %s"%(t.template, t.grossScore, t.netScore)
        for j in range(len(text)):
            r(j, text)
        if METERING:
            print "Score %.4f"%(float(accuracy(text)[0]))
        rules.append(r)
    return rules

def makeRule(k, templatetable):
    t = str(templatetable[k[2]])
    f = k[1]
    for x in k[3]:
        t = t.replace(x, k[3][x])
    f.template = t
    t = templatetable[k[2]]
    d = k[3]
    return rule(t.instantiate(d), t.makeRule(d), k[0], k[-1])

def applyrules(testdata, rules, tagsize=1000, trainingsize=0):
    before = accuracy(testdata, tagsize=tagsize)[0]
    testdata = [list(t) for t in testdata]
    for rule in rules:
        for i in range(len(testdata)):
            rule(i, testdata)
    after, confusion = accuracy(testdata, tagsize=tagsize)
    if METERING:
        print "Before retagging %s (training size = %s)"%(before, trainingsize)
        print "After retagging %s (training size = %s)"%(after, trainingsize)
        print underline("Confusion matrix")
        tag.showConfusion(confusion)
    else:
        print ", %s, %s"%(before, after)
    return confusion

def plot(pretagged, p=1.5, n0=500, n1=40000):
    while n0 < n1:
        print n0
        rules = trainwithmxlandbrill(pretagged=pretagged, N=n0, mxltagsize=2, tagsize=2, atagsize=2)
        n0 = int(p*n0)

import math
def importdict(targetdict, importeddict):
    for x in importeddict:
        NN = 0
        VV = 0
        for k in importeddict[x]:
            if k[0] == 'N':
                NN += importeddict[x][k]
            elif k[0] == 'V':
                VV += importeddict[x][k]
        if (NN > 0 or VV > 0) and not x in targetdict:
            targetdict[x] = {}
        if NN > 0:
            targetdict[x]['NN'] = math.sqrt(NN)
        if VV > 0:
            targetdict[x]['VB'] = math.sqrt(VV)
        if NN > 0 or VV > 0:
            normalise(targetdict[x])
