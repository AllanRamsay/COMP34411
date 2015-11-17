"""
COMP34411.PY: this one brings together tagging and MALT-style dependency
parsing in one place, using the fragment of the PTB that is provided
by the NLTK as training/testing data.

Programs to support COMP34411 Natural Language Systems: these programs
have more comments in them than I put in code that I write for my own
use, but it's unlikely to be enough to make them easy to
understand. If you play with them then I hope they will help with
understanding the ideas and algorithms in the course. If you try to
read the source code, you'll probably just learn what a sloppy
programmer I am.

A lot of the programs used in this course need training data. I am
currently using the data that is supplied at
https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/LRT-1478. It's
slightly bigger than the data supplied in the NLTK, it's a bit better
tagged, and it comes as dependency trees rather than phrases structure
trees, so I don't need to do the conversion to dependency trees (which
is a bit dodgy for the NLTK data). I think that some of their analyses
are pretty weird, so I do need to do some postprocessing to get ones
that I like, but by-and-large I get better accuracy if I use their
relations for training and do some post-processing than if I apply the
same rules before training as preprocessing.

Get the data
------------
sentences, pretagged = COMP34411.conll.readconll()
sentences, pretagged = COMP34411.tb.readtb()


sentences is a set of sentences with associated phrase-structure trees
and dependency trees. The dependency trees are constructed on the
basis of a reasonable enough set of head-percolation rules, with zero
items deleted and no attempt to do anything with traces.

pretagged is a set of words, each with a form and a tag. At this point
the tags are pretty much what was in the original data. We may later
decide to use a cut down set, but at this point they are basically the
originals.

Get a tagger
------------
N is the amount of data to be used for learning tagging rules. We have to
chop off another K items for the testset.

Chopping tags down to two characters turns out to be a sensible thing

to do--the tagger is more accurate, and it doesn't seem to do the
parser much harm.

S = 0
N = 10000
K = 10000
COMP34411.tbl.METERING = 1
brilltagger = COMP34411.tbl.trainwithmxlandbrill(pretagged=pretagged, S=S, N=N, K=K, tagsize=2)

To plot the effect of training size on accuracy, do

for S in range(20, 0, -1):
    brilltagger = COMP34411.tbl.trainwithmxlandbrill(pretagged=pretagged, S=S*10000, N=N, K=K, tagsize=2)

Then extract lines with "Making mxltagger", "Before" and "After" and make a .csv file. Outcome using UD is that BEFORE increases steadily, but AFTER is fairly stable: in other words, Brill retagging actually catches a lot of the errors that arise if you train with MXL without enough data.

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

Values plotted by COMP34411.tbl.plot(pretagged, n0=200, n1=100000, p=1.25)
are shown in tblplot.csv and tblplot.eps (in COMP34411/TEX) (plot puts
the value of n0 on the line between the two scores: too fiddly to do
anything better, just have to hand-edit it before importing it into a
spreadsheet).

Get a parser
------------

COMP34411.fp.METERING = True
COMP34411.fp.forceparseall(sentences, tagsize=2)
n = 3000
clsf = COMP34411.fp.makeclassifier(sentences[:n])


#Then you can test it with

COMP34411.fp.testparser(sentences[n:], classifier=clsf)


#You can do nfold-X-validation by doing

COMP34411.fp.nfold(sentences, n=5)


#To just use it for parsing, get a classifier clsf and a tagger btagger and do

COMP34411.fp.parse("the cat sat on the mat", clsf, brilltagger)

# You can do the whole thing in one fell swoop by

sentences, pretagged, brilltagger, clsf, training, testing = COMP34411.comp34411(metering=1, brilltagger=False, sentences=False, pretagged=False, qwindow=3, stackwindow=2, folds=5, tagsize=2, precision=1)


# You can fix brilltagger and/or sentences+pretagged if you've already got values for them. If folds=0 then
# don't bother doing nfold testing. Defaults are as shown.

"""

from useful import *
import tag
reload(tag)
import tb
reload(tb)
import tbl
reload(tbl)
import forceparse as fp
reload(fp)
"""
import te
reload(te)
"""
import conll

import datetime

try:
    tagger = load('tagger.pck')
except:
    print "No 'tagger.pck' available"
    
def comp34411(metering=0, brilltagger=False, sentences=False, pretagged=False, qwindow=2, stackwindow=False, folds=5, tagsize=2, atagsize=False, forced=False, precision=0.97, threshold=500):
    print "reading data"
    tb.METERING = metering
    if not atagsize:
        atagsize = tagsize
    if stackwindow == False:
        stackwindow = qwindow
    if not sentences:
        sentences, pretagged = tb.readtb()
    N = 10000
    K = 10000
    print "initial values for pretagged[:5], sentences[0]"
    print pretagged[:5]
    sentences[0].showDTree()
    tbl.METERING = metering
    tbl.tag.METERING = metering
    if not brilltagger:
        print "making tagger"
        t0 = datetime.datetime.now()
        brilltagger = tbl.trainwithmxlandbrill(pretagged=pretagged, N=N, K=K, mxltagsize=tagsize, tagsize=tagsize, atagsize=atagsize)
        print "training the tagger took %s seconds"%((datetime.datetime.now()-t0).seconds)
        print "pretagged[:5], sentences[0] after training the tagger"
        print pretagged[:5]
        sentences[0].showDTree()
    fp.METERING = metering
    if not forced:
        print "forceparse"
        t0 = datetime.datetime.now()
        fp.forceparseall(sentences, stackwindow=stackwindow, qwindow=qwindow,tagsize=tagsize)
        print "pretagged[:5], sentences[0] after forceparseall"
        print "forced parsing took %s seconds"%((datetime.datetime.now()-t0).seconds)
    print "nfold %s (precision = %s)"%(folds, precision)
    a, ca, c, parser, training, testing = fp.nfold(sentences, n=folds, stackwindow=stackwindow, qwindow=qwindow, tagsize=tagsize, precision=precision, threshold=threshold)
    print "average accuracy over all folds (precision = %s): %.3f\naverage classifier accuracy %.3f"%(precision, float(a), float(ca))
    print """
return the parser from the last fold & the training and testing sets
for that parser so we can do subsequent experiments soundly
"""
    return sentences, pretagged, brilltagger, parser, training, testing

def countrules(d):
    if type(d) == "ANSWERTABLE":
        n = 1
        for x in d.answers:
            n += countrules(d.answers[x])
        return n
    else:
        return 1
        
def testwindows(sentences, pretagged, I0=2, I1=5, J0=2, J1=5):
    for i in range(I0, I1+1): 
	for j in range(J0, J1+1):
            print "QWINDOW %s, STACKWINDOW %s"%(i, j)
            sentences, pretagged, brilltagger, clsf = comp34411(metering=1, brilltagger=True, sentences=sentences, pretagged=pretagged, qwindow=i, stackwindow=j, folds=10, tagsize=5, atagsize=False)

import re
def collectscores(ifile):
    p = re.compile("(QWINDOW (?P<Q>\d*), STACKWINDOW (?P<S>\d*))|(average accuracy over all folds: (?P<averageAccuracy>\S*)\s*)|(overall parser accuracy for.*was\s*(?P<overallAccuracy>(\d|\.)*).*)|(average classifier accuracy (?P<avclassifierAccuracy>\S*)\s*)|(classifier accuracy\s*(?P<classifierAccuracy>(\d|\.)*)\s*)")
    Q = False
    print "\t5-fold parsing accuracy\t5-fold classifier accuracy\t0-fold parsing accuracy\t0-fold classifier accuracy"
    for line in open(ifile):
        m = p.match(line.strip())
        if m:
            if m.group("Q"):
                if Q and not m.group("Q") == Q:
                    print "\n"
                Q = m.group("Q")
                thisOne = ["%s,%s"%(m.group("Q"), m.group("S"))]
            if m.group("averageAccuracy"):
                thisOne.append(m.group("averageAccuracy"))
            if m.group("avclassifierAccuracy"):
                thisOne.append(m.group("avclassifierAccuracy"))
            if m.group("classifierAccuracy"):
                thisOne.append(m.group("classifierAccuracy"))
            if m.group("overallAccuracy"):
                thisOne.append(m.group("overallAccuracy"))
                print "%s\t%s\t%s\t%s\t%s"%(thisOne[0], thisOne[1], thisOne[2], thisOne[4], thisOne[3])
            
