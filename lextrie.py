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

"""
A root can look like "(a>b)>c". If you find "c", you want to be
left with "a>b", not "(a>b)".
"""

def removeOuterBrackets(s):
    if len(s) > 1 and s[0] == "(" and s[-1] == ")":
        return s[1:-1]
    else:
        return s

"""
Similarly, a root can look "a>(b>c)". If we find "b>c" we obviously want to match that with "(b>c)"
"""
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

"""
Come here if we've just found some words at the current node. We have to see which of these
will combine with any of the fragments we've already got.
"""
def getcombinations(fragments, words, unseen, seen, top, indent="", rules=[], printing=False):
    if fragments == False:
        """
        This is the first set of items that you've found in the
        dictionary. So there isn't anything for them to combine with,
        so just return them
        """
        combinations = words
    else:
        """
        We've found some items. We already had some items. We want the things 
        that combine properly
        """
        if printing:
            print "%sLooking for combinations between %s and %s"%(indent, fragments, words)
        """
        combinations is the actual things we found
        """
        combinations = []
        """
        commentary is just for printing
        """
        commentary = ""
        for w0 in fragments:
            for w1 in words:
                c = combine(w0, w1)
                if c:
                    commentary += "%s+%s -> %s, "%(w0, w1, c)
                    combinations.append(c)
        if printing:
            if commentary == "":
                print "%sNone found"%(indent)
            else:
                print "%sFound %s"%(indent, commentary)
    if combinations == []:
        """
        If none of your existing fragments combined with any of your new
        items then this is not going anywhere
        """
        return []
    else:
        """
        Reenter the trie with the things you just found as the fragments you are building. You aren't allowed
        to carry out any spelling changes immediately after doing combinations: if there were any to be done,
        they should have been done BEFORE this.
        """
        return lookup(top, unseen, fragments=combinations, seen=seen, top=top, indent=indent, rules=rules, printing=printing, spellingChangesAllowed=False)

def lookup(trie, unseen, fragments=False, top=False, seen="", indent="", rules=[], printing=False, spellingChangesAllowed=True):
    if not top:
        top = trie
    if printing:
        if fragments == False:
            print "%s%s^%s"%(indent, reverse(seen), unseen)
        else:
            print "%s%s^%s, items found so far %s"%(indent, reverse(seen), unseen, fragments)
    if len(unseen) > 0 and unseen[0] == "+":
        if printing:
            print "%s going down alternative branch: %s"%(indent, unseen)
        return lookup(trie, unseen[1:], fragments=fragments, top=top, seen="+"+seen, indent=indent+"  ", rules=rules, printing=printing)
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
    (because that's tantamount to having an empty prefix, and
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
            answers += getcombinations(fragments, words, unseen, seen, top, indent=indent+"  ", rules=rules, printing=printing)
    """
    If there's an arc that you can follow with the current
    character then follow it
    """
    if not unseen == "" and unseen[0] in trie.arcs:
        c = unseen[0]
        answers += lookup(trie.arcs[c].trie, unseen[1:], fragments=fragments, top=top, seen=c+seen, indent=indent+"  ", rules=rules, printing=printing)
    if spellingChangesAllowed:
        for rule in rules:
            for t in rule.matchRule(seen, unseen, indent=indent, printing=printing):
                if printing:
                    print "%sSpelling rule applies: %s: unseen was %s and is now %s (seen %s)"%(indent, rule, unseen, t, reverse(seen))
                answers += lookup(trie, t, fragments=fragments, top=top, indent=indent+"  ", rules=rules, printing=printing)
    if printing:
        print "%sAnswers %s"%(indent, answers)
    return answers

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
    
    def show(self, indent='', out=sys.stdout):
        nl = '-'
        for arc in sorted(self.arcs.keys()):
            out.write(nl)
            indent1 = indent+'  '
            self.arcs[arc].show(indent1, out)
	    nl = '\n'+indent+'\\'
        if indent == '':
            out.write('\n')
            for w in self.getWords():
                out.write(str(w)+'\n')

    def getWords(self, prefix=''):
        words = []
        words = words+[(prefix, type) for type in self.words]
        for arc in sorted(self.arcs.keys()):
            arc = self.arcs[arc]
            c = arc.code
            words = words+arc.trie.getWords(prefix+c)
        return words

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

    def show(self, indent, out=sys.stdout):
        out.write(self.code)
        self.trie.show(indent, out)

