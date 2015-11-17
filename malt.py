"""
MALT.PY

Programs to support COMP34411 Natural Language Systems: these programs
have more comments in them than code that I write for my own use, but
it's unlikely to be enough to make them easy to understand. If you
play with them then I hope they will help with understanding the ideas
and algorithms in the course. If you try to read the source code,
you'll probably just learn what a sloppy programmer I am.

Version of MALT with a couple of extensions:

(i) leftArc is allowed to look beyond the first element of the stack
for the dtr, rightArc is allowed to look beyond the first element of
the queue for the dtr. This allows us to deal with various kinds of
extraposition that would otherwise be impossible to handle (simple
example: "I am sleeping", with "I" as subject of "sleeping" and
"sleeping" as complement of "am").

(ii) It's set up so that we can find the sequence of actions that
would lead to a specified target tree. The function that actually does
this is given in forceparse.py, which is not distributed onto waldorf
(because if it were then it could be used to do the coursework!).

Because I want to be able to undo actions (either manually or in
forceparse), each action contains lists of previous stacks and
previous queues so that we can easily restore a previous state. I used
to do this just by reconstructing them, because if you use the simple
definitions of leftArc and rightArc then you know what the stack and
queue must have been like before the move that you're about to undo.
But once I allowed these actions to look beyond the start of the
queue/top of the stack for the dtr, that became more complicated, so
just remembering the previous state is the easiest thing to do. But
that means that operations on the stack and queue must not be
destructive.
"""

SILENT = False

import re
import cPickle
from useful import *
import os
from word import WORD

"""
from nltk.corpus import wordnet
"""

"""
Set BNC to point to the right place on different machines
"""

REPLAY = False
USEFORMS = False

if usingMac():
    BNC = '/Users/ramsay/BNC'
    programs = "/Library/WebServer/CGI-Executables/COMP34411"
else:
    BNC = '/opt/info/courses/COMP34411/PROGRAMS/BNC'
    programs = "/opt/info/courses/COMP34411/PROGRAMS"

"""
Use my maximum-likelihood tagger
"""

try:
    brilltagger
    print "brilltagger already loaded"
except:
    try:
        brilltagger = load('%s/brilltagger.pck'%(programs))
        print "%s/brilltagger.pck OK"%(programs)
    except:
        print "%s/brilltagger.pck not available"%(programs)
        brilltagger = False
    
def tag(s, tagger=brilltagger):
    s = [WORD(x[0], x[1]) for x in tagger.tag(s)]
    for i in range(len(s)):
        s[i].position = i
    return s

def buildtree(relns, words, top=True, indent='', target=False):
    if type(top) == 'bool':
        if type(relns) == "list":
            rtable = {}
            for r in relns:
                rtable[r.dtr] = r
            relns = rtable
        for i in relns:
            if relns[i].hd == -1:
                top = i
                break
        else:
            for i in relns:
                if not relns[i].hd in relns:
                    top = relns[i].hd
                    break
        if type(top) == 'bool':
            print "buildtree:\n%s\n%s\n%s"%(relns, words, top)
            raise Exception("Couldn't find top")
    if type(top) == "WORD":
        top = top.position
    try:
        l = [words[top]]
    except Exception as e:
        print "TOP %s\nWORDS %s"%(top, words)
        raise e
    for x in sorted(relns.keys()):
        if relns[x].hd == top:
            if target and not (x in target and relns[x].hd == target[x].hd):
                words[relns[x].dtr].colour = "red"
                try:
                    words[relns[x].dtr].correct = target[x].hd
                except:
                    pass
            l.append(buildtree(relns, words, top=x, indent=indent+' ', target=target))
    return l

"""
A state has the three basic data structures (queue, stack, relations)
together with functions (methods: it's a class) for doing shifts and reductions.

It also contains lists of old stacks and queues, so that we can backtrack easily; and
a list of the actions that led to here, so that we can replay it.
"""
class STATE:

    def __init__(self, text=False, queue=[], stack=[], tagger=brilltagger):
        self.relations = {}
        self.stack = stack
        self.queue = queue
        self.oldqueues = []
        self.oldstacks = []
        self.text = text
        self.words = False
        self.actions = []
        if text:
            if isstring(text):
                self.initialise(text, tag=tagger.tag)
            else:
                for i in range(len(text)):
                    text[i].position = i
                self.words = [w for w in text]
                self.queue = [w for w in text]

    def __repr__(self):
        if self.words:
            return 'STATE(words:%s, queue:%s, stack:%s, relations: %s)'%(self.words, self.queue, self.stack, self.relations)
        else:
            return 'STATE(queue:%s, stack:%s, relations:%s)'%(self.queue, self.stack, self.relations)

    def copy(self):
        new = STATE(queue=self.queue, stack=self.stack)
        new.actions = self.actions
        new.relations = {}
        for r in self.relations:
            new.relations[r] = self.relations[r]
        new.words = self.words
        new.text = self.text
        return new
    
    """
    Tag the text, convert it to "words" (which are more complicated than just 2-tuples)
    """
    def initialise(self, text, tag=tag):
        self.queue = map(lambda x: WORD(form=x[0], tag=x[1]), tag(text))
        self.words = self.queue
        for i in range(len(self.queue)):
            self.queue[i].position = i
    
    def showState(self, latex=False):
        verbatim("""Queue: %s
Stack: %s
Relations: %s"""%([w.short() for w in self.queue],
                  [w.short() for w in self.stack],
                  self.relations), silent=SILENT, latex=False)

    """
    Used for generating a state descriptor in a form that
    can be used by the machine learning algorithm
    """
                    
    def stateDescriptor(self, action, qwindow=2, stackwindow=2, maxdiff=3):
        queue = self.queue
        stack = self.stack
        s = []
        for i in range(qwindow):
            if i < len(queue):
                s.append(queue[i].tag)
            else:
                s.append("-")
        for i in range(stackwindow):
            if i < len(stack):
                s.append(stack[i].tag)
            else:
                s.append("-")
        if stack == [] or queue == []:
            d = "N"
        else:
            d = stack[0].position-queue[0].position
            if d < -maxdiff:
                d = -maxdiff
        s.append("%s"%(d))
        if not action:
            return s
        s = "\t".join(s)
        offset = action.offset
        if offset == 0:
            return s + "\t%s"%(action.fn.__name__)
        else:
            return s + "\t%s%s"%(action.fn.__name__, offset)

    """
    replay the state by performing the actions that led to
    it, starting with a queue containing the input words and an
    empty stack
    """
    def replay(self, qwindow=2, stackwindow=2):
        global REPLAY
        REPLAY = (qwindow, stackwindow)
        self.stack = []
        self.queue = self.words
        for a in self.actions:
            (a.fn)(self)

    """
    The next few bits are for performing hand-coded rules
    (as in the coursework)
    
    Match a pattern against a sequence of items. Done recursively because
    we might have a pattern [A, B, ???] to match against [A, B, C, D], where
    ??? matches the whole list [C, D]
    """
    def matchPattern(self, pattern, target):
        if pattern == []:
            return target == []
        if pattern[0] == '???':
            return True
        if target == []:
            return False
        else:
            return self.matchElement(pattern[0], target[0]) and self.matchPattern(pattern[1:], target[1:])

    def matchElement(self, p, t):
        return p.form.match(t.form) and p.tag.match(t.tag)

    """
    Two states match if their stacks match and their queues match
    """
    def match(self, other):
        return self.matchPattern(self.stack, other.stack) and self.matchPattern(self.queue, other.queue)

    def before(self, action, msg):
        if REPLAY:
            if self.text == False:
                self.text = ""
            descriptor = self.stateDescriptor(action, qwindow=REPLAY[0], stackwindow=REPLAY[1])
            verbatim(descriptor, silent=SILENT)
            self.text += "%s\n"%(descriptor)
        else:
            self.actions += [action]
            verbatim(msg, underline=True, silent=SILENT)
            self.showState()
        self.oldstacks.append(self.stack)
        self.oldqueues.append(self.queue)

    def after(self, msg):
        if not REPLAY:
            verbatim(msg, underline=True, silent=SILENT)
            self.showState()

    def warn(self, warnings, msg, throwException=False):
        if throwException:
            raise Exception(msg)
        if warnings:
            verbatim(msg, silent=SILENT)
            self.showState()
        return False
        
    """
    The actions: all pretty straightforward: do NOT change the operations on
    the stack and queue to be destructive (e.g. using .pop and .append) because
    in the trainable version I allow a copy of a state to have the same queue
    and stack as the original: which means that if you did something destructively
    to the copy it would also change the original
    """
            
    def shift(self, dummyArg=False, offset=0, warnings=True, throwException=False):
        if self.queue == []:
            return self.warn(warnings, "Can't call shift with empty queue", throwException=throwException)
        action = ACTION(STATE.shift, dummyArg, offset)
        self.before(action, "Before shift")
        self.stack = [self.queue[0]]+self.stack
        self.queue = self.queue[1:]
        self.after("After shift")
        return self

    """
    leftArc: head of the queue is the i'th item on the stack
    """
    def leftArc(self, d="unknown", i=0, warnings=True, throwException=False):
        queue = self.queue
        stack = self.stack
        if queue == []:
            return self.warn(warnings, "Can't call leftArc with empty queue", throwException=throwException)
        if len(stack) <= i:
            return self.warn(warnings, "Can't call leftArc(%s) with stack of length %s"%(i, len(stack)), throwException=throwException)
        """
        Remember the current stack and queue for backtracking
        """
        dtr = stack[i]
        hd = queue[0]
        if islist(d):
            d = d[0]
        r = RELATION(hd.position, dtr.position, d)
        action = ACTION(STATE.leftArc, r.rel, offset=i)
        self.before(action, "Before leftArc(%s, '%s', %s): %s"%(r.hd, r.rel, r.dtr, i))
        self.relations[r.dtr] = r
        self.stack = [x for x in stack if not x == dtr]
        self.after("After leftArc(%s, '%s', %s): %s"%(r.hd, r.rel, r.dtr, i))
        return self

    """
    Top item on the stack is head of the i'th item in the queue

    Shift it back to the queue
    """
    def rightArc(self, d="unknown", i=0, warnings=True, throwException=False):
        queue = self.queue
        stack = self.stack
        if len(queue) <= i:
            return self.warn(warnings, "Can't call rightArc(%s) with queue of length %s"%(i, len(queue)), throwException=throwException)
        if self.stack == []:
            return self.warn(warnings, "Can't call rightArc with empty stack", throwException=throwException)
        hd = stack[0]
        dtr = queue[i]
        if islist(d):
            d = d[0]
        r = RELATION(hd.position, dtr.position, d)
        action = ACTION(STATE.rightArc, r.rel, offset=i)
        self.before(action, "Before rightArc(%s, '%s', %s): %s"%(r.hd, r.rel, r.dtr, i))
        self.relations[r.dtr] = r
        self.queue = [hd]+[x for x in queue if not x == dtr]
        self.stack = self.stack[1:]
        self.after("After rightArc(%s, '%s', %s): %s"%(r.hd, r.rel, r.dtr, i))
        return self

    def undo(self):
        if self.actions == []:
            print 'No more commands to undo'
            return False
        last = self.actions.pop().fn.__name__
        verbatim("Undo %s"%(last), underline=True, silent=SILENT)
        self.queue = self.oldqueues.pop()
        self.stack = self.oldstacks.pop()
        """
        undo leftArc: leftArc added a relation !!!!!
        """
        if last == "leftArc":
            del self.relations[self.stack[0].position]
        if last == "rightArc":
            del self.relations[self.queue[0].position]
        self.showState()
        return self

    """
    A state is a terminal state if there's nothing on the queue and
    one item on the stack
    """
    def terminal(self):
        return self.queue == [] and len(self.stack)==1

    def latex(self, outfile=sys.stdout):
        with safeout(outfile) as write:
            for word in self.words:
                write("\\rnode{c%s}{%s}\n"%(word.position, word.form))
            for r in self.relations.values():
                write("\\nccurve[nodesepB=10pt,angleA=90,angleB=90,arrowscale=2]{->}{c%s}{c%s}\n"%(r.hd, r.dtr))
    
class RELATION:

    def __init__(self, hd, dtr, rel="unknown"):
        if rel == False:
            raise Exception("%s %s"%(hd, dtr))
        if not type(hd) == "int":
            raise Exception("hd of relation should be int: %s"%(hd))
        if not type(dtr) == "int":
            raise Exception("dtr of relation should be int: %s"%(dtr))
        self.hd = hd
        self.dtr = dtr
        self.rel = rel

    def __repr__(self):
        return "%s >%s> %s"%(self.hd, self.rel, self.dtr)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)
  
class ACTION:

    def __init__(self, fn, arg=False, pattern=[], offset=0):
        self.fn = (lambda c: fn(c, self.arg, self.offset))
        self.fn.__name__ = fn.__name__
        self.name = fn.__name__
        self.arg = arg
        self.offset = offset

    def __repr__(self):
        if self.arg:
            return 'ACTION(%s, %s, %s)'%(self.name, self.offset, self.arg)
        else:
            return 'ACTION(%s, %s)'%(self.name, self.offset)

class PATTERN:

    def __init__(self, p):
        self.pattern = re.compile(p)

    def __repr__(self):
        return "<%s>"%(self.pattern.pattern)

    def match(self, s):
        return self.pattern.match(s)
        
class RULE:

    def __init__(self, queue=[], stack=[], action=False):
        self.pattern = False
        self.action = action
        self.setPattern(queue, stack)

    def __repr__(self):
        return "%s ==> %s"%(self.pattern, self.action.__name__)

    def match(self, s):
        return self.pattern.match(s)

    """
    Turn the elements of a pattern into compiled regexes
    """
    def setPatternComponent(self, l0):
        l1 = []
        for x in l0:
            if x == '???':
                l1.append(x)
            else:
                w = WORD(form=".*", tag=".*")
                if 'form' in x and x['form']:
                    w.form = x['form']
                if 'pos' in x and x['pos']:
                    w.tag = x['pos']
                w.form = PATTERN(w.form)
                w.tag = PATTERN(w.tag)
                l1.append(w)
        return l1
    
    def setPattern(self, queue0, stack0):
        self.pattern = STATE(queue=self.setPatternComponent(queue0),
                             stack=self.setPatternComponent(stack0))

def dtree2state(tree, top=True):
    relns = dtree2relns(tree.dtree)
    state = STATE()
    state.words = [word for word in tree.leaves if type(word.position) == 'int' and not word.tag == "NONE"]
    state.queue = state.words
    return state, relns

def dtree2relns(tree, relns=False):
    if relns == False:
        relns = {}
    hd = tree[0]
    for dtr in tree[1:]:
        relns[dtr[0].position] = RELATION(hd.position, dtr[0].position, dtr[0].label)
        dtree2relns(dtr, relns)
    return relns

"""
regexes for reading rules and extracting patterns
"""
        
wdtagpattern = re.compile("{(((pos:\s*(?P<pos>[^},]*))|(form:\s*(?P<form>[^},]*)))\s*,?\s*)*}|\?\?\?")
rulepattern = re.compile("\[(?P<queue>.*)\]\s*:\s*\[(?P<stack>.*)\]\s*==>\s*(?P<action>.*);")
actionpattern = re.compile("\s*(?P<action>[a-zA-Z]*)(?P<args>(\(.*\))?)\s*")
argpattern = re.compile('[^\(\),\s]+')

def makeWord(m):
    if m.group(0) == '???':
        return '???'
    elif m.group(0) == '{}':
        return {}
    else:
        return {'form':m.group('form'), 'pos':m.group('pos')}
    
def makeWords(words):
    return [makeWord(m) for m in wdtagpattern.finditer(words)]

"""
This is fairly complex: do the match encoded in the
action, dig out the group that was matched, stick this in a string
with a name like "state.leftShift" and use that to construct a closure
that can be applied to a state. But doing complex things when you
read a ruleset in order to have an efficient way of applying it is
a good idea, so I wasn't just showing off when I did it this way,
it is actually quite neat.
"""

def makeAction(action):
    action = actionpattern.match(action)
    f0 = eval('STATE.'+action.group("action"))
    args = [m.group(0) for m in argpattern.finditer(action.group('args'))]
    f = lambda x: f0(x, args)
    f.__name__ = '%s%s'%(action.group("action"), action.group("args"))
    return f

def convertRules(s):
    rules = [RULE(makeWords(m.group('queue')), makeWords(m.group('stack')), makeAction(m.group('action'))) for m in rulepattern.finditer(s)]
    return rules

def readRules(rules="%s/maltrules"%(programs)):
    return readRules1(open(rules, 'r').read())

def readRules1(rules):
    rules = convertRules(rules)
    for x in rules:
        print x
    return rules

"""
Here's where the complex bit of code above pays off: when you
find the rule that matches your situation you've got a function
which can be applied directly to a state--no lookup, no nothing:
just do it
"""
def chooseAction(s, rules):
    for r in rules:
        if r.pattern.match(s):
            print "%s chosen"%(r)
            return r.action
    return False

"""
So here's the parser: dead simple, because of the work we did earlier.
chooseAction is itself pretty simple, because we compile the patterns
and actions, and parse is just "(i) choose action, (ii) do it. 
"""

def parse(s, rules, tagger=brilltagger):
    if not s.__class__.__name__ == 'state':
        s = STATE(s, tagger=tagger)
    s.showState()
    while not(s.terminal()):
        a = chooseAction(s, rules)
        if not a:
            break
        a(s)
    return s
