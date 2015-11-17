import re, sys, os
from nltk.corpus import wordnet as wn

def readAnswers(ifile="corpora/answers+misc/tasks/english-all-words/key"):
    answers = {}
    pattern = re.compile("(?P<id>d\S*)\s+(?P<sense>\S+:\S+)")
    for i in pattern.finditer(open(ifile).read()):
        try:
            answers[i.group("id")] = wn.lemma_from_key(i.group("sense"))
        except:
            pass
    return answers

def readTests(ifile="corpora/english-all-words/test/eng-all-words.test.xml"):
    pattern = re.compile("""(<head id="(?P<id>\S*)">(?P<form>\S*)</head>)|(?P<simpleword>\w+)""")
    n = 0
    idtable = {}
    text = []
    for line in open(ifile):
        m = pattern.match(line.strip())
        if m:
            id = m.group("id")
            if id:
                idtable[n] = id
                text.append(m.group("form"))
            else:
                text.append(m.group("simpleword"))
            n += 1
    return text, idtable

def canonicalAnswers(text, answers, idtable):
    markedup = []
    for i in range(len(text)):
        w = text[i]
        try:
            answer = answers[idtable[i]]
        except:
            answer = "ignore"
        markedup.append((w, answer))
    return markedup
    
