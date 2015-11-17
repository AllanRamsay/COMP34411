"""
TAG.PY: collection of tagging algorithms. mxltagger is a version of the one we developed for Arabic.

Programs to support COMP34411 Natural Language Systems: these programs
have more comments in them than code that I write for my own use, but
it's unlikely to be enough to make them easy to understand. If you
play with them then I hope they will help with understanding the ideas
and algorithms in the course. If you try to read the source code,
you'll probably just learn what a sloppy programmer I am.
"""

import re
import copy
from useful import *
import os

try:
    from nltk.tag import brill as nltkbrill
    from nltk.corpus import wordnet
except:
    print "WORDNET NOT AVAILABLE ON THIS MACHINE"

import sys
import cPickle
import math

METERING = False

def tag(tagger, text, default='NN1', getAll=False):
    if text.__class__.__name__ == "str":
        text = text.split(" ")
    tags0 = []
    """
    Start by getting initial estimates from the dictionary
    """
    for word in text:
        found = False
        if word in tagger.dict:
            tags0.append(tagger.dict[word])
            found = True
        else:
            for affix in ['n', 'v', 'a']:
                root = getroot(word, affix)
                if root and not word == root and '!%s!'%(root) in tagger.dict:
                    tags0.append(tagger.dict['!%s!'%(root)])
                    found = True
                    break
        if not found:
            if len(word) > 3 and "-%s"%(word[:3]) in tagger.dict:
                tags0.append(tagger.dict["-%s"%(word[:3])])
            else:
                tags0.append({default:1.0})
    tags0 = tags0+[{'YYY':1.0}]
    lastTag = {'XXX':1.0}
    tags1 = []
    """
    Now collect the transition likelihoods for each of the tags that
    were suggested by the dictionary
    """
    for i in range(len(tags0)-1):
        d = {}
        transitions = {}
        t = tags0[i]
        nextTag = tags0[i+1]
        for k in t:
            s = t[k]
            transitions[k] = 0
            for lt in lastTag:
                if lt in tagger.ftransitions and k in tagger.ftransitions[lt]:
                    transitions[k] = transitions[k]+0.25*tagger.ftransitions[lt][k]
            for nt in nextTag:
                if nt in tagger.btransitions and k in tagger.btransitions[nt]:
                    transitions[k] = transitions[k]+tagger.btransitions[nt][k]
            """
            Use sqrt as a way of downgrading the significance
            of the dictionary. No good reason except that it works.
            """
            d[k] = math.sqrt(s)
        lastTag = t
        normalise(d)
        try:
            normalise(transitions)
            for x in d:
                d[x] = d[x]*transitions[x]
            normalise(d)
        except:
            """
            It can happen that there are no transitions between this tag
            the next/previous one (if, for instance, you were to
            end the sentence with something that has never been seen at
            the end of a sentence). Under those circumstances the best you
            can do is to rely on the dictionary
            """
        tags1.append(d)
    if getAll:
        return [(form, tag) for form, tag in zip(text, tags1)] 
    else:
        return [(text[i], getBest(tags1[i])[0]) for i in range(0, len(text))]

try:
    getroot = wordnet.morphy
except:
    getroot = lambda x, y: x

"""
Set BNC to point to the copy of the BNC on the machine where the
program is being run. My Mac seems to have two names, depending on
whether it's connected to the internet
"""

if usingMac():
    BNC = '/Users/ramsay/BNC'
else:
    BNC = '/opt/info/courses/COMP34411/PROGRAMS/BNC'

"""
I'm very lazily storing word:tag pairs as either two elements lists or two element
tuples, rather than specifying a class. This is a very feeble attempt at doing things
correctly by specifying constants as the offsets into these items
"""
WORD = 0
TAG = 1

"""
For reading words from in my simple format and splitting them into the
tag and the word
"""
simpleTagPattern = re.compile('(?P<tag>.*)!!(?P<form>.*)')

"""
Read every file in the specified path and do something to it
"""
def readCorpus(path, task):
    if os.path.isdir(path):
        for path, dirs, files in os.walk(path):
            for filename in files:
                print path+"/"+filename
                d = readFile(path+"/"+filename, task)
    else:
        d = readFile(path, task)
    return d

"""
Read the specified file, split it into a list of form:tag pairs and do
'task' to each pair
"""
def readFile(file, task):
    # print file
    s = open(file, 'r').read()
    for m in simpleTagPattern.finditer(s):
        task(m.group('form').strip(), m.group('tag'))    

"""
Use readCorpus/readFile to get the words in the corpus as one great
big list
"""
def getTestSet(path):
    t = []
    readCorpus(path, (lambda word, tag: t.append((word, tag))))
    return t

"""
Run the tagger on the testset, return precision, recall, f, confusion matrix

The tagger will have been trained to either leave ambiguous tags alone or to
pick the first choice. When we're testing we have to follow the same regime,
so we ask the tagger for its value of splitAmbiguousTags when preparing
the test data.
"""
def testTagger(testset, tagger, showTest=False):
    if type(testset[0]) == "WORD":
        testset = [(w.form, w.tag) for w in testset]
    l = tagger.tag([x[0] for x in testset])
    b = []
    right = 0.0
    tried = 0.0
    total = 0.0
    confusion = {}
    for i in range(0, len(l)):
        tag0 = testset[i][TAG]
        """
        The tagger will have been trained to either leave
        ambiguous tags alone or to pick the first choice. When we're testing
        we have to follow the same regime, so we ask the tagger for its value
        of splitAmbiguousTags when preparing the test data (and below).
        """
        if tagger.splitAmbiguousTags:
            tag0 = tag0.split("-")[0]
        word = testset[i][WORD]
        if not (word  == '' or ' ' in word):
            total = total+1
            if l[i][TAG]:
                tried = tried+1
                tag1 = l[i][TAG]
                if tagger.splitAmbiguousTags:
                    tag1 = tag1.split("-")[0]
                b.append((word, tag0, tag1))
                incTable2(tag0, tag1, confusion)
                if tag1 == tag0:
                    if showTest: print testset[i]
                    right = right+1
                else:
                    if showTest: print '****', testset[i], tag1
            else:
                if showTest: print '????', testset[i]
                b.append((word, tag0, 'UNK'))
                incTable2(tag0, 'UNK', confusion)
    if tried == 0.0:
        tried = 1.0
    p = right/tried
    r = right/total
    return p, r, (2*p*r)/(p+r), confusion

"""
showConfusion just lays out the confusion matrix reasonably neatly.
If latex is set to True, then the output is appropriate latex source
code.
"""
def showConfusion(c, latex=True, n=1000):
    tags = []
    for t1 in c:
        if not t1 in tags:
            tags.append(t1)
        for t2 in c[t1]:
            if not t2 in tags:
                tags.append(t2)
    for t1 in tags:
        if not t1 in c:
            c[t1] = {}
        if not t1 in c[t1]:
            c[t1][t1] = 0
    tags = [(c[t1][t1], t1) for t1 in tags]
    tags.sort()
    tags.reverse()
    tags = [tag1[1] for tag1 in tags][:n]
    if 'UNK' in tags:
        tags.remove('UNK')
        tags = ['UNK']+tags
    if latex:
        s = r'\begin{tabular}{|c'+('|c'*len(tags))+'|}\n\\hline\n'
        for t1 in tags:
            s = s+'&%s'%(t1)
        s = s+'\\\\\n\\hline\n'
        for t1 in tags:
            s = s+t1
            if c[t1]:
                r = c[t1]
                for t2 in tags:
                    if t2 in r and r[t2] > 0:
                        s = s+'&%s'%(r[t2])
                    else:
                        s = s+'&'
                s += "\\\\\n"
            else:
                s = s+('&'*len(tags))
                s = s+'\\\\\n\\hline\n'
        s = s+'\\end{tabular}\n'
    else:
        s = ""
        for t1 in tags:
            s = s+"%s\t%s\n"%(t1, sortTable(c[t1]))
    return s

"""
This is useful if we're using the Prolog implementation of Brill retagging.

But at present I'm not using that in COMP34411 (I do think it's neater, and
it's easier to extend the set of templates, but I'm trying to stick to Python
for COMP34411)
"""
def brillFormat(l, out=sys.stdout):
    if not out == sys.stdout:
        out = open(out, 'w')
    s = """
:- abolish([wd/2, tag/2, tag/3, sf/2, pf/2]).
:- dynamic wd/2, tag/2, tag/3, sf/2, pf/2.

"""
    for i in range(0, len(l)):
        x = l[i]
        s = s+"""
wd(%s, '%s').
tag(%s, '%s').
tag('%s', '%s', %s).
"""%(i, x[0], i, x[2], x[2], x[1], i)
    out.write(s)
    if not out == sys.stdout:
        out.close()

"""
Several of the taggers require a dictionary extracted from the corpus.

The basic idea is pretty simple--just read the words and stick them in a hash
table. There are some fiddly bits about things that aren't well-formed words,
but overall it's pretty straightforward.

If splitAmbiguousTags is true then we take the first part of the tag to be the bit
we want, so 'NN1-VVI' becomes 'NN1'. 
"""
        
class corpusdict:


    """
    Local exception class, used for breaking the loop in readCorpus when we've
    got as many words as we want.
    """
    class DictFull(Exception):
        def __init__(self):
            """Nothing to do"""

        def __str__(self):
            return "DictFull"

    def __init__(self, path, maxlength=0, n=None, t=None, splitAmbiguousTags=False):
        self.basedict = {}
        self.alltags = {}
        self.maxlength = maxlength
        self.splitAmbiguousTags = splitAmbiguousTags
        if path.__class__.__name__ == "list":
            for word, tag in path:
                self.addWord(word, tag, splitAmbiguousTags=splitAmbiguousTags)
        else:
            try:
                readCorpus(path, (lambda word, tag: self.addWord(word, tag, splitAmbiguousTags=splitAmbiguousTags)))
            except self.DictFull:
                """Limit reached"""
        self.removeCopies()
        self.prune(n, t)
        self.alltags = normalise(self.alltags)
      
    def addWord(self, word, tag, splitAmbiguousTags=False):
        d = self.basedict
        if splitAmbiguousTags:
            tag = tag.split("-")[0]
        incTable(tag, self.alltags)
        if not word == '' and not (' ' in word or '\n' in word):
            incTable2(word, tag, d)
            self.maxlength = self.maxlength-1
            if self.maxlength == 0:
                raise DictFull()

    def occurrences(self, x, d):
        n = 0
        for y in d[x]:
            n = n+d[x][y]
        return n
    
    def closed(self, x, d):
        for t in d[x]:
            if not t[:2] in ['NN', 'VV', 'AJ', 'NP']:
                return True
        return False

    def merge(self, d1, d2):
        for k in d2:
            if k in d1:
                d1[k] = d1[k]+d2[k]
            else:
                d1[k] = d2[k]
        return d1
            
    def removeCopies(self):
        d = self.basedict
        for x in d.keys():
            y = x.lower()
            if not x == y:
                if y in d:
                    d[y] = self.merge(d[y], d[x])
                    del d[x]
                    
    def prune(self, n=None, threshold=None):
        d0 = self.basedict
        if n == None and threshold == None:
            self.dict = d0
            return
        if n == None:
            n = len(d0)
        openList = []
        closedList = []
        d1 = {}
        for x in d0:
            if self.closed(x, d0):
                closedList.append(x)
            else:
                openList.append(x)
        l = [(self.occurrences(x, d0), x) for x in openList]
        l.sort()
        l.reverse()
        i = 0
        for x in l[:n]:
            d1[x[1]] = d0[x[1]]
        for x in closedList:
            if not(threshold == None) and len(d0[x]) <= threshold:
                d1[x] = d0[x]
        self.dict = d1

"""
The taggers: in line with standard NLTK practice, a tagger is something
that has a definition of tag, where tag takes either a string (which it
promptly converts to a list ofr words) or a list of words and returns
a list of (word, tag) pairs.
"""

"""
default tagger: return NN1 for everything
"""
class defaulttagger:

    def __init__(self, tagdict = {'NN1':1.0}):
        if type(tagdict) == 'corpusdict':
            tagdict = tagdict.alltags
            self.splitAmbiguousTags = tagdict.splitAmbiguousTags
        else:
            self.splitAmbiguousTags = False
        self.tagdict = tagdict

    def tag(self, l, choices=False):
        if islist(l):
            return [self.tag(x, choices) for x in l]
        else:
            if choices:
                return (l, self.tagdict)
            else:
                return (l, getBest(self.tagdict))

"""
Collect the SUFFIXLENGTH prefixes and suffixes from a dictionary,
use those for tagging. Only makes sense as a backoff for a
dictionary based tagger.
"""
class affixtagger:
    
    def __init__(self, words, SUFFIXLENGTH=3):
        self.dict = {}
        self.SUFFIXLENGTH = SUFFIXLENGTH
        if type(words) == 'corpusdict':
            self.splitAmbiguousTags = words.splitAmbiguousTags
            words = words.basedict
        else:
            self.splitAmbiguousTags = False
        for x in words:
            if len(x) > self.SUFFIXLENGTH:
                s = x[-self.SUFFIXLENGTH:]
                if not s in self.dict:
                    self.dict[s] = {}
                d = self.dict[s]
                for t in words[x]:
                    if not t in self.dict[s]:
                        self.dict[s][t] = words[x][t]
                    else:
                        self.dict[s][t] = self.dict[s][t]+words[x][t]

    def tagWord(self, word):
        if len(word) > self.SUFFIXLENGTH:
            word = word[-self.SUFFIXLENGTH:]
            if word in self.dict:
                return self.dict[word]
        return False

    def tag(self, l, choices=False):
        if islist(l):
            return [self.tag(x, choices) for x in l]
        else:
            if ' ' in l:
                return self.tag(l.split(' '), choices)
            if choices:
                return (l, self.tagWord(l))
            else:
                return (l, getBest(self.tagWord(l)))
"""
dicionary-based tagger: pretty simple-minded. Use the commonest
tag for the given form in the dictionary!
"""
class dicttagger:

    def __init__(self, dict):
        if type(dict) == 'corpusdict':
            self.splitAmbiguousTags = dict.splitAmbiguousTags
            dict = dict.dict
        else:
            self.splitAmbiguousTags = False
        self.dict = dict

    def tag(self, l, choices=False):
        if islist(l):
            return [self.tag(x, choices) for x in l]
        else:
            l = l.strip()
            if ' ' in l:
                return self.tag(l.split(' '), choices)
            if choices:
                choose = (lambda x: x)
            else:
                choose = getBest
            if l in self.dict:
                return (l, choose(self.dict[l]))
            elif l.lower() in self.dict:
                return (l, choose(self.dict[l.lower()]))
            else:
                return (l, False)

"""
This one's a bit more complicated. But it's also quite a bit more
accurate, so it's worth including.

We add statistics about how likely one tag is to be followed or
preceded by another (these are not the same thing turned round: the
likelihood that a determiner is followed by a noun is not the same as
the likelihood that a noun is preceded by a determiner).

Imagine that we have three words, W1, W2, W3, where each of these has
(to keep things simple) two possible tags, T11, T12, T21, T22, T31,
T32

We're interested in W2: it must have one of the tags T21 and T22, and
it must be preceded by either T11 or T12 and followed by either T31 or
T31. The likelihood that T21 is preceded by either T11 or T12 is
p(T11->T21)+p(T12->T21), and the likelihood that T22 is preced by
either T11 or T12 is p(T11->T22)+p(T12->T22), where p(Ti -> Tj) is the
probability of Ti being followed by Tj. So we can estimate how likely
T21 and T22 each are on the basis of the preceding context.

Exactly analogous arguments let us estimate how likely T21 and T22 are
on the basis of the following context. So we now have three ways of
estimating the likelihood of each tag--preceding context, dictionary
and following context. The obvious way of combining them is by
multiplying them, but it would be nice to be able to goive them
different weights in the calculation. In particular, it turns out that
the dictionary-based element has a disproportionate effect. You can't
weight the elements in a product by multiplying them by a constant; so
what I do is take the square root of the contribution from the
dictionary. The consequence of this is to even out the differences
between different frequencies, which seems to work out quite
nicely. There are probably better ways of doing it (and even if there
aren't, there are probably powers that would work better--there's no
obvious reason why PC*(DICT^0.5)*FC should be better than, say
(PC^0.9)*(DICT^0.43)*FC. There's an experiment to be done here, but I
haven't done it. PC*(DICT^0.5) works quite well, and that will do me
for now.

This is an alternative to using HMMs. Works better for me than HMMs, which is
why I'm including it rather than an HMM-based one.
"""

class mxltagger:

    sentenceSplitter = re.compile('<p><a name="\d*">')
    
    def __init__(self, corpus=BNC, subcorpus="", ftransitions = {}, btransitions = {}, trainingsize=-1, splitAmbiguousTags=True, tagsize=1000, preprocess=(lambda x, y: (x, y))):
        if not subcorpus == "":
            if not subcorpus[0] == "/":
                subcorpus = "/%s"%(subcorpus)
            corpus += subcorpus
        if METERING:
            if isstring(corpus):
                print "Making mxltagger from %s"%(corpus)
            else:
                print "Making mxltagger from %s pretagged items"%(len(corpus))
        dict = {}
        self.dict = dict
        self.ftransitions = ftransitions
        self.btransitions = btransitions
        self.splitAmbiguousTags = splitAmbiguousTags
        self.tagsize = tagsize
        self.tagset = {}

        """ftransitions
        Build the dictionary and the transition tables. The use of affix tables is built-in,
        so the dictionary contribution is the same as using a standard dictionary-based tagger
        with back-off to affix tables.

        We have to build the transition table on a per-sentence basis, rather than just word-by-word
        through the file, because we need some notion of transitions to the first word of a sentence
        and from the last word. So I add a couple of dummy words, with affixes 'XXX' and 'YYY', to
        be 'the word before/after the start/end of the sentence'
        """
        trigrams = {}
        if corpus.__class__.__name__ == "str":
            for path, dirs, files in os.walk(corpus):
                for f in files:
                    if f[-4:] == ".xml":
                        if METERING:
                            print f
                        for s in self.sentenceSplitter.split(open("%s/%s"%(path, f), 'r').read()):
                            lastTag = False
                            taggedItems = [i for i in simpleTagPattern.finditer("XXX!!beforeSentence\n"+s+"YYY!!afterSentence")]
                            ti = taggedItems[1]
                            (form, tag) = preprocess(ti.group("form").lower(), ti.group("tag"))
                            tag = tag[:self.tagsize]
                            for i in range(1, len(taggedItems)-1):
                                incTable(tag, self.tagset)
                                if not form == "":
                                    ti1 = taggedItems[i+1]
                                    (form1, tag1) = preprocess(ti1.group("form").lower(), ti1.group("tag"))
                                    nextTag = tag1[:self.tagsize]
                                    incTableN([form, tag, lastTag, nextTag], trigrams)
                                lastTag = tag
                                form, tag = form1, tag1
        else:
            lastTag = "SS"
            for word in corpus:
                word.tag = word.tag[:self.tagsize]
                incTable(word.tag, self.tagset)
            N = len(corpus)-1
            for i in range(N):
                word = corpus[i]
                tag = word.tag
                nextTag = corpus[i+1].tag
                incTableN([word.form, tag, lastTag, nextTag], trigrams)
                lastTag = tag
                if METERING:
                    print "Collecting trigrams: %.2f %s %s"%(float(i)/float(N), i, N)
        N = 0
        for x in trigrams:
            for y in trigrams[x]:
                for z in trigrams[x][y]:
                        N += len(trigrams[x][y])
        k = 0
        for form in trigrams:
            for tag in trigrams[form]:
                for lastTag in trigrams[form][tag]:
                    for nextTag in trigrams[form][tag][lastTag]:
                        if METERING:
                            print "Processing trigrams: %.2f %s %s"%(float(k)/float(N), k, N)
                        k += 1
                        n = trigrams[form][tag][lastTag][nextTag]
                        incTableN([form, tag], self.dict, n=n)
                        try:
                            if len(form) > 3 and tag[0] in ['N', 'V', 'A']:
                                root = wordnet.morphy(form, tag[0].lower())
                            if not root == form:
                                incTableN(["!%s!"%(root), tag], self.dict, n=n)
                        except:
                            "This won't work if we didn't manage to load the NLTK"
                        incTableN(["%s-"%(form[:3]), tag], self.dict, n=n)
                        incTableN(["-%s"%(form[-3:]), tag], self.dict, n=n)
                        incTableN([lastTag, tag], self.ftransitions, n=n)
                        incTableN([tag, lastTag], self.btransitions, n=n)
            trainingsize = trainingsize-1
            if trainingsize == 0:
                break
        """
        normalise takes a hash table with numerical values and fixes it
        so that they add up to 1. normalise2 does this to every element of
        a hash table of hash tables.
        """
        normalise2(self.dict)
        normalise2(self.ftransitions)
        normalise2(self.btransitions)

    def getTagFromDict(self, word):
        return self.dict[word]

    def formInDict(self, root):
        return root in self.dict

    def default(self, word):
        if word.istitle():
            return {"NP":1}
        else:
            return {"NN":1}
        
    def initialtags(self, text):
        tags0 = []
        for word in text:
            found = False
            if self.formInDict(word):
                tags0.append(self.getTagFromDict(word))
                found = True
            else:
                for affix in ['n', 'v', 'a']:
                    root = getroot(word, affix)
                    if root and not word == root and self.formInDict('!%s!'%(root)):
                        tags0.append(self.getTagFromDict('!%s!'%(root)))
                        found = True
                        break
            if not found:
                if word.istitle():
                    tags0.append(self.default(word))
                elif len(word) > 3 and self.formInDict("-%s"%(word[:3])):
                    tags0.append(self.getTagFromDict("-%s"%(word[:3])))
                else:
                    tags0.append(self.default(word))
        tags0 = tags0+[{'YYY':1.0}]
        return tags0

    def setFromFtransitions(self, tag, k, transitions):
        if tag in self.ftransitions and k in self.ftransitions[tag]:
            transitions[k] += self.ftransitions[tag][k]

    def setFromBtransitions(self, tag, k, transitions):
        if tag in self.btransitions and k in self.btransitions[tag]:
            transitions[k] += self.btransitions[tag][k]
    
    def usetransitionprobs(self, text, tags0):
        lastTag = {'XXX':1.0}
        tags1 = []
        for i in range(0, len(tags0)-1):
            d = {}
            transitions = {}
            t = tags0[i]
            nextTag = tags0[i+1]
            for k in t:
                transitions[k] = 0
                for lt in lastTag:
                    self.setFromFtransitions(lt, k, transitions) 
                for nt in nextTag:
                    self.setFromBtransitions(nt, k, transitions)
                """
                Use sqrt as a way of downgrading the significance
                of the dictionary. No good reason except that it works.
                """
                s = float(t[k])
                d[k] = s**0.5
            lastTag = t
            normalise(d)
            try:
                normalise(transitions)
                for x in d:
                    d[x] = d[x]*transitions[x]
                normalise(d)
            except:
                """
                It can happen that there are no transitions between this tag
                the next/previous one (if, for instance, you were to
                end the sentence with something that has never been seen at
                the end of a sentence). Under those circumstances the best you
                can do is to rely on the dictionary
                """
            tags1.append(d)
        return tags1

    def tag(self, text, getAll=False):
        if text.__class__.__name__ == "str":
            text = text.split(" ")
        """
        Start by getting initial estimates from the dictionary
        """
        tags0 = self.initialtags(text)
        """
        Now collect the transition likelihoods for each of the tags that
        were suggested by the dictionary
        """
        tags1 = self.usetransitionprobs(text, tags0)
        if getAll:
            return [[form, tag] for form, tag in zip(text, tags1)] 
        else:
            return [[text[i], getBest(tags1[i])[0]] for i in range(0, len(text))]

    def showtransitions(self, transitions, n=100):
        for k in sorted(transitions.keys())[:n]:
            s = "%s: "%(k)
            for x, y in sortTable(transitions[k]):
                s += "%s %.2f, "%(x, y)
            print s

    def showftransitions(self, n=100):
        self.showtransitions(self.ftransitions)

    def showbtransitions(self, n=100):
        self.showtransitions(self.btransitions)

"""
Given a list of taggers, where the first one is better (higher
precision) than the second, and the second is better than the third,
..., make a single tagger which tries them each in order.
"""
class backofftagger:

    def __init__(self, taggers):
        self.main = taggers[0]
        if len(taggers[1:]) == 1:
            self.backoff = taggers[1]
        else:
            self.backoff = backofftagger(taggers[1:])
        self.splitAmbiguousTags = main.splitAmbiguousTags

    def tag(self, l, choices=False):
        if isstring(l):
            l = l.strip()
            if ' ' in l:
                return self.tag(l.split(' '), choices)
            t = self.main.tag(l, choices)
            if t[1]:
                return t
            else:
                return self.backoff.tag(l, choices)
        else:
            return [self.tag(x, choices) for x in l]
