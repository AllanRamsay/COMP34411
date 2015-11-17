"""
spelling.py

Programs to support COMP34411 Natural Language Systems: these programs
have more comments in them than code that I write for my own use, but
it's unlikely to be enough to make them easy to understand. If you
play with them then I hope they will help with understanding the ideas
and algorithms in the course. If you try to read the source code,
you'll probably just learn what a sloppy programmer I am.
"""

import re
from useful import *

class spellingRule:

    def __init__(self, left=[], target=[], right=[], result=[]):
	self.left = left
	self.target = target
	self.right = right
	self.result = result
	
    def __str__(self):
        """
        Thanks to Brendan Jackman for pointing out that I this the wrong way round
        """
	return str(self.target)+' ==> '+str(self.result)+' : '+str(self.left)+' _ '+str(self.right)+';'

    def __repr__(self):
        return str(self)

    """
    A rule has a left-hand side, a target, a right-hand side and a result. If the left-hand side
    matches the prefix and the target+the right-hand side match the suffix, then the rule
    applies. In which case you replace the bit of the suffix that matched the target by the result

    The only tricky bit is the use of variables: the matcher carries along a set of bindings, in the form
    of a hash table. When you first match a variable (something like "v0", "c0" or "x0") then the
    value is added to the bindings, subsequent cases have to match whatever was stored.
    """
    def matchRule(rule, prefix0, suffix0, indent='', printing=False):
        prefix1 = rule.left
        target = rule.target
        right = rule.right
        result = reverse(rule.result)
        suffix1 = target+right
        b = {}
        if matchSeq(prefix1, prefix0, b) and matchSeq(suffix1, suffix0, b):
            suffix0 = suffix0[len(target):]
            for x in result:
                suffix0 = lookup(x, b)+suffix0
            return [suffix0]
        return []

def reverse(l0):
    l1 = []
    for x in l0:
        l1 = [x]+l1
    return l1

def makePattern(name):
    return '\s*\[(?P<'+name+'>[^\]]*)\]\s*'

def makePartRule(m, s):
    p = re.compile('\s*,\s*')
    return [x for x in p.split(m.group(s)) if not(x == '')]

srPattern = re.compile(makePattern('target')+'==>'+makePattern('result')+':'+makePattern('left')+'_'+makePattern('right'))

basePattern = re.compile('(?P<rule>[^;\n]*);')

def makeSpellingRule(s):
    m = srPattern.match(s)
    if m:
        return spellingRule(reverse(makePartRule(m, 'left')), makePartRule(m, 'target'), makePartRule(m, 'right'), makePartRule(m, 'result'))
    else:
        return 'Error in rule format:' +s

def skipComments(s):
    return re.compile('(""".*?""")|(#[^\n]*\n)', re.DOTALL).sub("", s)
    
def readSpellingRules(rules='spellingRules.txt'):
    rules = [makeSpellingRule(i.group('rule')) for i in basePattern.finditer(skipComments(open(rules, 'r').read()))]
    printall(rules)
    return rules

def vowel(c):
    return c in "aeiou"

def consonant(c):
    return c in "qwrtypsdfghjklzxcvbnm"

def character(c):
    return not c in "+"

def bind(k, v, b):
    if k in b:
	return b[k] == v
    else:
	b[k] = v
	return True

def lookup(k, b):
    if k in b:
        return b[k]
    else:
        return k

"""
If c0 is a variable ("c0", "c1", ..., "v0", "v1", ..., "x0", "x1", ...)
then check that the target character is the right type and do/check the binding
"""
def matchChar(c0, c1, b):
    if len(c0) == 2:
        if c0[0] == 'v':
            return vowel(c1) and bind(c0, c1, b)
        if c0[0] == 'c':
            return consonant(c1) and bind(c0, c1, b)
        if c0[0] == 'x':
            return character(c1) and bind(c0, c1, b)
    else:
        return c1 in c0.split("/")

def matchSeq(l0, l1, b):
    if len(l0) > len(l1):
        return False
    for i in range(0, len(l0)):
        if not(matchChar(l0[i], l1[i], b)):
            return False
    return True
    
