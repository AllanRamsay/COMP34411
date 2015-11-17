"""
lextrie.py

Programs to support COMP34411 Natural Language Systems: these programs
have more comments in them than code that I write for my own use, but
it's unlikely to be enough to make them easy to understand. If you
play with them then I hope they will help with understanding the ideas
and algorithms in the course. If you try to read the source code,
you'll probably just learn what a sloppy programmer I am.
"""

import sys
import re
import spelling
import sign
import re
from useful import *

reload(spelling)

def removeOuterBrackets(s):
    if len(s) > 1 and s[0] == "(" and s[-1] == ")":
        return s[1:-1]
    else:
        return s
    
def latexsafe(s):
    return re.compile("(?P<b><|>)").sub("$\g<b>$", str(s)).replace("'", "").replace("_", "\_")
    
def combine(w0, w1):
    suffix = ">%s"%(w1)
    if w0.endswith(suffix):
        return removeOuterBrackets(w0[:-len(suffix)])
    suffix = ">(%s)"%(w1)
    if w0.endswith(suffix):
        return removeOuterBrackets(w0[:-len(suffix)])
    prefix = "<%s"%(w0)
    if w1.endswith(prefix):
        return removeOuterBrackets(w1[:-len(prefix)])
    prefix = "<(%s)"%(w0)
    if w1.endswith(prefix):
        return removeOuterBrackets(w1[:-len(prefix)])
    return False

def getcombinations(fragments, words1, unseen, seen, top, indent="", rules=[], printing=False, route=[], latex=False, outfile=sys.stdout):
    commentary = ""
    if fragments == []:
        combinations = words1
    else:
        combinations = []
        for w0 in fragments:
            for w1 in words1:
                c = combine(w0, w1)
                if c:
                    commentary += "%s+%s -> %s, "%(w0, w1, c)
                    if printing:
                        print "%s%s"%(indent, commentary)
                    combinations.append(c)
    if combinations == []:
        return []
    else:
        return lookup(top, unseen, fragments=combinations, seen=seen, top=top, indent=indent, rules=rules, printing=printing, spellingChanges=False, route=route, latex=latex, outfile=outfile, commentary=r"\noindent \textcolor{blue}{%s}"%(commentary))

def lookup(trie, unseen, fragments=[], top=False, seen="", indent="", rules=[], printing=False, reenter=False, spellingChanges=True, route=[], latex=False, outfile=sys.stdout, commentary=""):
    if not top:
        top = trie
    if printing:
        print "%s%s^%s, items found so far %s"%(indent, reverse(seen), unseen, fragments)
    if latex:
        with safeout(outfile, mode="a") as out:
            if trie == top and seen == "":
                out(r"""
\newpage
\begin{verbatim}
trie.lookup(t, '%s')
\end{verbatim}
"""%(unseen))
            out(latexsafe(r"""
\newpage
{\scriptsize
%%%%%s
"""%(route)))
            out(pstree(top, trie, route=route))
            out(latexsafe(r"""

\noindent
Unseen: %s, items found so far: %s

%s
}
"""%(unseen, fragments, commentary)))
    if unseen == "" and not [f for f in fragments if not ">" in f] == []:
        return fragments
    if len(unseen) > 0 and unseen[0] == "+":
        if printing:
            print "%s going down alternative branch: %s"%(indent, unseen)
        return lookup(trie, unseen[1:], fragments=fragments, top=top, seen="+"+seen, indent=indent+"  ", rules=rules, printing=printing, latex=latex, reenter=True, outfile=outfile, route=route)
    answers = []
    """
    We're at the end of the word and we're about to try
    to reenter the trie. Any proper word that we've found so
    far is an answer
    """
    if top == trie and unseen == "":
        answers += [f for f in fragments if not ">" in f and not "<" in f]
    """
    You might find some items here that combine with things 
    you've already got. Do the combinations and re-enter the
    trie from the start. 

    This is one set of answers to the overall problem. But 
    don't do it if you haven't seen any characters yet 
    (because that's tantamount to have an empty prefix, and
    they don't occur in English) and don't do it if there are
    no characters left to look at and you're about to reenter
    the trie (because that's tantamount to have an empty
    infix, and they don't occur in English either
    """
    if not seen == "" and not(trie == top and not unseen == ""):
        words = trie.words
        if not words == []:
            if printing:
                print "%s%s found here"%(indent, words)
            answers += getcombinations(fragments, words, unseen, seen, top, indent=indent+"  ", rules=rules, printing=printing, route=route, latex=latex, outfile=outfile)
    """
    If there's an arc that you can follow with the current
    character then follow it
    """
    if not unseen == "" and unseen[0] in trie.arcs:
        c = unseen[0]
        answers += lookup(trie.arcs[c].trie, unseen[1:], fragments=fragments, top=top, seen=c+seen, indent=indent+"  ", rules=rules, printing=printing, route=route+[(trie.index, trie.arcs[c].trie.index)], latex=latex, outfile=outfile)
    if spellingChanges and not reenter and not "+" in unseen:
        for rule in rules:
            for t in rule.matchRule(seen, unseen, indent=indent, printing=printing):
                if printing:
                    print "%sSpelling rule applies: %s: unseen was %s and is now %s (seen %s)"%(indent, rule, unseen, t, seen)
                if latex:
                    commentary = r"""
\noindent
Spelling rule applied: %s: unseen was %s and is now %s (seen %s)
"""%(rule, unseen, t, seen)
                answers += lookup(trie, t, fragments=fragments, top=top, indent=indent+"  ", rules=rules, printing=printing, latex=latex, route=route, outfile=outfile, commentary=commentary)
    if printing:
        print "%sAnswers %s"%(indent, answers)
    return answers

import re
def pstree(t, target, indent="", arcs=False, args="[treemode=R,linestyle=none,treesep=20pt]", route=[]):
    st = ""
    if arcs == False:
        arcs = []
    for a in t.arcs:
        a = t.arcs[a]
        if (t.index, a.trie.index) in route:
            colour = "red"
        else:
            colour = "black"
        arcs.append(r"""
%s\ncline[linecolor=%s]{->}{%s}{%s}\ncput*{\textcolor{%s}{%s}}"""%(indent, colour, t.index, a.trie.index, colour, a.code))
        st += pstree(a.trie, target, indent=indent+" ", args=args, arcs=arcs, route=route)
    words = t.words
    if words == []:
        words = "."
        lsep = 60
        for a in t.arcs:
            if not t.arcs[a].trie.words == []:
                lsep = 60
                break
    else:
        lsep = 60
    words = re.compile("(?P<b><|>)").sub("$\g<b>$", str(words)).replace("'", "")
    if t == target:
        colour = "red"
    else:
        colour = "black"
    s = r"""
%s\pstree%s{\TR{\Rnode{%s}{\textcolor{%s}{%s}}}}{%s}"""%(indent, args.replace("]", ",levelsep=%spt]"%(lsep)), t.index, colour, words, st)
    if indent == "":
        for a in arcs:
            s += a
    return s

class TRIE:

    nodeCounter = 0
    
    def __init__(self, words=[]):
        self.words = []
        self.arcs = {}
        self.addAll(words)
        self.index = TRIE.nodeCounter
        TRIE.nodeCounter += 1

    def __str__(self):
        return 'TRIE('+str(self.words)+','+str(self.arcs)+')'

    def __repr__(self):
        return str(self)

    """
    If the string representing the surface form is empty,
    we've got to the point in the trie where we want to store
    the information about what this word is. Otherwise we
    follow (if possible) or introduce (if necessary) the necessary
    arc and move on.
    """
    def add(self, word, type, path=False):
        if word == '':
            if not type in self.words:
                self.words.append(type)
        else:
            c = word[0]
            try:
                self.arcs[c].add(word[1:], type, path)
                return
            except:
                arc = ARC()
                arc.code = c
                arc.add(word[1:], type, path)
                self.arcs[c] = arc

    def addAll(self, l):
        for x in l:
            self.add(x[0], x[1])

    """
    Dummy function left over from more complex version
    """
    def type(self, x):
        return x
                        
    """
    Do the lookup: complications arise because we want to apply rules (and we want to
    apply them sensibly!)
    """

class ARC:

    
    def __init__(self):
        self.code = ''
        self.trie = TRIE()

    def __str__(self):
        return str(self.code)+'->'+str(self.trie)

    def __repr__(self):
        return str(self)

    def __cmp__(self, other):
        if other.__class__.__name__ == 'ARC':
            if self.code == other.code:
                return 0
            elif self.code < other.code:
                return -1
            else:
                return 1
        else:
            return 1

    def add(self, word, root, type):
        self.trie.add(word, root, type)

    def lookup(self, suffix, prefix, rules, indent='', top=[], printing=False):
        return self.trie.lookup(suffix, prefix=prefix, rules=rules, indent=indent, top=top, printing=printing)

    def show(self, indent, out=sys.stdout):
        out.write(self.code)
        self.trie.show(indent, out)

WORDS = [("bar", "noun>agr"), ("bat", "noun>agr"), ("bard", "noun>agr"), ("battle", "noun>agr"),
         ("car", "noun>agr"), ("cat", "noun>agr"), ("cart", "noun>agr"), ("card", "noun>agr"), ("cattle", "noun>agr"), 
         ("catch", "noun>agr"), ("chase", "verb>tns"),
         ("construct", "verb>tns"),
         ("kiss", "noun>agr"), ("kiss", "verb>tns"), 
         ("walk", "verb>tns"),
         ("ed", "tns"), ("ing", "tns"), ("s", "tns"), ("", "tns"), 
         ("s", "agr"), ("", "agr"),
         ("re", "(verb>tns)>(verb>tns)"),
         ("ation", "(noun>agr)<(verb>tns)"),]

WORDS1 = [("bar", "noun>agr"), ("bat", "noun>agr"), ("bard", "noun>agr"), ("battle", "noun>agr"), ("bottle", "noun>agr"),
         ("car", "noun>agr"), ("cat", "noun>agr"), ("cart", "noun>agr"), ("card", "noun>agr"), ("cattle", "noun>agr"),]

L = [("cat", "noun>agr"), ("car", "noun>agr"), ("care", "noun>agr"), ("card", "noun>agr"), ("cot", "noun>agr"), ("core", "noun>agr"),
     ("s", "agr"), ("", "agr"),]
