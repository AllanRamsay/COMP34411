
import re, sys, subprocess
from useful import *

def gettag(s):
    return s.split(":")[1]

ftransitions = {"P":{"N":0.3, "V":0.7},
                "N":{"D":0.1, "V":0.5, "N":0.1, "A":0.1, "I":0.7},
                "D":{"N":0.5, "A":0.4, "V":0.1, "I":0.6},
                "V":{"D":0.3, "N":0.2, "V":0.1, "I":0.8},
                "A":{"N":0.8, "V":0.2},
                "I":{"N":0.4, "D":0.6}}

normalise2(ftransitions)

btransitions = {"N":{"D":0.4, "V":0.4, "A":0.2, "P":0.1, "N":0.1},
                "D":{"N":0.5, "V":0.5, "I":0.5},
                "V":{"P":0.3, "N":0.6, "V":0.2, "D":0.1, "A":0.1},
                "A":{"D":0.8, "N":0.2},
                "I":{"N":0.4, "V":0.6}}

normalise2(btransitions)

probs = {"he":{"P":0.8, "X":0.2},
         "runs":{"N":0.2, "V":0.8},
         "a":{"D":0.9, "N":0.1},
         "an":{"D":1.0},
         "the":{"D":1.0},
         "his":{"D":1.0},
         "time":{"N":0.5, "V":0.5},
         "flies":{"N":0.5, "V":0.5},
         "like":{"V":0.5, "I":0.5},
         "loves":{"V":0.5, "N":0.5},
         "life":{"V":0.5, "N":0.5},
         "great":{"A":1.0},
         "latest":{"A":0.5, "N":0.5},
         "of":{"I":1.0},
         "arrow":{"V":0.5, "N":0.5},
         "small":{"A":0.7, "V":0.3},
         "shop":{"N":0.5, "V":0.5}}
               
def mxl(nodes, probs=probs, ftransitions=ftransitions, outfile=sys.stdout, nodeprobs=False, red=False, showLinks=True):
    if nodeprobs == False:
        nodeprobs = {}
        for j in range(len(nodes)):
            node = nodes[j]
            nodeprobs[j] = {p:probs[node][p] for p in probs[node]}
    if outfile == sys.stdout or outfile == sys.stdout.write:
        return nodeprobs
    with safeout(outfile) as out:
        tagnodes = {}
        out(r"""
\newpage
\setlength{\tabcolsep}{40pt}
\begin{tabular}{%s}"""%("c"*(len(nodes))))
        maxdepth = 0
        tabstring = "%s"
        for i in range(len(nodes)):
            node = nodes[i]
            out(tabstring%(node))
            tabstring = "& %s"
            maxdepth = max(maxdepth, len(probs[node]))
        out("\\\\\n")
        for i in range(maxdepth):
            tabstring = ""
            for j in range(len(nodes)):
                node = nodes[j]
                tags = sorted(probs[node].keys())
                if len(tags) <= i:
                    out(tabstring)
                else:
                    if j == red:
                        colour = "red"
                    else:
                        colour = "blue"
                    out(" %s \\Rnode{%s:%s}{\\textcolor{%s}{%s:%.2f}}"%(tabstring, j, tags[i], colour, tags[i], nodeprobs[j][tags[i]]))
                    
                    try:
                        tagnodes[j].append('%s:%s'%(j, tags[i]))
                    except:
                        tagnodes[j] = ['%s:%s'%(j, tags[i])]
                tabstring = "&"
            out("\\\\\n")
            if i < maxdepth-1:
                out(("%s\\\\"%("&"*(len(nodes)-1)))*4)
        out("""
\\end{tabular}
""")
        if not showLinks:
            return nodeprobs
        for i in sorted(tagnodes.keys()):
            if i in tagnodes and i+1 in tagnodes:
                for ni in range(len(tagnodes[i])):
                    ti = tagnodes[i][ni]
                    for nj in range(len(tagnodes[i+1])):
                        tj = tagnodes[i+1][nj]
                        # connect(ni, nj, ftransitions, ti, tj, out)
                        connect(nj, ni, btransitions, tj, ti, out)
        out(r"""
{\large
\vspace{0.5in}
\noindent
Forward transition probabilities
""")
        transitions2tabular(ftransitions, outfile=out)
        out(r"""

\medpara
Backward transition probabilities
""")
        transitions2tabular(btransitions, outfile=out)
        out("""}


""")
        
    return nodeprobs

def connect(ni, nj, transitions, ti, tj, out):
    try:
        p = transitions[gettag(ti)][gettag(tj)]
    except:
        # no such transition = prob of taking it is 0
        p = 0
    if ni == nj:
        if ti < tj:
            angleA = 45
            angleB = 135
        else:
            angleA = -135
            angleB = -45
    if ni < nj:
        if ti < tj:
            angleA = -90
            angleB = 135
        else:
            angleA = -90
            angleB = 45
    if ni > nj:
        angleA = 90
        angleB = -135
    out("\\nccurve[nodesep=2pt, angleA=%s,angleB=%s,arrowscale=2]{->}{%s}{%s}\\ncput*[npos=0.33,nrot=:U]{\\footnotesize %.2f}\n"%(angleA, angleB, ti, tj, p))

def test(text="he runs a small shop", outfile=sys.stdout, N=0, included=True):
    if type(text) == "str":
        text = text.split(" ")
    with safeout(outfile) as out:
        if not outfile == sys.stdout and not included:
            out(r"""
\documentclass[12pt]{article}
\usepackage{pstricks, pst-node, pst-tree}
\begin{document}
""")
        nodeprobs = mxl(text, outfile=out, showLinks=False, red=-1)
        nodeprobs = mxl(text, outfile=out, red=-1)
        initialprobs = [(text[i], nodeprobs[i]) for i in range(len(text))]
        for i in range(N):
            nodeprobs = update(nodeprobs, i)
            if not outfile == sys.stdout:
                mxl(text, nodeprobs=nodeprobs, outfile=out, red=i)
        if not outfile == sys.stdout and not included:
            out("""
\\end{document}
""")
    if not outfile == sys.stdout and not included:
        outfile = outfile[:-4]
        subprocess.Popen(["latex", outfile]).wait()
        subprocess.Popen(["dvipdf", outfile]).wait()
        print "Latex complete"
    return initialprobs, [(text[i], nodeprobs[i]) for i in range(len(text))]

def update(nodeprobs, i, ftransition=ftransitions, btransitions=btransitions, out=sys.stdout):
    column = nodeprobs[i]
    try:
        nextcol = nodeprobs[i+1]
    except:
        nextcol = False
    try:
        prevcol = nodeprobs[i-1]
    except:
        prevcol = False
    FT = 0
    ftprobs = {}
    btprobs = {}
    for x in column:
        ftprobs[x] = 0
        if nextcol:
            for y in nextcol:
                try:
                    ftprobs[x] += ftransitions[x][y]
                except:
                    "Not there: so not possible. So 0"
        else:
            ftprobs[x] = 0
        btprobs[x] = 0
        if prevcol:
            for y in prevcol:
                try:
                    btprobs[x] += btransitions[x][y]
                except:
                    "Not there: so not possible. So 0"
        else:
            btprobs[x] = 0
    try:
        normalise(ftprobs)
    except:
        """ ftprobs is all 0"""
    try:
        normalise(btprobs)
    except:
        """ btprobs is all 0"""
    column = {x: column[x]+(btprobs[x]+ftprobs[x])**0.5 for x in column}
    normalise(column)
    nodeprobs = {j:nodeprobs[j] for j in nodeprobs}
    nodeprobs[i] = column
    return nodeprobs
        
def transitions2tabular(transitions, outfile=sys.stdout):
    maxtrans = 0
    for x in transitions:
        maxtrans = max(maxtrans, len(transitions[x]))
    with safeout(outfile) as out:
        out(r"""
{\large
\setlength{\tabcolsep}{1pt}
\begin{tabular}{%s}
\hline"""%("|c|"+("c"*maxtrans)+"|"))
        for x in transitions:
            out("\n%s"%(x))
            links = sorted(transitions[x].keys())
            for i in range(maxtrans):
                if i >= len(links):
                    out("&")
                else:
                    out("& %s:%.2f"%(links[i], transitions[x][links[i]]))
            out(r"\\")
        out(r"""
\hline
\end{tabular}
}
""")
        
    
