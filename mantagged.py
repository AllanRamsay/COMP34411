import re, sys, os
from nltk.corpus import wordnet
from useful import *

def getSSFromLemma(l):
    return str(wordnet.lemma_from_key(l).synset().name())

mainpattern = re.compile(".*<keys>(?P<keys>.*)</keys>.*<def \S*>(?P<def>.*)</def>.*", re.DOTALL)

def getDisambiguatedTerms(defn):
    terms = []
    for t in dtermpattern.finditer(defn):
        try:
            terms.append(getSSFromLemma(t.group("sense")))
        except:
            pass
    return terms

skpattern = re.compile("""<sk>(?P<sk>\S*?)</sk>""")

def manLinks(ifiles=["adj.xml", "adv.xml", "noun.xml", "verb.xml"], N=0):
    defns = {}
    n = 0
    if type(ifiles) == "str":
        ifiles = [ifile]
    for ifile in ifiles:
        for i in pattern.finditer(open("merged/%s"%(ifile)).read()):
            print n
            n += 1
            if n == N:
                break
            m = mainpattern.match(i.group("SS"))
            for sk in skpattern.finditer(m.group("keys")):
                try:
                    defns[getSSFromLemma(sk.group("sk"))] = getDisambiguatedTerms(m.group("def"))
                except:
                    pass
    return defns

pattern = re.compile("""<synset .*?>(?P<SS>.*?)</synset>""", re.DOTALL)
