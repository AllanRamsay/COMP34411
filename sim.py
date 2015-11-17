import re
import sys
import os
import math
import bnc
reload(bnc)
from useful import *
import useful
reload(useful)

"""
VO = sim.bnc.getDepRels(sim.bnc.BNC, "justverbandobj")

or 

VO = sim.load("VO.pck")

print sim.intersection('read', 'write', VO, 'OBJ', n=20)

words = sim.getWORDS(["eat", "devour", "drink", "sip", "read", "write", "love", "hate", "kick", "hit"], VO, "OBJ")
print words.selfcompare()

verbs = sim.getroletable(VO, "OBJ")
objects = sim.getroletable(VO, "MV")
"""

def sectionpattern(tag):
    return re.compile("<(?P<tag>(%s|%s).*?)>(?P<section>.*?)<?P=tag>"%(tag.lower(), tag.upper()), re.DOTALL)

def remSection(tag, text):
    return sectionpattern(tag).sub("", text)

def remtags(s):
    return re.compile('<.*?>', re.DOTALL).sub('', s)

def remKeyWord(w, s):
    return re.compile(w, re.IGNORECASE).sub('****', s)

# This is for reading in HTML pages and removing the tags and commands
def readDoc(file, keywords=[]):
    s = open(file, 'r').read()
    for x in ['script', 'style']:
        s = remsection(x, s)
    s = remtags(s)
    s = re.compile('(\s)\s*').sub(' ', s)
    for k in keywords:
        s = remKeyWord(k, s)
    return s
 
def intersection(word1, word2, table, role, n=20, out=sys.stdout, latex=False):
    table1 = table[word1][role]
    table2 = table[word2][role]
    with safeout(out) as write:
        if latex:
            write(r"""
\medpara
%s: """%(word1))
        else:
            write(r"""
%s: """%(word1))
        for word, count in sortTable(table1)[:n]:
            if word in table2:
                if latex:
                    write(r"\textcolor{blue}{%s, %s (%s)}; "%(word, count, table2[word]))
                else:
                    write("%s, %s (%s); "%(word, count, table2[word]))
            else:
                write("%s, %s; "%(word, count))
        if latex:
            write(r"""

\medpara
%s: """%(word2))
        else:
            write(r"""
            
%s: """%(word2))
        for word, count in sortTable(table2)[:n]:
            if word in table1:
                if latex:
                    write(r"\textcolor{blue}{%s, %s (%s)}; "%(word, count, table1[word]))
                else:
                    write("%s, %s (%s); "%(word, count, table1[word]))                   
            else:
                write("%s, %s; "%(word, count))
        if not latex:
            write("\n")
   
# An ITEM is an object with an associated vector.

class ITEM:
    
    def __repr__(self):
	return "<%s %s>"%(type(self), self.src)

    """
    Suppose v is {i, j, k}

    Then I want v.euclid({}) to be 1, i.e. sqrt(i^2+j^2+k^2) to be 1

    So I should divide each of them by (i^2+j^2+k^2)
    
    """
    def normalise(self):
        t = 0.0
        v = self.vector
        for k in v.values():
            t += k**2
        t = math.sqrt(t)
        for k in v:
            v[k] = v[k]/t

    def size(self):
        size = 0.0
        for x in self.vector.values():
            size = size+x*x
        return math.sqrt(size)

    def euclid(self, other):
	n = 0.0
	v0 = self.vector
        size0 = self.size()
	v1 = other.vector
        size1 = other.size()
        for k in v0:
            v0k = v0[k]/size0
            if k in v1:
                v1k = v1[k]/size1
                n += (v0k-v1k)*(v0k-v1k)
            else:
                n += v0k*v0k
        for k in v1:
            if not k in v0:
                v1k = v1[k]/size1
                n += v1k*v1k
        return math.sqrt(n)

    def cos(self, other):
        v1 = self.vector
        v2 = other.vector
        nom = 0
        for k in v1:
            if k in v2:
                nom += v1[k]*v2[k]
        return float(nom)/(self.size()*other.size())
    
    def showSimilarities(self, others, compare):
	text = self.src
	s = [(self.compare(x), x.src) for x in others]
	s.sort()
	for x in s:
	    text = text+'&\n     '+self.src[1]+' %.2f'%x[0]
	text = text+r'\\'+'\n'
	return text

class VECTOR(ITEM):

    def __init__(self, vector, src="???"):
        self.vector = vector
        self.src = src

"""
A DOC is an ITEM whose vector is constructed by reading a document
(probably a web page: that's what I used in the lectures) and collecting
all the words on that page. So 'src' is the name of a file (smart would be if
it were a URL!)
"""

class DOC(ITEM):

    def __init__(self, src, keywords=[]):
	vector = {}
	self.src = src
	self.string = readDoc(src, keywords=keywords)
        for w in re.compile('[a-zA-Z]+').finditer(self.string):
            w = bnc.root(w.group(0).lower())
            incTable(w, vector, n=1.0)

 
"""
A WORD is an ITEM whose vector is constructed from a list of words that
have been found elsewhere (e.g. by finding co-occurring items: for the 
similarity server, these will have been read into a table of the form
{'read':{'headNoun':[('novel':20), ('poem':17), ...]}, {'verb':[...]}}
where the 'headNoun' list is a list of words that have occurred as the object
of 'read' and the 'verb' list contains that have had 'read' as their objects
(you could easily have other relationships: at the moment these are the two
I'm using)
"""             
    
class WORD(ITEM):

    def __init__(self, form, vector):
	self.vector = vector
	self.src = form
        
def getWORDS(words, d, role):
    return ITEMSET([WORD(w, d[w][role]) for w in words if w in d and role in d[w]])

"""
An ITEMSET is a set of ITEMS (!). Initialisation includes removing
entries from vectors if they occur nowhere else in the set (because
if that happens then they cannot contribute to comparison with other
items) and readjusting the scores in each item by TF/IDF-ing them.
"""

class ITEMSET:

    def __init__(self, items):
        self.items = items
	self.allTerms = {}
	self.table = {}
	for d in items:
	    self.table[d.src] = d
        for d in items:
            for f in d.vector.keys():
                incTable(f, self.allTerms)
        self.index = False
        self.tfidf()
        self.index = {x.src:x for x in self.items}

    def __repr__(self):
        return "<ITEMSET: %s>"%(", ".join(map(str, self.items)))

    def __getitem__(self, i):
        try:
            return self.items[i]
        except:
            return self.find(i)

    def __iter__(self):
        return iter(self.index)

    def __len__(self):
        return len(self.items)

    def find(self, k):
        try:
            return self.index[k]
        except Exception as e:
            print "??? find(%s)"%(k)
            raise e
	
    # I've split the calculation of the DF out so that it can be done for
    # whole itemset just once. I can't actually see a point where I would
    # want to do this, but I can almost imagine wanting it. So here it is.

    def tfidf(self):
	for d in self.items:
            d.tfidf = {}
            for k in d.vector:
		d.tfidf[k] = d.vector[k]/math.log(self.allTerms[k]+1)

    def selfcompare(self, out=sys.stdout, latex=False):
        with safeout(out) as write:
            if latex:
                write(r"""
\begin{tabular}{|l|%s|}
\hline
"""%("c"*len(self.items)))
            write("\t")
            for ii in self.items:
                if latex:
                    write("& %s"%(ii.src))
                else:
                    write("%s\t"%(ii.src))
            if latex:
                write(r"""
\\
\hline
""")
            else:
                write("\n")
        for i in range(len(self.items)):
            ii = self.items[i]
            write("%s "%(ii.src))
            for j in range(len(self.items)):
                jj = self.items[j]
                if latex:
                    write("& %.3f"%(ii.cos(jj)))
                else:
                    write("\t%.3f"%(ii.cos(jj)))
            if latex:
                write(r"""
\\
\hline
""")
            else:
                write("\n")
        if latex:
            write(r"""
\end{tabular}
""")

    def mostDifferent(self):
        md = (1, 1, 1)
        for x in self.items:
            for y in self.items:
                s = x.cos(y)
                if s < md[0]:
                    md = (s, x, y)
        return md[1:]

# K-means clustering: a CLUSTER is based on an existing item. The main thing
# that you want to do to it is to update once you've found all the other ITEMS
# that want to belong to it.
    
def mergeTables(t1, t2):
    t = {}
    for k in t1:
        t[k] = t1[k]
    for k in t2:
        incTable(k, t, t2[k])
    return t
        
class CLUSTER(ITEM):

    def __init__(self, seeds):
        self.cluster = seeds
        self.update()
        self.vector = {}
        for s in seeds:
            self.vector = mergeTables(self.vector, s.vector)
        self.src = ":".join([d.src for d in self.cluster])

    def __repr__(self):
        return "<CLUSTER %s: %s, %.2f>"%(self.src, len(self.cluster), self.density())

    def update(self):
        scores = self.sorted()
        t = {x.src:x for x in self.cluster}
        self.cluster = [t[x[0]] for x in scores[:len(scores)/2+1]]
        self.vector = {}
        for doc in self.cluster:
            self.vector = mergeTables(self.vector, doc.vector)
        self.src = ":".join(sorted([d.src for d in self.cluster]))

    def density(self):
        d = 0.0
        n = 0
        for i in range(len(self.cluster)):
            d += self.cluster[i].cos(VECTOR(self.vector))
            n += 1
        try:
            return d/n
        except:
            return 1

    def sorted(self):
        scores = {}
        bestdist = 0.0
        for x in self.cluster:
            dist = 0.0
            n = 0.0
            for y in self.cluster:
                dy = x.cos(y)
                dist += dy
                n += 1
            dx = dist/n
            if dx > bestdist:
                bestdist = dx
                self.best = x
            scores[x.src] = dx
        return sortTable(scores)

class CLUSTERSET(ITEMSET):

    def __init__(self, items, seeds=False):
        if type(items) == "list":
            items = ITEMSET(items)
        self.items = items
        self.clusters = map((lambda seed: CLUSTER([seed])), seeds)
        self.src = ", ".join(map(str, self.clusters))

    def __repr__(self):
        return "<CLUSTERSET %s>"%(self.src)
    
    def __getitem__(self, i):
        return self.clusters[i]

    def __iter__(self):
        return iter(self.clusters)

    def update(self, printing=0):
        clusters = self.clusters
        for cluster in clusters:
            cluster.cluster = []
        changed = False
	for doc in self.items.items:
            t = 0
	    c = clusters[0]
	    for cluster in clusters:
		t1 = doc.cos(cluster)
                if printing > 1:
                    print "Target item: %s, cluster: %s, cos %.3f"%(doc.src, cluster, t1)
		if t1 > t:
		    t = t1
		    c = cluster
            else:
	        c.cluster.append(doc)
                try:
                    if not doc.belongsto == c:
                        changed = True
                        doc.belongsto = c
                except AttributeError:
                    changed = True
                    doc.belongsto = c
        for cluster in clusters:
            cluster.update()
        self.clusters = clusters
        self.src = ", ".join(map(str, self.clusters))
        return changed

    def updateN(self, n=100, printing=True):
        for i in range(n):
            if printing:
                print "Generation %s"%(i)
                printall(self.clusters)
            changed = self.update(printing=printing)
            if not changed:
                break
        self.score = sum(map(lambda x: x.density()/len(self.clusters), self.clusters))
        return self

    def separation(self):
        l = []
        for i in range(len(self.clusters)):
            xi = self.clusters[i]
            for j in range(i+1, len(self.clusters)):
                l.append(xi.cos(self.clusters[j]))
        return l

def rank(d, n0=200, n1=200000):
    r = {}
    for x in d:
        t = 0
        for k in d[x].vector.keys():
            try:
                t += d[x].vector[k]
            except:
                pass
        r[x] = t
    return sortTable(r)

def prune(d, n0=200, n1=200000):
    return {x[0]:d[x[0]] for x in rank(d, n0, n1)}

def getroletable(VO, role):
    return ITEMSET([WORD(k, VO[k][role]) for k in VO if role in VO[k]])

import random
def chooseSeeds(table1, table2, potentialseeds=False, target=False, nclusters=4, nseeds=20, sIterations=10000):
    if not potentialseeds:
        potentialseeds = [x[0] for x in sortTable(table1[target].vector) if x[0] in table2 and len(table2[x[0]].vector)][:nseeds]
    seen = {}
    bestscore = nclusters**2
    best = False
    for i in range(sIterations):
        s = sorted([table2[x] for x in random.sample(potentialseeds, nclusters)])
        d = 0.0
        for i in range(len(s)):
            for j in range(i+1, len(s)):
                d += s[i].cos(s[j])
        if str(s) in seen:
            continue
        seen[str(s)] = True
        if d < bestscore:
            bestscore = d
            best = s
        # print s, "%.2f"%(d)
    return best

def findClusters(table1, table2, seeds=False, potentialseeds=False, target=False, nclusters=4, nseeds=20, nwords=200, sIterations=10000):
    if seeds:
        seeds = [table2[x] for x in seeds]
    else:
        seeds = chooseSeeds(table1, table2, potentialseeds=potentialseeds, target=target, nseeds=nseeds, nclusters=nclusters, sIterations=sIterations)
    print seeds
    if target:
        words = [table2[x[0]] for x in sortTable(table1[target].vector)[:nwords] if x[0] in table2 and len(table2[x[0]].vector)>4]
    else:
        words = [table2[x] for x in potentialseeds]
    return CLUSTERSET(words, seeds)

def iterateClusters(table1, table2, I, seeds=False, potentialseeds=False, target=False, nclusters=4, nseeds=20, nwords=200, sIterations=10000):
    for i in range(2, I):
        c = findClusters(table1, table2, target=target, nclusters=i, nseeds=nseeds, nwords=nwords, sIterations=sIterations).updateN()
        print "%i, %.2f"%(i, c.score)
        printall(c.clusters)



