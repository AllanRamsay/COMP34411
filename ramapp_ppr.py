#!/usr/bin/python

"""
PPR.PY: implementation of Agirre et al.'s approach to word sense disambiguation using personalised page rank.

Programs to support COMP34411 Natural Language Systems: these programs
have more comments in them than code that I write for my own use, but
it's unlikely to be enough to make them easy to understand. If you
play with them then I hope they will help with understanding the ideas
and algorithms in the course. If you try to read the source code,
you'll probably just learn what a sloppy programmer I am.
"""

import cgi
import cgitb
from useful import *
import sys
from scipy import sparse
import numpy
import cPickle
try:
    from postandsession import *
except:
    pass

numpy.set_printoptions(precision=2)
from nltk.corpus import wordnet
from nltk import word_tokenize

if usingMac():
    BNC = '/Users/ramsay/BNC'
    programs = "/Users/ramsay/TEACHING/MODULES/COMP34411/PROGRAMS-2014/PYTHON"
else:
    BNC = '/opt/info/courses/COMP34411/PROGRAMS/BNC'
    programs = "/opt/info/courses/COMP34411/PROGRAMS"

"""
Use my maximum-likelihood tagger
"""

"""
from tag import mxlmysqltagger
mxltag = mxlmysqltagger().tag
"""

try:
    mxltag = cPickle.load(open('mxl.pck')).tag
except Exception as e:
    pass
    

class node:

    def __init__(self, name, prob=0.0):
        self.name = name
        self.prob = prob

    def __repr__(self):
        return "{%s, %.2f}"%(self.name, self.prob)

class link:

    def __init__(self, a, b, prob=0.0):
        self.a = a
        self.b = b
        self.prob = prob

    def __repr__(self):
        return "%s->%s(%.2f)"%(self.a, self.b, self.prob)

class ppr:

    def __init__(self, links='', undirected=False):
        linktable = {}
        nodetable = {}
        if isstring(links):
            rawlinks = [l.strip().split("->") for l in links.split(",")]
            links = {}
            for (x, y) in rawlinks:
                if not x in links:
                    links[x] = {}
                links[x][y] = True
                if undirected:
                    if not y in links:
                        links[y] = {}
                    links[y][x] = True
        for l in links:
            nodetable[l] = node(l)
            for x in links[l]:
                lx = link(l, x)
                nodetable[x] = node(x)
                try:
                    linktable[l].append(lx)
                except:
                    linktable[l] = [lx]
        for a in linktable:
            alinks = linktable[a]
            if not alinks == []:
                p = 1.0/len(alinks)
                for alink in alinks:
                    alink.prob = p
        self.nodetable = nodetable
        self.linktable = linktable

    def setprobs(self, probs):
        nodes = self.nodetable
        for n in nodes:
            nodes[n].prob = 0.0
        probs = [p.strip().split("=") for p in probs.strip().split(",")]
        for p, t in probs:
            self.nodetable[p.strip()].prob = float(t.strip())

    def initprobs(self):
        probs = {}
        nodes = self.nodetable
        p = 1.0/len(nodes)
        for n in nodes:
            probs[n] = p
        return probs
   
    def getvariance(self, probs0, probs1):
        t = 0.0
        for n in probs0:
            t += abs(probs0[n]-probs1[n])
        return t
            
    template = r"""
	\BREAK
	\bigpara
	Page rank: network simulator
	
	\begin{minipage}[b]{0.5\linewidth}
	\rput(0, -10){\Rnode{A}{\LARGE A}}
	\rput(8, -10){\Rnode{B}{\LARGE B}}
	\rput(0, -2){\Rnode{C}{\LARGE C}}
	\rput(8, -2){\Rnode{D}{\LARGE D}}
        \rput(0, -14){\Rnode{a}{\LARGE {A}}}
        \rput(4, -14){\Rnode{b}{\LARGE {B}}}
        \rput(8, -14){\Rnode{c}{\LARGE {C}}}
        \rput(12, -14){\Rnode{d}{\LARGE {D}}}
	"""
	
    def latex(self, preferred=[], template=template, out=sys.stdout):
        nodes = self.nodetable
        links = self.linktable
        t = template
        s = ""
        for n in nodes:
            n = nodes[n]
            t = t.replace(' %s'%(n.name), ' %s (%.2f)'%(n.name, n.prob))
        s = s+t
        for l in links:
            for l in links[l]:
                a = l.a
                b = l.b
                if a < b:
                    s = s+r"""
\ncline[linewidth=2pt,nodesep=5pt]{->}{%s}{%s}\ncput*[npos=0.5,nrot=:U]{\large
	  %.2f}"""%(a, b, l.prob)
                else:
                    s = s+r"""
\nccurve[linewidth=2pt,nodesep=10pt, angleA=0, angleB=315]{->}{%s}{%s}\ncput*[npos=0.33,nrot=:U]{\large %.2f}"""%(a, b, l.prob)
        for p in preferred:
            s += r"""
\nccurve[linewidth=2pt,nodesep=10pt, angleA=0, angleB=315,linecolor=blue]{->}{%s}{%s}\ncput*[npos=0.33,nrot=:U]{\large %.2f}"""%(p.lower(), p, 0.15/len(preferred))
        s = s+r"""
	\end{minipage}
	"""
        return s

    def plaintext(self):
        s = ""
        for l in self.linktable:
            s += '%s\n'%(self.linktable[l])
        return s
	    
    def step(self, probs0, preferred=[], damping=0.85, weight=1):
        nodes = self.nodetable
        links = self.linktable
        probs1 = {}
        if preferred == []:
            damping = 1.0
        """ Look at every place it's possible to be """
        for n in nodes:
            """ Look at every place you can get to from there"""
            if n in links:
                for link in links[n]:
                    """
                    How likely is it that I'm at n * how likely am I to go from n to the next place
                    """
                    t = damping*probs0[link.a]*link.prob
                    b = link.b
                    try:
                        probs1[b] += t
                    except:
                        probs1[b] = t
        for n in preferred:
            probs1[n] += (1-damping)*weight/float(len(preferred))
        return probs1
     
    def run(self, probs, preferred=[], damping=0.85, weight=1, n=20, template=template, out=sys.stdout):
        probs = self.initprobs()
        nodes = self.nodetable
        links = self.linktable
        s = ""
        if template:
            s += self.latex(template=template, preferred=preferred, out=out)
        else:
            for nn in nodes:
                s += '%s %.2f, '%(nn, nodes[nn].prob)
            s += "\\\\\n"
        for i in range(n):
            probs = self.step(probs, preferred=preferred, damping=damping, weight=weight)
            for nn in nodes:
                nodes[nn].prob = probs[nn]
            if template:
                s = s+self.latex(template=template, preferred=preferred, out=out)
            else:
                for nn in nodes:
                    s += '%s %.2f, '%(nn, nodes[nn].prob)
                s += "\\\\\n"
        with safeout(out) as out:
            out(s)

class sparseppr:

    def __init__(self, links='', rows=False, columns=False, data=False, indices=False):
        if indices == False:
            rows = []
            columns = []
            data = []
            linktable = {}
            if isstring(links):
                nodenames = [n.strip() for n in nodenames.split(",")]
                for l in links.split(","):
                    a, b = l.split("->")
                    a = indices[a.strip()]
                    b = indices[b.strip()]
                    try:
                        linktable[a][b] = True
                    except:
                        linktable[a] = {b:True}
            else:
                nodenames = []
                nntable = {}
                for n in links:
                    if not n in nntable:
                        nntable[n] = True
                    for x in links[n]:
                        if not x in nntable:
                            nntable[x] = True
                nodenames = [n for n in nntable]
                linktable = links
            indices = {}
            for i in range(len(nodenames)):
                indices[nodenames[i]] = i
            print "Tables set up"
            n = 0.0
            N = float(len(linktable))
            for x in linktable:
                ltx = linktable[x]
                x = indices[x]
                print "%.4f, %s"%(n/N, n)
                n += 1.0
                for y in ltx:
                    t = ltx[y]
                    data.append(t)
                    y = indices[y]
                    rows.append(y)
                    columns.append(x)
        self.rows = numpy.array(rows)
        self.columns = numpy.array(columns)
        self.data = numpy.array(data)
        self.indices = indices
        self.sparsearray = sparse.csr_matrix((data, (rows, columns)), (len(indices), len(indices)))

    def initprobs(self):
        return numpy.array([1.0/len(self.indices)]*len(self.indices))
    
    def resetsparsematrix(self):
        if self.sparsearray.__class__.__name__ == 'bool':
            self.sparsearray = sparse.csr_matrix((self.data, (self.rows, self.columns)), (len(self.indices), len(self.indices)))
        
    def step(self, p0):
        self.resetsparsematrix()
        return self.sparsearray.dot(p0)

    def run(self, probs, preferred=[], target=[], pweight=0.0, damping=1.0, n=1, template=False, out=sys.stdout):
        preferred = [self.indices[p] for p in preferred if p in self.indices]
        originalprobs = probs
        self.resetsparsematrix()
        links = self.sparsearray
        pweight = pweight*((1-damping)/len(originalprobs))
        damping = damping-len(preferred)*pweight
        dampingvector = numpy.array([damping/len(self.indices)]*len(self.indices))
        for p in preferred:
            dampingvector[p] += pweight
        for i in range(n):
            probs = (damping*links.dot(probs))+dampingvector
            variance = 0.0
            for i in range(len(probs)):
                variance += abs(probs[i]-originalprobs[i])
        choices = {}
        for t in target:
            try:
                choices[t] = probs[self.indices[t]]
            except:
                """
                If we had to allow all interpretations in allsynsets when we wanted to
                use the tagger (because the tagger chose the wrong thing, and then there
                were no synsets for what it chose) then we may find unwanted things here
                """
        return probs, variance, choices

    def chooseInterpretation(self, target, context, p0, damping=0.85, pweight=10000, n=10, tagger=False, useAll=False, tagging="useTagger", useboost="absolute"):
        targetsynsets, targettags = allsynsets(target, tagger=tagger, tagging=tagging)
        contextsynsets, contexttags = allsynsets(context, tagger=tagger, tagging=tagging)
        flattenedtargetsynsets = flatten(targetsynsets)
        flattenedcontextsynsets = flatten(contextsynsets)
        devnull = open("/dev/null", "a")
        probs, variance, t1 = self.run(p0, preferred=flattenedcontextsynsets, target=flattenedtargetsynsets, pweight=pweight, damping=0.85, n=n, out=devnull)
        probs, variance, t2 = self.run(p0, preferred=[], target=flattenedtargetsynsets, pweight=0.0, damping=0.85, n=n, out=devnull)
        g1 = gathersynsets(targetsynsets, t1)
        g2 = gathersynsets(targetsynsets, t2)
        allchoices = []
        for t1, t2 in zip(g1, g2):
            if useboost == "boost":
                choices = [(t1[x]/t2[x], x) for x in t1]
            else:
                choices = [(t1[x], x) for x in t1]
            choices.sort()
            choices.reverse()
            allchoices.append(choices)
        return allchoices, targettags, contexttags

    def save(self, out="wsd.pck"):
        out = open(out, 'w')
        cPickle.dump([self.rows, self.columns, self.data, self.indices], out)
        out.close()

def gathersynsets(targetsynsets, table):
    groups = []
    for tss in targetsynsets:
        group = {}
        for ss in tss:
            try:
                group[ss] = table[ss]
            except:
                """
                There may be a synset in targetsynsets that never made it into the main table
                """
        groups.append(group)
    return groups

def getUpDownLinks(word):
    seen = {}
    links = {}
    agenda = wordnet.synsets(word)
    while not agenda == []:
        print len(agenda), len(seen), len(links)
        ss = agenda.pop()
        if ss in seen:
            continue
        seen[ss] = True
        for s in ss.hypernyms()+ss.hyponyms():
            if not(s in seen):
                try:
                    links[ss.name][s.name] = 0
                except:
                    links[ss.name] = {s.name:0}
                agenda.append(s)
    for l in links:
        ll = links[l]
        for d in ll:
            links[l][d] = 1.0/float(len(ll))
    return links

import re
wordboundary = re.compile("\W+")
def getGlossLinks(word, useverbs=False, reflexive=False):
    seen = {}
    links = {}
    waiting = {}
    agenda = wordnet.synsets(word)
    n = 0
    while not agenda == []:
        print len(agenda), len(seen), len(links), n
        ss = agenda.pop()
        ssname = ss.name
        if ssname in seen:
            continue
        seen[ssname] = True
        defn = wordboundary.split(ss.definition)
        for w in defn:
            if len(w) < 3 or w == word:
                continue
            for s in wordnet.synsets(w):
                sname = s.name
                if (useverbs and '.v.' in sname) or '.n.' in sname:
                    try:
                        links[sname][ssname] = True
                    except:
                        links[sname] = {ssname:True}
                    n += 1
                    if reflexive:
                        try:
                            links[ssname][sname] = True
                        except:
                            links[ssname] = {sname:True}
                    if not sname in waiting:
                        agenda.append(s)
                        waiting[sname] = True
    for l in links:
        ll = links[l]
        for d in ll:
            links[l][d] = 1.0/float(len(ll))
    return links
    
def normalisearray(a):
    t = a.sum()
    for i in range(len(a)):
        a[i] = a[i]/t
        
def printtable(t, n=2):
    s = ""
    f = "%s, %.2f, ".replace("2", "%s"%(n))
    for x in t:
        s += f%(x, t[x])
    return s

def flatten(l0):
    l1 = []
    for l in l0:
        l1 += l
    return l1

def allsynsets(words, tagger=False, tagging="useAll"):
    ss0 = []
    if isstring(words):
        words = words.split(" ")
    for w in words:
        try:
            ss0.append([s.name for s in wordnet.synsets(w)])
        except:
            """ Calling s.name throws an exception on ramapp """
            ss0.append([s.name for s in wordnet.synsets(w)])
    if tagger:
        ss1 = []
        tags = tagger.tag(words)
        words = [x[1].lower()[0] for x in tags]
        for w, s in zip(words, ss0):
            ss1.append([x for x in s if '.%s.'%(w) in x])
        if not ss1 == []:
            return ss1, " ".join(["%s-%s"%(x[0], x[1]) for x in tags])
        tagging = "useAll"
    ss1 = []
    for s in ss0:
        ss1.append([x for x in s if tagging=="useAll" or '.n' in x])
    return ss1, []

def showchoices(allchoices):
    s = ""
    for choices in allchoices:
        if choices == []:
            s += "1.0::no synsets found (closed class word?)::\n\n"
            continue
        best = choices[0][0]
        for score, choice in choices:
            try:
                s += "%s::%s::%s\n"%(score/best, choice, wordnet.synset(choice).definition)
            except:
                """ Calling wordnet.synset(choice).definition throws an exception on ramapp """
                s += "%s::%s::%s\n"%(score/best, choice, wordnet.synset(choice).definition)
        s += "\n"
    return s

def wsd(POST, SESSION):
    content = ""
    [target, context, action, damping, contextprob, tagging, ranking] = allPOST(["target", "context", "action", "damping", "contextprob", "tagging", "ranking"], POST)
    if tagging == "":
        tagging = "useTagger"
    [useNPs, useTagger, useAll, useBoost, useAbsolute] = [""]*5
    if tagging == "useTagger":
        useTagger = " checked"
    elif tagging == "useNPs":
        useNPs = " checked"
    else:
        useAll = " checked"
    if ranking == "":
        ranking = "boost"
    if ranking == "boost":
        useBoost = " checked"
    else:
        useAbsolute = " checked"
    try:
        damping = float(damping)
    except:
        damping = 0.85
    try:
        contextprob = int(contextprob)
    except:
        contextprob = 10000
    cstring = "\n<table>\n"
    if not action == "":
            if context == "" and not target == "":
                context = target
            [rows, columns, data, indices] = cPickle.load(open("wsd.pck"))
            sppr = sparseppr(rows=rows, columns=columns, data=data, indices=indices)
            allchoices, targettags, contexttags = sppr.chooseInterpretation(target, context, sppr.initprobs(), pweight=contextprob, damping=damping, tagging=tagging, useboost=ranking)
            if tagging == "useTagger":
                cstring += "<p>Target tagged as %s<p>Context tagged as %s"%(targettags, contexttags.split("\n\n"))
            for form, choices in zip(target.split(" "), showchoices(allchoices).split("\n\n")):
                cstring += "<tr><th>%s</th><td><table>\n"%(form)
                for choice in choices.split("\n"):
                    choice = choice.strip()
                    if choice:
                        (score, ss, gloss) = choice.split("::", 2)
                        cstring += """
<tr>
  <td>%s</td>
  <td>%.2f</td>
  <td>%s</td>
</tr>"""%(ss, float(score), gloss)
                cstring += "</table></td></tr>"
    cstring += "\n</table>\n"
    content += """
<center><h2>PPR-based word sense disambiguation</h2></center>
"""
    if target == "":
        content += """
This is a rough implementation of Agirre et al.'s approach to WSD using personalised page rank on a network constructed
using wordnet glosses. If you specify a context then the target is disambiguated using the words in the context, so you can look at the influence of individual words on a target (e.g. try "bank" as the target and "money" or "boat" as the context). If you don't specify the context, the target itself is used as the context (try "I keep my money tied up at the bank" vs "I keep my boat tied up at the bank").
<p>
There are various parameters that you can alter. <b>Damping</b> is a measure of how much of the recalculated probability comes from the links and how much from the original probability mass, <b>Weight of context items</b> says how much more important context items are than non-context items, the <b>Tagging</b> radio buttons will let you decide whether to use the tagger when looking at synsets, and the <b>Ranking</b> radio buttons let you choose between my suggestion of using the items that receive the greatest boost from the context and the ones that obtain the highest overall score. I've set a reasonable collection of options, but you can try alternatives.
<p>
It's fairly fragile. You can let me know if it gives you error messages, then you can pass them on to me, but I'm probably not going to do anything about them. It's just to illustrate some points about WSD, so it won't break my heart if it sometimes misbehaves. If it crashes every time you try to use then that's another matter.
"""
    content += """
<form method="post">
<p>
<b>Target text:</b> <input type="text" name="target" size="50" value="%s">
<p>
<b>Context:</b> <input type="text" name="context" size="50" value="">
<p>
<b>Damping: </b> <input type="number" step="0.05" min="0.0" max="1.0" name="damping" width="4em" value="%s">
<b>Weight of context items:</b> <input type="number" step="1000" name="contextprob" size="10" min="0" max="99000" value="%s">
<p> <b>Tagging</b> <input type="radio" name="tagging" value="useNPs" %s>Just use synsets for nouns
<input type="radio" name="tagging" value="useTagger" %s>Use tagger
<input type="radio" name="tagging" value="useAll" %s>Use all synsets
<p>
<b>Ranking</b>
<input type="radio" name="ranking" value="boost" %s>Use boosted value
<input type="radio" name="ranking" value="absolute" %s>Use absolute value (which is what I think Agirre et al. do)
<p>
<input type="submit" name="action" value="Disambiguate target text"> (takes a while to load the PPR algorithm: the length of the target and context are almost irrelevant to the time taken)
</form>
<p>
%s
<p>
"""%(target, damping, contextprob, useNPs, useTagger, useAll, useBoost, useAbsolute, cstring)
    print """Content-type: text/html\n%s

<head>
<title>
PPR-based word sense disambiguation
</title>
<style>
table {
    border-collapse: collapse;
}

table, th, td, tr {
    border: 1px solid black;
    padding: 10px;
}
</style>
</head>
<body>
%s
</body>
"""%(SESSION.output(), content)
    

if 'ppr.py' in sys.argv[0]:
    try:
        cgitb.enable()
        mxltag = cPickle.load(open('mxl.pck')).tag
        POST = cgi.FieldStorage()
        SESSION = checkCookie()
        wsd(POST, SESSION)
    except:
        print """Content-type: text/html

"""
        cgitb.handler()
    
