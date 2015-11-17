#!/usr/bin/python

import re
import string
import os
import shutil
import stat
import sys
import subprocess
import time
import cPickle
import useful

try:
    from nltk.corpus import wordnet
except:
    """
    Some machines where I want to run this don't have the NLTK installed: I'm
    only using it in order to get at morphy, so it's not a disaster if it's not
    there
    """
from useful import *

try:
    mxl = cPickle.load(open("mxl.pck"))
except:
    pass

""" Set BNC to point to the right place on different machines """
if sys.platform == "darwin":
    BNC = '/Users/ramsay/BNC/'
else:
    BNC = '/opt/info/courses/COMP34411/PROGRAMS/BNC/'
A00 = "%s/A/A0/A00.xml"%(BNC)

def toBNCFormat(text):
    s = ""
    for form, tag in mxl.tag(text):
        s = s+"%s!!%s\n"%(tag, form)
    return s

subjpro = re.compile("PNP!!(?P<form>(he|she|we|I|they)\n)")
def fixSubjPronouns(s):
    return subjpro.sub("SUB!!\g<form>", s)

"""
A sample grammar

Terminals must be complete tag descriptions: you can't merge, for
instance, merge the three verbs "VB.", "VD.", "VH." into a single tag
"". If you do, everyting will fall over. I suspect that the regex
compiler probably spots this and merges them behind the scenes anyway.

Non-terminals must be mixture of lower-case characters and digits.

Specific words are marked by putting double quotes round them (I use
the words "to" and "that" rather than their BNC counterparts, for
instance, because I think the BNC often gets them wrong: it's better
to ask for the word "to" rather than specifying that you want a
preposition or the infinitive marker, because the word "to" will
always be correctly given the surface form "to", whereas it might be
given the wrong tag).
"""

defns = {'noun':'NN.',
         'adj1':'AJ.',
         'det0':'(AT.|DT.)!!(?!that)[a-z]*',
         'card':'CRD',
         'possmarker':'POS',
         'pron':'PNP',
         'conj':'CJC',
         'prep':'PR.',
         'adv':'AV.',
         'xx':'XX.',
         'aux':'(?:VB.)|(?:VD.)|(?:VH.)',
         'verb':'VV.',
         # Active verbs for greater precision when finding VPs
         'gverb':'(VB. VVG)',
         'dverb':'(VH. VV(N|D))',
         'zverb':'(VVZ|VVI)',
         'averb':'(gverb|dverb|zverb)',
         
         'to':'"to"',
         'that':'"that"',
         'dot':'PUN!!\\.',

         'title':'("Mr"|"Mrs")',
         'name': 'title NP.',

         'adj':'(?:adj1|NN1)*',
         'poss':'((?:(?:det0 adj noun) | NP. | PNP) possmarker)',
         'det':'(?:poss | det0)',
         'basenp':'det0 adj noun',
         'np':'(basenp | NP. | PNP)',
         'subjnp': '(basenp | NP. | SUB)',
         'pp':'prep np',

         'auxseq':'(?:aux* (?:adv | xx))*',
         'verbseq':'(CV:(aux|verb))',

         'tovp':'to verbseq ',
         'thatcomp': '(that np| SUB) verbseq np',
         'npthatcomp': 'np (that np| SUB) verbseq np',
         'npinfcomp': 'np VVI np',
         'npprespartcomp': 'np VVG np',
         'prespartcomp': 'VVG np',
         
         'justverbandobj': '(MV:averb) det? adj (OBJ:noun)',

         'verbobj': 'subjnp  (MV:averb) det? adj (OBJ:noun)',
         'verbthatcomp': 'subjnp  (MV:averb) thatcomp',
         'verbnpthatcomp': 'subjnp  (MV:averb) npthatcomp',
         'verbnpinfcomp': 'subjnp  (MV:averb) npinfcomp',
         'verbtocomp': 'subjnp  (MV:averb) tovp',
         'verbnptocomp': 'subjnp  (MV:averb) np tovp',
         'verbprespartcomp': 'subjnp  (MV:averb) prespartcomp',
         'verbnpprespartcomp': 'subjnp  (MV:averb) npprespartcomp',
         'verbditrans': 'subjnp  (MV:averb) np np',
         'verbtrans': 'subjnp  (MV:averb) np dot',
         'verbintrans': 'subjnp  (MV:averb) pp',
         'sentence':'(?:aux)? np verbseq (tovp | thatcomp | np)'}

"""
Make up a tag. If properTags is true then make something that will
match items in BNC format, if it's false then just return the tag
itself. The latter is useful for debugging and exposition.

Set lowerCaseOnly to True to ignore names (useful because otherwise it's
difficult to force "Mr Jones" and "Allan Ramsay" to be a single NP, and if
you let them be multiple single word NPs you get things you may not want)
"""

def tag(tag, properTags=True, lowerCaseOnly=True):
    if properTags:
        if lowerCaseOnly:
            return r'(?:%s!![a-z|\.]*)\n'%(tag)
        else:
            return r'(?:%s!!.*)\n'%(tag)
    else:
        return tag

"""
Likewise, but for words
"""
    
def makeWord(word, properTags=True):
    if properTags:
        return "([^\n]*!!%s)\n"%(word.replace('"', ''))
    else:
        return word

"""
Horrible regex for picking out bits of a pattern to be replaced by tags
"""
tpattern = re.compile("""(?P<word>("([A-Za-z]|\d|\.)+"))|((?P<label>([A-Z]|\d)+):)|(?P<tag>(([a-z]|\d)+))|(?P<ltag>.*)!!(?P<lform>.*)|(?P<pos>([A-Z]|\d|\.|\(.*\)){3})""")

"""
This is used as the function in a replacement based on matches of
tpattern.

m is a match of tpattern against some element of the term that we are
translating, defns is the set of rules. It's all quite
straightforward--each branch of tpattern has a named group, so knowing
which group is non-null tells us what kind of match it was, and that
lets us work out what to do.
"""

def replaceTag(m, defns, properTags=True):
    l = m.group('ltag')
    if l:
        return "%s!!%s\\n"%(l, m.group('lform'))
    l = m.group('label')
    if l:
        return '?P<%s>'%(l)
    t = m.group('tag')
    if t:
        return readRE(defns[t], defns, properTags)
    w = m.group('word')
    if w:
        if properTags:
            return makeWord(w)
        else:
            return w
    p = m.group('pos')
    if p:
        if properTags:
            return tag(p)
        else:
            return p
    raise Exception(m)

"""
Turn an entry in defns into a regex that can be used for parsing BNC-format text.
"""
        
def readRE(s, defns=defns, properTags=True):
    return tpattern.sub((lambda m: replaceTag(m, defns, properTags)), s).replace(" ", "")

"""
readAllFiles gets

    a path (might be directory, might be a file)
    a pattern
    a function saying what to do with each match

and calls readFile with every file in the directory (if the path is a
directory) or with the file (if it's just one file), the pattern and
the function
"""

def printTags(a, b, c, d):
    print "****"
    for g in c.groupindex:
        print g, b.group(g)

def readAllFiles(path, pattern, function):
    startTime = time.time()
    n = 0
    if pattern.__class__.__name__ == "list":
        pattern = [(p, re.compile(readRE(p), re.DOTALL)) for p in pattern]
    else:
        pattern = re.compile(readRE(pattern), re.DOTALL)
        print pattern.pattern
    if os.path.isdir(path):
        for path, dirs, files in os.walk(path):
            for filename in files:
                if pattern.__class__.__name__ == "list":
                    for p in pattern:
                        readFile(path+"/"+filename, p, function)
                else:
                    readFile(path+"/"+filename, pattern, function)
                n = n+len(open(path+"/"+filename).readlines())
                print n, n/(time.time()-startTime)
    else:
        readFile(path, pattern, function)
    print "Time taken: %.2f"%(time.time()-startTime)

"""
Used for splitting BNC files into sentences
"""
sentenceSep = re.compile("<p>")
idPattern = re.compile('<a name="(?P<name>.*?)">', re.DOTALL)

def readFile(ifile, pattern, function, fixSubjPronouns=fixSubjPronouns):
    print ifile
    if useful.type(pattern) == "tuple":
        (original, pattern) = pattern
    else:
        original = False
    groups = pattern.groupindex
    for s in sentenceSep.split(fixSubjPronouns(open(ifile, 'r').read().replace("'", ""))):
        """
        Find everything that matches the pattern in this file, do something with it
        """
        for i in pattern.finditer(s):
            function(s, i, original, pattern, ifile)

"""
We're trying to find a pairwise relation between the two items
(e.g. trying to find all verb-object pairs), so store them, both ways
round, in the dictionary.

   {'affect': {'OBJ': {'system': 1}},
    'system': {'MV': {'affect': 1}}}
"""

def root(word):
    for t in ['a', 'v', 'n']:
        r = wordnet.morphy(word, t)
        if r and not r == word:
            return r
    return word

def saveDepRel(s, i, pattern, dict):
    [w1, w2] = [[g, root(getWord(i.group(g), g).split(" ")[-1])] for g in pattern.groupindex]
    incTableN(w1[1:]+w2, dict)
    incTableN(w2[1:]+w1, dict)
    
def getDepRels(path, pattern):
    dict = {}
    readAllFiles(path, pattern, (lambda s, i, original, pattern, ifile: saveDepRel(s, i, pattern, dict)))
    return dict

def saveDepRelWithFile(s, i, pattern, ifile, dict):
    [w1, w2] = [[g, getWord(i.group(g), g)] for g in pattern.groupindex]
    n = idPattern.match(s)
    n = n.group('name')
    incTableN(w1[1:]+w2+[ifile, n], dict)
    incTableN(w2[1:]+w1+[ifile, n], dict)
    
def getDepRelsWithFiles(path, pattern):
    dict = {}
    readAllFiles(path, pattern, (lambda s, i, original, pattern, ifile: saveDepRelWithFile(s, i, pattern, ifile, dict)))
    return dict

def getSentence(ifile, offsets):
    text = ""
    print ifile
    ifile = open(ifile).read()
    for offset in offsets:
        print offset
        for i in (re.compile('<a name="%s">(?P<s>.*?)(<a name|$)'%(offset), re.DOTALL)).finditer(ifile):
            text = text+i.group('s').replace("\n", " ")
    return text

def getSentences(w1, r1, w2=False, dict=dict):
    sentences = {}
    for x1 in dict[w1][r1]:
        if not(w2) or w2 == x1:
            sentences[x1] = []
            for s in dict[w1][r1][x1]:
                s = getSentence(s, dict[w1][r1][x1][s])
                sentences[x1].append(s)
    return sentences

def saveTable(d, r1, path):
    try:
        shutil.rmtree(path)
    except:
        """ Didn't exist anyway """
    os.mkdir(path)
    az = re.compile("^[a-z]+$")
    for x in d:
        if r1 in d[x] and az.match(x):
            print x
            out = open("%s/%s"%(path, x), 'w')
            out.write("%s"%(d[x][r1]))
            out.close()
    
                    
wordPattern = re.compile("(?P<tag>.*)!!(?P<form>.*)")
def saveParses(s, i, pattern, parses):
    parses.append([wordPattern.sub((lambda g: g.group("form")), s).replace("\n", " "), plantBrackets(i, pattern.groups)])

def getParses(path, pattern):
    parses = []
    readAllFiles(path, pattern, (lambda s, i, pattern, ifile: saveParses(s, i, pattern, parses)))
    return parses

def stem(x, g):
    x = x.lower()
    if 'V' in g:
        g = 'v'
    else:
        g = 'n'
    try:
        s = wordnet.morphy(x, g)
        if s:
            return s
    except:
        " wordnet was't loaded--only option is to return the original "
    return x

def getWord(s, g):
    txt = ""
    for x in s.strip().split("\n"):
        txt = txt+"%s "%(stem(x.split("!!")[1].strip(), g))
    return txt[:-1]
    
def plantBrackets(i, groups):
    chunks = [i.group(chunk) for chunk in range(0, groups+1)]
    chunks = noCopies([re.compile('...!!').sub("", chunk.replace("\n", " "))[:-1] for chunk in chunks if chunk])
    x = chunks[0]
    for y in chunks[1:]:
        if len(y.split(" ")) > 1:
            x = x.replace(y, "[%s]"%y)
    return "[%s]"%(x)

idpattern = re.compile("""(?P<id><a name="\d*">)""")

"""
>>> frames = bnc.getFrames(bnc.BNC+"/A/A0", bnc.ALLFRAMES)
"""
 
ALLFRAMES = ['verbthatcomp',
             'verbnpthatcomp',
             'verbtocomp',
             'verbnptocomp',
             'verbnpinfcomp',
             'verbditrans',
             'verbintrans',
             'verbtrans',
             'verbprespartcomp',
             'verbnpprespartcomp']

def getFrames(d, patterns=ALLFRAMES, table=False):
    if table == False:
        table = {}
    
    def add2table(s, i, original, pattern, ifile):
        v = stem(i.group("MV").strip().split("!!")[-1], 'V')
        if not v in table:
            table[v] = {}
        tablev = table[v]
        if not original in tablev:
            tablev[original] = []
        useful.incTable('TOTAL', tablev)
        tablev[original].append((idpattern.search(s).group("id"), ifile))
            
    readAllFiles(d, patterns, add2table)
    return table

wordpattern = re.compile(".*!!(?P<word>.*)")
def getSentenceFromFile(id, ifile):
    s = open(ifile).read().split(id)[1]
    return wordpattern.sub("\g<word> ", s.split("<a name")[0]).replace("\n", "")

def saveFrames(frames):
    for word in frames:
        print "%s %s"%(word, frames[word])
    print "Save frames?"
    if sys.stdin.readline()[0] == "y":
        print "Saving FRAMES (still available as bnc.FRAMES)"
        out = open('frames.pck', 'w')
        cPickle.dump(frames, out)
        out.close()
    else:
        print "Not saving FRAMES (still available as bnc.FRAMES)"
        
"""
bnc.checkFrames(frames) shows you each frame in turn: if you say "y" then this one gets added to the overall set,
"n" says don't save it, 7 says show me 7 more examples, q or CR says quit.
at the end you can save them in 'frames.pck'.
"""
def checkFrames(table, allframes=ALLFRAMES, out=sys.stdout):
    global FRAMES
    if not out == sys.stdout:
        out = open(out, 'w')
    try:
        FRAMES = cPickle.load(open('frames.pck'))
    except:
        FRAMES = {}
    for word in FRAMES:
        try:
            del table[word]
        except:
            pass
    l = []
    for word in table:
        l.append((table[word]['TOTAL'], word))
    l.sort()
    l.reverse()
    for (n, word) in l:
        FRAMES[word] = {}
        total = table[word]['TOTAL']
        for frame in table[word]:
            if frame == "TOTAL":
                continue
            s = """
/**
%s %s (%s/%s)"""%(word, frame, len(table[word][frame]), total)
            i = 0
            printed = 0
            examples = table[word][frame]
            while printed < 12 and i < len(examples):
                (id, ifile) = examples[i]
                i += 1
                words = []
                sentence = getSentenceFromFile(id, ifile)
                for x in sentence.split(" "):
                    if wordnet.morphy(x.lower(), 'v') == word:
                        words += ['***', x, '***']
                        theword = x
                    else:
                        words.append(x)
                w = '\n\n'
                for x in words:
                    w += '%s '%(x)
                try:
                    w = limit(w, theword, 60)
                except Exception as e:
                    """
                    Get to here if the word wasn't found as a verb by morphy, which is either
                    because it's not a proper word or it's not a verb. In either case we should skip
                    """
                    continue
                s += "\n%s\n"%(w.strip())
                printed += 1
            r = float(len(table[word][frame]))/float(total)
            if r < 0.001:
                continue
            if printed == 0:
                print "No examples found for %s"%(word)
                continue
            if r < 0.05:
                 alarm = "!!!!!!!!!!!!!!"
            else:
                 alarm = ""
            s += """
%s %s (%s/%s) %s
**/
"""%(word, frame, len(table[word][frame]), total, alarm)
            if out == sys.stdout:
                os.system('clear')
                print s
                OK = sys.stdin.readline().strip()
                if OK == "q":
                    saveFrames(FRAMES)
                    return
                if not frame in FRAMES[word]:
                    FRAMES[word][frame] = {}
                try:
                    FRAMES[word][frame][allframes[int(OK)]] = len(examples)
                except:
                     if OK == "other":
                        FRAMES[word][frame]["other"] = True
            else:
                incTableN([word, frame], FRAMES, n=len(examples))
                out.write("""
%s
lexEntry(%s, X) :-
    X <> [vroot, %s].
"""%(s, word, frame))
    if out == sys.stdout:
        saveFrames(FRAMES)
    else:
        out.close()

def pairtags(t1, t2, frames):
    pairs = []
    for word in frames:
        if t1 in frames[word] and not t2 in frames[word]:
            pairs.append((len(frames[word][t1]), word, t1, t2))
    pairs.sort()
    return pairs

def limit(s, w, n=50):
    try:
        s = s.split(w)
        if len(s[0]) > n:
            w = "... %s %s"%(s[0][-n:], w)
        else:
            w = "%s %s"%(s[0], w)
        if len(s[1]) > n:
            w = "%s %s ..."%(w, s[1][:n])
        else:
            w = "%s %s"%(w, s[1])
        return w
    except Exception as e:
        raise e
