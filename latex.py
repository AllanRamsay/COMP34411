import re, sys, subprocess
from useful import *

def bw2at(s0):
    bw2at = {'E':'`','D':'.d','g':'.g','F':'aN','i':'u','H':'.h','j':'^g','$':'^s','p':'T','S':'.s','u':'uN','T':'.t','v':'_t','Y':'A','x':'_h','Z':'.z','*':'_d','|': "'A", "<":"A", ">":"A", '&':"U'", "}":"'y"}
    s1 = ""
    for c in s0:
        try:
            s1 += bw2at[c]
        except:
            s1 += c
    return r"\A{%s}"%(s1)

def remspecials(s):
    return replaceAll(s, [("_", r"\_"), ("$", r"\$"), (">", "I"), ("<", "O"), ("&", r"\&"), ("}",r"\}"), ("{",r"\{")])

def depth(tree):
    m = 0
    if type(tree) == "list":
        for x in tree[1:]:
            m = max(m, depth(x))
    return m+1

def width(tree):
    if type(tree) == "list":
        return max(1, sum([width(d) for d in tree[1:]]))
    else:
        return 1

def latexText(i, text):
    if text == "":
        return ""
    else:
        return r"""
{
\begin{examples}
\item[%s]
\begin{examples}
\item
%s
\item
%s
\end{examples}
\end{examples}
}
"""%(i, bw2at(text), remspecials(text))
        
def latexDTree(tree, colour, levelsep, treesep, links, indent=''):
    s = ""
    if indent == '':
        params = '[treefit=tight,levelsep=%spt, treesep=%spt, nodesep=0pt]'%(levelsep, treesep)
    else:
        params = ''
    if colour:
        usecolour = colour
    else:
        try:
            usecolour = tree[0].colour
            if usecolour == "red":
                try:
                    links.append((tree[0].position, tree[0].correct))
                except:
                    pass
        except:
            usecolour = "black"
    s += r"%s\pstree%s{{\pslnode{\textcolor{%s}{%s:%s}}{\textcolor{%s}{%s:%s}}\Rnode{N%s}{}}}{"%(indent,  params, usecolour, bw2at(tree[0].form), remspecials(tree[0].form), usecolour, remspecials(tree[0].tag), tree[0].position, tree[0].position)
    for d in tree[1:]:
        s += "\n%s%s"%(indent, latexDTree(d, colour, levelsep, treesep, links, indent=indent+' '))
    s += "}"
    return s

def latexPSTree(tree, treesep, levelsep, indent=''):
    if type(tree) == "WORD":
        return r"\pstree{\TR{%s$_{%s}^{\scriptsize %s}$}}{}"%(remspecials(tree.form), tree.position, remspecials(tree.tag))
    else:
        s = ""
        if indent == '':
            params = '[treefit=tight,levelsep=%spt, treesep=%spt, nodesep=2pt]'%(levelsep, treesep)
        else:
            params = ''
        s += r"%s\pstree%s{\TR{%s}}{"%(indent, params, remspecials(tree[0]))
        for d in tree[1:]:
            s += "\n%s%s"%(indent, latexPSTree(d, treesep, levelsep, indent=indent+' '))
        s += "}"
        return s

def latexSentence(i, tree, whichtrees=['PSTREE', 'DTREE', 'PARSED']):
    s = ""
    text = latexText(i, ' '.join([word.form for word in tree.leaves]))
    if 'PSTREE' in whichtrees:
        w = max(10, int(400/width(tree.pstree)))
        s += r"""
{
%s
%s
\newpage
}"""%(text, latexPSTree(tree.pstree, w, max(25, int(625/depth(tree.pstree)))))
    if 'DTREE' in whichtrees:
        w = max(20, int(500/width(tree.dtree)))
        s += r"""
{
%s
%s
\newpage
}"""%(text, latexDTree(tree.dtree, "blue", max(30, int(700/depth(tree.dtree))), w, False))
    if 'PARSED' in whichtrees:
        links = []
        w = max(20, int(width(tree.parsed)/0.45))
        s += r"""
{
%s
%s
}
"""%(text, latexDTree(tree.parsed, False, max(30, int(700/depth(tree.parsed))), w, links))
        for link in links:
            link = r"""\nccurve[angleA=270, angleB=0, linewidth=0.5pt,linecolor=blue, nodesepA=20pt, nodesepB=30pt,arrowscale=2.5]{->}{N%s}{N%s}"""%link
            s += link
        s += r"""
\newpage
"""
    return s

def latexTree(tree, whichtrees=['PSTREE', 'DTREE', 'PARSED'], out=sys.stdout):
    s = r"""
\documentclass[10pt]{article}
\usepackage[a3paper,landscape,margin=0.2in]{geometry}
\usepackage{defns}
\usepackage{pstricks, pst-node, pst-tree}
\usepackage{psfig}
\usepackage{ulem}
\usepackage{examples}
\usepackage{fancyvrb}
\usepackage{arabtex}
\usepackage{arababbr}

\begin{document}
\Large
"""
    if type(tree) == "SENTENCE":
        s += latexSentence(1, tree, whichtrees=whichtrees)
    else:
        i = 1
        for t in tree:
            s += latexSentence(i, t, whichtrees=whichtrees)
            i += 1
    s += r"""
\end{document}
"""
    with safeout(out) as write:
        write(s)
    if not out == sys.stdout:
        subprocess.Popen(['latex', out[:-4]]).wait()
        subprocess.Popen(['dvipdf', out[:-4]])
        
    
