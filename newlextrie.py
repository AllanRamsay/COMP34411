import spelling
reload(spelling)
import useful
reload(useful)
import sys
import re

def removeOuterBrackets(s):
    if len(s) > 1 and s[0] == "(" and s[-1] == ")":
        return s[1:-1]
    else:
        return s
    
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

def latexsafe(s):
    return re.compile("(?P<b><|>)").sub("$\g<b>$", str(s)).replace("'", "").replace("_", "\_")

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
        print "%s%s^%s, carrying %s, route %s"%(indent, useful.reverse(seen), unseen, fragments, route)
    if latex:
        with useful.safeout(outfile, mode="a") as out:
            out(latexsafe(r"""
\newpage
%%%%%s
\scriptsize
"""%(route)))
            out(pstree(top, trie, route=route))
            out(latexsafe(r"""

\noindent
Unseen: %s, items found so far: %s

%s
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
def pstree(t, target, indent="", arcs=[], args="[treemode=R,linestyle=none,treesep=20pt]", route=[]):
    st = ""
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
        words = str(t.index)
        lsep = 60
        for a in t.arcs:
            if not t.arcs[a].trie.words == []:
                lsep = 120
                break
    else:
        lsep = 120
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

