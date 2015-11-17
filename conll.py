import re, sys, os
from word import WORD
from malt import RELATION, buildtree
from tb import SENTENCE
from useful import *

if usingMac():
    BNC = '/Users/ramsay/BNC'
    programs = "/Library/WebServer/CGI-Executables/COMP34411"
else:
    BNC = '/opt/info/courses/COMP34411/PROGRAMS/BNC'
    programs = "/opt/info/courses/COMP34411/PROGRAMS"
    
numPattern = re.compile("\d+\t(?P<num>\d+(\.\d+)?)\t")
                
def readconll(conllfile="%s/ud-treebanks-v1.1/UD_English/wholething.txt"%(programs)):
    specials = {"-":"DASH", 
                "that":"THAT",
                "if":"IF",
                "his":"PX",
                "my":"PX",
                "our":"PX",
                "your":"PX",
                "their":"PX",
                "sure":"JJ",
                "ago":"NI",
                "of":"OF",
                "has":"VH", "had":"VH", "have":"VH", "having":"VH",
                "be":"VX", "am":"VX", "is":"VX", "are":"VX", "was":"VX", "were":"VX", "being":"VX", "been":"VX", }
    preps = ['@', 'about', 'across', 'after', 'although', 'as', 'at', 'because', 'before', 'behind', 'besides', 'between', 'beyond', 'by', 'due', 'during', 'for', 'in', 'into', 'near', 'on', 'over', 'out', 'per', 'since', 'than', 'through', 'till', 'under', 'up', 'vs', 'vs.', 'whereas', 'while', 'with']
    for p in preps:
        specials[p] = "IN"
    sentences = []
    words = []
    sentence = []
    n = 0
    for line in open(conllfile).readlines():
        line = line.strip()
        m = numPattern.match(line)
        line = line.replace("``", '"').replace("''", '"')
        if line == "":
            if len(sentence) > 1:
                relations = [RELATION(word.hd, word.position, rel=word.label) for word in sentence]
                preswap(sentence, relations)
                tree = buildtree(relations, sentence)
                leaves = sentence
                sentence = SENTENCE(leaves, conllfile, n, n)
                sentence.dtree = tree
                sentence.leaves = leaves
                relations = {r.dtr:r for r in relations}
                sentence.goldstandard = relations
                sentence.parsed = relations
                sentences.append(sentence)
            sentence = []
        else:
            word = line.split("\t")
            POSITION = 0
            FORM = 1
            TAG = 4
            HD = 6
            LABEL = 7
            form = word[FORM]
            if form[0] in "?.!*+-=":
                word[FORM] = form[0]
                form = word[FORM]
            if re.compile("\d+(\.\d+)").match(form):
                word[FORM] = "9999"
                form = word[FORM]
            if word[TAG] == "NNP":
                word[TAG] = "NP"
            else:
                word[FORM] = form.lower()
                form = word[FORM]
            if form in specials:
                word[TAG] = specials[form]
            word = WORD(form=word[FORM], tag=word[TAG], label=word[LABEL], hd=int(word[HD])-1, position=int(word[POSITION])-1)
            sentence.append(word)
            words.append(word)
    if len(sentence) > 1:
        preswap(sentence)
        tree = buildtree([RELATION(word.hd, word.position, rel=word.label) for word in sentence], sentence)
        sentence = SENTENCE(words, conllfile, n, n)
        sentence.dtree = tree
        sentence.leaves = words
        sentences.append(sentence)
    return sentences, words

def swap(w, words, relations, swapdtrs=False):
    i = w.position
    h = words[w.hd]
    rx = False
    ry = False
    for r in relations:
        if r.dtr == h.position:
            rx = r
        if r.dtr == i:
            ry = r
    if rx and ry:
        if swapdtrs:
            for r in relations:
                if r.hd == h.position and not r.dtr == i:
                    r.hd = w.position
        rx.dtr = i
        ry.dtr = ry.hd
        ry.hd = i
    
def preswap(words, relations):
    for x in words:
        if False and x.tag == "TO" and x.hd >= 0:
            swap(x, words, relations)
        if False and x.tag == "IN" and x.hd >= 0:
            swap(x, words, relations)
        if x.label == "cop" and x.hd >= 0:
            swap(x, words, relations, swapdtrs=True)
            break

def swaprel(r, relations):
    print "swaprel(%s, %s)"%(r, relations)
    hd = r.hd
    dtr = r.dtr
    hdhd = relations[hd].hd
    print r, hd, dtr, hdhd
            
def postswap(relations, words):
    for x in relations:
        x = relations[x]
        if True and words[x.dtr].tag == "IN" and x.hd >= 0:
            swaprel(x, relations)
        if True and words[x.dtr].tag == "TO" and x.hd >= 0:
            swaprel(x, relations)
        if words[x.dtr].tag == "." and not x.hd == -1:
            swaprel(x, relations)

def allpostswaps(sentences):
    for s in sentences:
        print s.parsed
        print s.leaves
        postswap(s.parsed, s.leaves)
        postswap(s.goldstandard, s.leaves)
        
def red(s):
    return """<span style="fontsize: 0.5em; color:red;">%s</span>"""%(s)

def getmistagged(tagger, words, out=sys.stdout):
    with safeout(out) as out:
        out("<html><body>\n  <table>\n")
        tagged = tagger.tag(map(lambda x: x.form, words))
        for x, t0, t1 in map(lambda x: x[0]+[x[1]], zip(map(lambda x: [x.form, x.tag], words), map(lambda x: x[1], tagged))):
            if t0[:len(t1)] == t1:
                out("    <tr><td>%s</td><td>%s</td><td>%s</td></tr>\n"%(x, t0, t1))
            else:
                out("""    <tr><td>%s</td><td>%s</td><td>%s</td></tr>\n"""%(red(x), red(t0), red(t1)))
        out("  </table></body>\n</html>")

def getpreps(tagger):
    d = tagger.mxl.dict
    preps = {}
    for x in d:
        v = d[x]
        if not "-" in x and not "!" in x and 'IN' in v and len(v) > 1 and v['IN'] > 0.6:
            preps[x] = v
    return preps

def simplifytree(tree):
    if type(tree) == "WORD":
        return r"{\Rnode{N%s}{\footnotesize \textcolor{%s}{%s$_{%s}^{%s:%s}$}}}"%(tree.position, tree.colour, tree.form.replace("$", r"\$"), tree.label, tree.position, tree.tag.replace("$", r"\$"))
    else:
        return map(simplifytree, tree)

def plantlinks(tree):
    goldstandard = tree.goldstandard
    parsed = tree.parsed
    s = ""
    for x in parsed:
        if x in goldstandard:
            h0 = parsed[x]
            h1 = goldstandard[x]
            if not h0.hd == h1.hd:
                s += "\\ncline[linecolor=blue,linestyle=dashed]{->}{N%s}{N%s}\n"%(x, h1.hd)
    return s
            
def showtrees(trees, outfile=sys.stdout):
    with safeout(outfile) as out:
        out(r"""
\documentclass[10pt]{article}
\usepackage[a4paper,landscape]{geometry}
\usepackage{headerfooter}
\usepackage{defns}
\usepackage{lscape}
\usepackage{ifthen}
\usepackage{natbib}
\usepackage{lscape}
\usepackage{examples}
\usepackage{multicol}
\usepackage[usenames,dvipsnames,svgnames,table]{xcolor}
\usepackage{pstricks, pst-node, pst-tree}
\usepackage{graphicx}
\oddsidemargin=0in
\evensidemargin=0in
\begin{document}
\begin{examples}
""")

        for tree in trees:
            for leaf in tree.leaves:
                leaf.colour = "black"
            t = simplifytree(tree.dtree)
            d = depth(t)
            out(r"""

\newpage
\item %s

\noindent
DTREE (= Gold Standard)

\noindent
%s
"""%(" ".join(map(lambda x: x.form, tree.leaves)).replace("$", r"\$"),
     pstree(t, lsep=min(70, int(350.0/d)), tsep=20)))
            goldstandard = tree.goldstandard
            parsed = tree.parsed
            out(showTreeAsArcs(tree.leaves, goldstandard))
            for leaf in tree.leaves:
                i = leaf.position
                if i in goldstandard and i in parsed:
                    if not goldstandard[i].hd == parsed[i].hd:
                        leaf.colour = "red"
                elif i in goldstandard or i in parsed:
                    leaf.colour = "red"
            t = simplifytree(buildtree(tree.parsed, tree.leaves))
            d = depth(t)
            out(r"""         
\newpage
\noindent
PARSED

\noindent
%s
"""%(pstree(t, lsep=min(70, int(350/d)), tsep=20)))
            out(plantlinks(tree))
            out(showTreeAsArcs(tree.leaves, parsed))
        out(r"""
\end{examples}
\end{document}
""")
    if not outfile == sys.stdout:
        subprocess.Popen(["latex", outfile]).wait()
        subprocess.Popen(["dvipdf", outfile[:-4]]).wait()
        print "dvipdf complete"

from math import log
def showTreeAsArcs(leaves, relations):
    if len(leaves) > 10:
        return ""
    txt = "\n"
    for leaf in leaves:
        txt += r"""\Rnode{c%sleft}{}\Rnode{c%scentre}{%s}\Rnode{c%sright}{}\hspace{0.5in}
"""%(leaf.position, leaf.position, leaf.form, leaf.position)
    for r in relations.values():
        if r.hd > r.dtr:
            A = "left"
            B = "right"
        else:
            A = "right"
            B = "left"
        if abs(r.hd-r.dtr) == 1:
            txt += r"""\ncline[nodesepA=8pt,nodesepB=3pt,arrowscale=2]{->}{c%s%s}{c%s%s}
"""%(r.hd, A, r.dtr, B)
        else:
            txt += r"""\nccurve[angleA=%s,angleB=%s,nodesepA=8pt,nodesepB=3pt,ncurv=%.2f,arrowscale=2]{->}{c%s%s}{c%scentre}
"""%(90, 90, log(abs(r.hd-r.dtr))/2, r.hd, A, r.dtr)
    return txt

NPPN = {"NP":True, "PN":True}
def tagsandstuff(words, mixedcase):
    tagset = {}
    contexts = {}
    mapctxt = lambda x: [x.form, x.tag]
    for i in range(len(words)):
        word = words[i]
        form = word.form
        if word.position==0 and form.istitle() and not word.tag in NPPN:
            form = form.lower()
        context = [map(mapctxt,words[i-5:i]), map(mapctxt, words[i:i+6])]
        try:
            contexts[form].append(context)
        except:
            contexts[form] = [context]
        if not form in tagset:
            tagset[form] = {}
        try:
            tagset[form][word.tag[:2]] += 1
        except:
            tagset[form][word.tag[:2]] = 1
    return tagset, contexts

def getmismatches(tagset1, tagset2, i=0, mismatches=False):
    if mismatches == False:
        mismatches = {}
    for form in tagset1:
        if form in tagset2:
            mm = []
            for tag in tagset1[form]:
                if not tag in tagset2[form]:
                    mm.append(tag)
            if not mm == []:
                if not form in mismatches:
                    mismatches[form] = [[],[]]
                mismatches[form][i] = mm
    return mismatches

def mergetagsets(words1, words2):
    uppercase = {}
    lowercase = {}
    mixedcase = {}
    for word in words1+words2:
        form = word.form
        if word.position==0 and form.istitle() and not word.tag in NPPN:
            uppercase[form.lower()] = True
        elif form.islower():
            lowercase[form] = True
    for form in uppercase:
        if form in lowercase:
            mixedcase[form] = True
    tagset1, contexts1 = tagsandstuff(words1, mixedcase)
    tagset2, contexts2 = tagsandstuff(words2, mixedcase)
    mismatches = getmismatches(tagset2, tagset1, i=0)
    mismatches=getmismatches(tagset1, tagset2, i=1, mismatches=mismatches)
    return mismatches, tagset1, tagset2, contexts1, contexts2

def gettagpairs(t1, t2, mismatches):
    tagpairs = []
    for form in mismatches:
        if mismatches[form] == [t1, t2]:
            tagpairs.append(form)
    return sorted(tagpairs)

def showcontexts(x, contexts, tag=False):
    if not x in contexts:
        return
    if tag:
        contexts = [ctxt for ctxt in contexts[x] if [x, tag] == ctxt[1][0]]
    else:
        contexts = contexts[x]
    for ctxt in contexts:
        left = " ".join([c[0] for c in ctxt[0]])
        while len(left) < 50:
            left = " "+left
        right = " ".join([c[0] for c in ctxt[1]])
        print left[-50:]+" "+right
        
"""
If UD says NP and PTB says PN use PN.

If PTP says IN then use it.

If UD says VX then use VX (equals "be")
"""
            
    

