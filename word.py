import re

"""
What matters about a word is its form and its tag: but tags are used as patterns
for matching BNC tags: we compile these when we first see the word rather
than on the fly, and we stick them in self posPattern (we do also compile them
in the fly if necessary: I can't see how a situation can arise when a word is
created with a pattern but without the pattern being compiled at creation time,
but it does seem to happen so we check for it and compile them later if that
turns out to be necessary.
"""
    
"""
wordnet.morphy will usually get you the root if you give it the right
part of speech tag. Here I'm going to map the tag I got from the tagger
(which was itself derived from the BNC tags, i.e. NN0, VVI, ...) to
a wordnet tag (n, v, ...) and use that.
"""

try:
    from nltk.corpus import wordnet
except:
    print "Wordnet not available on this machine"

"""
You'd think that you could just take the lowercase first letter of the
tag, but with some tagsets this won't work (e.g. JJ for adjectives)
"""
tagequiv = {"NN":"n",
            "VV":"v",
            "VH":"v",
            "VB":"v",
            "JJ":"a",
            "AJ":"a"}

def morphy(w, t):
    try:
        return wordnet.morphy(w, tagequiv[t[:2]])
    except:
        return w
    
class WORD:

    def __init__(self, form=False, tag=False, position=False, label=False, hd=False):
        self.form = form
        self.tag = tag
        self.root = morphy(form, tag)
        self.position = position
        self.label = label
        self.hd = hd

    def __repr__(self):
	s = "word(%s, %s"%(self.form, self.tag)
	if type(self.label).__name__ == 'str':
	    s += ", label=%s"%(self.label)
	if type(self.position).__name__ == 'int':
	    s += ", position=%s"%(self.position)
	if type(self.hd).__name__ == 'int':
	    s += ", hd=%s"%(self.hd)
	return s+")"

    def short(self):
        return '%s:%s:%s'%(self.position,self.form,self.tag)

    """
    Two words match if they have the same form (or the first one
    doesn't have a form, in which case it's an element of a pattern,
    so we're not specifying the form) and its tagPattern matches the
    other word's tag. 
    """
    def match(self, other):
        if self.form and not self.form == other.form:
            return False
        if self.tag:
            return self.tagPattern.match(other.tag)
        return True

def isword(x):
    return x.__class__.__name__ == "WORD"
