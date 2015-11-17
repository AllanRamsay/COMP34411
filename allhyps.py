"""
TE.PY: simple minded textual entailment by dynamic time warping with
WordNet lexical relations. Do pre-computation of the word \subset word
relations.

Programs to support COMP34411 Natural Language Systems: these programs
have more comments in them than I put in code that I write for my own
use, but it's unlikely to be enough to make them easy to
understand. If you play with them then I hope they will help with
understanding the ideas and algorithms in the course. If you try to
read the source code, you'll probably just learn what a sloppy
programmer I am.
"""

from nltk.corpus import wordnet
from useful import *
import dtw
reload(dtw)

"""
A trick: I want the tagger to be loaded, but I don't want to reload it
each time I reload the program. The try will succeed if "tagger" is already
defined: if not then we will have to read it
"""

try:
    tagger
    print "tagger already loaded"
except:
    try:
        tagger = load("tagger.pck")
        print "tagger loaded from tagger.pck"
    except:
        print "No tagger loaded"
        tagger = False
        
"""
Try to get the root form -- you won't find inflected forms in wordnet
"""
def getRoot(w, tag):
    try:
        return wordnet.morphy(w, tag)
    except:
        return w

"""
Given a synset, work upwards through the lattice: save the parents and 
ancestors in a great big table (annoying to have to set the default to
False and then turn it into a table as appropriate, but if you set it to
an empty table then you can find yourself updating the same table on
subsequent occasions)
"""
def getHyps(s, hyps=False, n=1):
    if hyps == False:
        hyps = {}
    for h in s.hypernyms():
        if not h in hyps or hyps[h] > n:
            hyps[h] = n
            getHyps(h, hyps, n=n+1)
    return hyps

"""
Do it for all synsets in l: use the tag if it's specified. The table
we really want links words to words, rather than synsets to synsets,
so we do it for all the lemmas of each synset. That's a touch
dangerous, because by doing that I'm saying that W1 \subseteq W2 is
there is any interpretation of W1 which is a subset of some
interpretation of W2. I think that's sensible, and I can't see any
reasonable alternative (every interpretation of W1 is a subset of
every interpretation of W2 anyone?). Call it abductive inference and
it sounds fancy and posh.
"""

def getAllHyps(l, tag=False):
    allhyps = {}
    for ss in l:
        if tag and not ss.pos == tag:
            continue
        h = getHyps(ss)
        if not h == {}:
            for w1 in ss.lemma_names:
                if "_" in w1:
                    continue
                for superset in h:
                    if tag and not superset.pos == tag:
                        continue
                    n = h[superset]
                    for w2 in superset.lemma_names:
                        if "_" in w2:
                            continue
                        if not w1 in allhyps:
                            allhyps[w1] = {}
                        allhyps[w1][w2] = n
    return allhyps

"""
Do it for all words, all tags. Sounds expensive, but it isn't.
"""
def getTaggedHyps():
    allsynsets = [ss for ss in wordnet.all_synsets()]
    alltags = {}
    for ss in allsynsets:
        alltags[ss.pos] = True
    taggedhyps = {}
    for tag in alltags:
        taggedhyps[tag] = getAllHyps(allsynsets, tag=tag)
    return taggedhyps

"""
Still, quicker to do it once, the first time the whole thing is loaded,
and then skip it on subsequent goes. Same trick as above.
"""

try:
    taggedhyps
    print "taggedhyps already loaded"
except:
    try:
        taggedhyps = load("taggedhyps.pck")
        print "taggedhyps loaded from taggedhyps.pck"
    except:
        print "creating the hypernym table"
        taggedhyps = getTaggedHyps()
        print "OK -- saving it for next time"
        dump(taggedhyps, "taggedhyps.pck")

"""
You can exchange two words at no cost if the first is a subset of the second
"""
def scoreXCH(w1, w2, taggedhyps=taggedhyps):
    w1, t1 = w1[0], w1[1][0].lower()
    w1 = getRoot(w1, t1)
    w2, t2 = w2[0], w2[1][0].lower()
    w2 = getRoot(w2, t2)
    try:
        if t1 == t2 and (w1 == w2 or w2 in taggedhyps[t1][w1]):
            return 0
    except:
        pass
    return 3

def deleteAdjs(w1, w2):
    if w1[1] == "JJ":
        return 0
    else:
        return 2
"""
Do alignment allowing deletion of words from the premise and exchange if
the word in the premise is a subset of the word in the conclusion.

Have to make the cost of insert 4 to ensure that simple exchange is cheaper
than insert followed by delete, since delete is now worth 0
"""

def teAlignment(s1, s2, tagger, hyps=taggedhyps, DELETE=lambda x:0, INSERT=lambda x:4, EXCHANGE=scoreXCH):
    s1 = tagger.tag(s1)
    s2 = tagger.tag(s2)
    a = dtw.array(s1, s2, DELETE=DELETE, INSERT=INSERT, EXCHANGE=EXCHANGE)
    return a.findPath(), a
    
    
