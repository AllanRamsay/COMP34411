import sys
from useful import *
    
"""
Dynamic time warping: mixture of code for doing it and stuff for
generating pretty LaTeX output from it. The raw algorithm is dead simple--my
LaTeX stuff makes it look horrible.
"""

"""
You can define different ways of calculating the cost of the core
edit operations--EXCHANGE, INSERT and DELETE are functions that you apply
to the two otems beings swapped. Default definitions just return constants.
"""

def EXCHANGE(x, y):
    if x == y:
        return 0
    else:
        return 3
    try:
        x = float(x)
        y = float(y)
        return 3*abs(x-y)/(x+y)
    except:
        try:
            x = float(len(x))
            y = float(len(y))
            return 1.5+1.5*abs(x-y)/(x+y)
        except:
            return 3

def INSERT(x):
    return 2

def DELETE(x):
    return 2
    
"""
Two alternatives that you could use for EXCHANGE: the first one
utilises the fact that in MT strings of similar lengths are more
likely to be mutual translations than ones of different lengths, the
second uses DTW to match the strings themselves, on the grounds that
lots of words are either borrowed or derived from the same other
language, so that mutual translations are actually likely to look
pretty similar.
"""
def matchStrings(s0, s1):
    lens0 = float(len(s0))
    lens1 = float(len(s1))
    if lens0 > lens1:
        return lens0/lens1
    else:
        return lens1/lens0

"""
This isn't the one I used for the notes. ???
"""
def matchStrings1(s0, s1):
    a = array(s0, s1)
    a.showAlignment()
    return (a.last().value)/float(len(s0))+float(len(s1))

def exchdiacritics(x, y):
    if x in "AIU" or y in "AIU":
        return 0
    else:
        return 2

def insertdiacritic(x):
    if x in "AIU":
        return 0
    else:
        return 3

"""
One to use if you're matching arrays of numbers. Two numbers are similar
if their difference is small!
"""
def matchFloats(s0, s1, d=4.0):
    return abs(s0-s1)/float(d)

class link:

    """
    A link connects the points at array[x][y], and may contain
    a back-pointer and a score
    """
    def __init__(self, x, y, array):
        self.x = x
        self.y = y
        self.link = False
        self.value = -1
        self.cost = 0
        self.edit = False
        self.array = array

    def __repr__(self):
        return "(%s,%s,%s,%s,%s)"%(self.x, self.y, self.cost, self.value, self.edit)

    """
    Look to the right, diagonally and down and see if this is better
    predecessor of the place you're looking at than the one you've already
    got (if you have indeed already been there). This is the key operation
    in the wntire algorithm
    """
    def extend(self, dx, dy):
        a = self.array
        array = a.array
        x = self.x+dx
        y = self.y+dy
        if x >= len(a.v1) or y >= len(a.v2):
            return
        av1x = a.v1[x]
        av2y = a.v2[y]
        if dx == 1 and dy == 1:
            edit = 'EXCHANGE'
            if av1x == av2y:
                s = 0
            else:
                s = a.EXCHANGE(av1x, av2y)
        elif dx == 0:
            edit = 'INSERT'
            s = a.INSERT(av2y)
        else:
            edit = 'DELETE'
            s = a.DELETE(av1x)
        other = array[x][y]
        if other.value == -1 or self.value+s < other.value:
            other.cost = s
            other.value = self.value+s
            other.link = self
            other.edit = edit
            
    def transpose(self, dx, dy, TRANSPOSE):
        a = self.array
        array = a.array
        x = self.x+dx
        y = self.y+dy
        if x >= len(a.v1) or y >= len(a.v2):
            return
        if a.v1[self.x+1] == a.v2[y] and a.v1[self.x+1]:
            s = TRANSPOSE
            other = array[x][y]
            if other.value == -1 or self.value+s < other.value:
                intermediate = array[self.x+1][self.y+1]
                intermediate.cost = s
                intermediate.value = self.value+s
                intermediate.link = self
                other.edit = "TRANSPOSE"
                other.cost = s
                other.value = intermediate.value+s
                other.link = intermediate
                other.edit = "TRANSPOSE"

    """
    For tracing back from the end once you've got there
    """
    def getLinks(self):
        if self.link:
            links = self.link.getLinks()
            return links+[(self.x, self.y, self.cost, self.edit)]
        else:
            return [(self.x, self.y, self.cost, self.edit)]

class array:

    """
    An array of links. Set the scoring functions you're going to use
    for this problem.

    Transpose is fairly flaky--I've put it in to show how you can
    extend the basic algorithm to allow for transposition. It gets my
    main example right, but I'm not sure that it will always get
    everything right
    """
    
    def __init__(self, v1, v2, EXCHANGE=EXCHANGE, INSERT=INSERT, DELETE=DELETE, TRANSPOSE=False):
        if v1.__class__.__name__ == "str":
            """
            v1 = "*"+v1+"*"
            v2 = "*"+v2+"*"
            """
        else:
            x = v1[0]
            if isstring(x):
                dummy = "DUMMY"
            else:
                dummy = ("DUMMY")*len(x)
            v1 = [dummy]+v1+[dummy]
            v2 = [dummy]+v2+[dummy]
        self.v1 = v1
        self.v2 = v2
        self.EXCHANGE=EXCHANGE
        self.INSERT=INSERT
        self.DELETE=DELETE
        self.TRANSPOSE = TRANSPOSE
        self.array = [[link(i, j, self) for j in range(0, len(self.v2))] for i in range(0, len(self.v1))]

    """
    Walk through the links, seeing where you can get to and whether this
    is the best way to get there
    """
    def findPath(self, latex=False, out=sys.stdout, bandwidth=False, exchange=False, insert=False, delete=False):
        if exchange:
            self.EXCHANGE = exchange
        if insert:
            self.INSERT = insert
        if delete:
            self.DELETE = delete
        with safeout(out, mode='a') as out:
            self.array[0][0].value = 0
            for j in range(0, len(self.array[0])-1):
                for i in range(0, len(self.array)):
                    if bandwidth and abs(i-j) > bandwidth:
                        continue
                    if latex:
                        out(self.tabular())
                    l = self.array[i][j]
                    l.extend(0, 1)
                    l.extend(1, 1)
                    l.extend(1, 0)
                    if self.TRANSPOSE:
                        l.transpose(2, 2, self.TRANSPOSE)
        return self.array[-1][-1].value
    
    """
    All the rest is for printing things out
    """
    def last(self):
        row = self.array[len(self.array)-1]
        return row[len(row)-1]

    """
    Plain text output
    """
    def show(self):
        s = ''
        for j in range(0, len(self.array[0])):
            for i in range(0, len(self.array)):
                s = s+str(self.array[i][j].value)+' '
            s = s+'\n'
        return s

    """
    LaTeX output!
    """
        
    def tabular(self):
        s = r'\BREAK\VPARA\begin{tabular}{'+('c'*(len(self.array)+1))+'}\n'
        for i in range(0, len(self.v1)):
            s = s+'~~&~~'+str(self.v1[i])
        s = s+'\\\\\n'
        for j in range(0, len(self.v2)):
            s = s+str(self.v2[j])
            for i in range(0, len(self.v1)):
                s = s+r' & \Rnode{n%s%s}{\texttt{%s}}'%(i, j, str(self.array[i][j].value))
            s = s+'\\\\\n'+('&'*len(self.v1))+'\\\\\n'
        s = s+'\\end{tabular}\n'
        for j in range(0, len(self.array[0])):
            for i in range(0, len(self.array)):
                l = self.array[i][j]
                if l.link:
                    if l.edit == "TRANSPOSE":
                        s = s+'\\ncline[linewidth=2pt,nodesep=5pt]{<->}{n%s%s}{n%s%s}\n'%(l.x, l.y, l.link.x, l.link.y)
                    else:
                        s = s+'\\ncline[linewidth=2pt,nodesep=5pt]{->}{n%s%s}{n%s%s}\n'%(l.x, l.y, l.link.x, l.link.y)
        return s

    """
    Textual version of the alignment with *s for inserts and deletes
    """
    def getAlignment(self):
        path = self.last().getLinks()
        alignment = []
        for l in path:
            if l[3] == 'DELETE':
                t = (self.v1[l[0]], '*', l[2])
            elif l[3] == 'INSERT':
                t = ('*', self.v2[l[1]], l[2])
            else:
                x = self.v1[l[0]]
                y = self.v2[l[1]]
                if l[2] == 0:
                    t = (x, y)
                else:
                    t = (x, y, l[2])
            alignment.append(t)
        return alignment[1:-1]

    def showAlignment(self):
        self.findPath()
        return self.getAlignment()

"""
Latex version of the alignment 
"""
def latexAlign(alignment):
    s = """\\begin{table}[cc]\n"""
    for a in alignment:
        s =s+"""%s & %s\\\\\n"""%(a[0], a[1])
    s = s+"""\\end{table}\n"""
    return s
        
"""
" Examples used in the MT lecture "
>>> a = dtw.array([1,2,3,9,10], [1,2, 9, 10, 11])
>>> a = dtw.array(['I', 'hold', 'the', 'post', 'of'], ['Je', 'detiens', 'le', 'poste', 'de'])

or

>>> a = dtw.array([1,2,3,9,10], [1,2, 9, 10, 11], EXCHANGE=matchStrings)
>>> a = dtw.array(['I', 'hold', 'the', 'post', 'of'], ['Je', 'detiens', 'le', 'poste', 'de'], EXCHANGE=matchStrings)

(or similar)

>>> p = a.findPath()
"""

"""
CSV version of the alignment 
"""
def csvalign(alignment, out=sys.stdout):
    if not out == sys.stdout:
        out = open(out, 'w')
    s = ""
    for a in alignment:
        s =s+"""%s,%s\n"""%(a[0], a[1])
    out.write(s)
    if not out == sys.stdout:
        out.close()

