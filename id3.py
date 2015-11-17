"""
Programs to support COMP34411 Natural Language Systems: these programs
have more comments in them than code that I write for my own use, but
it's unlikely to be enough to make them easy to understand. If you
play with them then I hope they will help with understanding the ideas
and algorithms in the course. If you try to read the source code,
you'll probably just learn what a sloppy programmer I am.

Reimplementation of ID3 for COMP34411 Natural Language Systems.

There are numerous implementations of ID3 around, including in the
scipy.sklearn package. I have little doubt that they all have have
advantages over what I've done here, but this one does have one major
advantage: I understand the format of the final decision tree
tables. I can't find anything in the sklearn documentation which
enables me to get the tables out--I just get a black-box classifier,
and I can't work with black boxes.

The sklearn version also has the disadvantage that it's set up to take
numerical data, and you have to go for a very weird encoding to get it
to accept categorical data. And since the data I want to use is
categorical, I would have to carry out this weird encoding (and then decode
the answer).

So I've written this one, because I do at least understand it. I found
http://www.cise.ufl.edu/~ddd/cap6635/Fall-97/Short-papers/2.htm very
helpful, though the code here has very little in common with the
pseudo-code there.

Allan Ramsay, October 2014

Some of this code is quite neat. Some is a bit clumsy. The clumsy bit
is that I make a decision tree by incrementally choosing features to
split on, and then I make a classifier by extracting question:answer
tables from the tree. If I'd been better organised I might have been
able to do it all in one go. But I wasn't better organised, and it's
too much effort now to try to rewrite it. The classifier, which is the
bit where you really need efficiency, is very efficient, so I'm happy
enough with what I've done.
"""

import numpy as np
from useful import *

def showtable(t):
     s = "{"
     for x in t:
          s += "%s:%.3f, "%(x, t[x])
     return s[:-2]+"}"

class ANSWERTABLE:

     """
     An ANSWERTABLE consists of a question and a table of
     answers, where an answer is either an answertable or a leaf table.

     They are used for classifying instances, where an instance
     contains a feature-value table where the features are potential
     answers to the question and the answers are either ANSWERTABLEs or
     leaftables. You classify an instance by looking up the question in
     its F-V table, and then asking the ANSWERTABLE/leaftable that for
     the value that the question has in the instance to classify it.

     The ANSWERTABLE for the example given in
     http://www.cise.ufl.edu/~ddd/cap6635/Fall-97/Short-papers/2.htm
     looks like

        outlook?
         -> Overcast
            {'Yes': 4}
         -> Sunny
            humidity?
             -> High
                {'No': 3}
             -> Normal
                {'Yes': 2}
         -> Rain
            wind?
             -> Strong
                {'No': 2}
             -> Weak
                {'Yes': 3}

     In other words, the first question asks for the vale of
     outlook. If the answer to this question in the instance being
     classified is 'Sunny', it asks about humidity. If the answer to
     this in the instance is 'High', it returns {'No': 3}, i.e. there
     were 3 'No' instances down this path and no 'Yes's. It can happen
     that there is a mixture, in which case you most likely want to take
     the commonest one.

     For the instance {'outlook':'Sunny','temperature':'Hot','humidity':'High','wind':'Weak'}
     it will say 'No'. Start by asking about Outlook, answer is
     'Sunny'. So ask about humidity, the answer is 'High'. So leaf node
     is {'No': 3}
     """

     def __init__(self, question, answers):
          self.question = question
          self.answers = answers

     def __repr__(self):
          return "<id3.ANSWERTABLE> (use print x.show(maxlines=50) to see it properly)"

     def show(self, indent='', maxlines=False):
          s = "\n%s?%s=???"%(indent, self.question)
          for x in self.answers:
               s += "\n%s -> %s%s"%(indent, x, self.answers[x].show(indent+'    '))
          try:
               s += "\n%s -> %s"%(indent, showtable(self.default))
          except:
               pass
          if indent == '' and maxlines:
              s = "\n".join(s.split("\n")[:maxlines])
          return s

     def normalise(self):
          normalise(self.default)
          for a in self.answers:
               self.answers[a].normalise()

     def classify(self, i, printing=False, indent=''):
          a = i.fvtable[self.question]
          if printing:
               print "%s%s=%s"%(indent, self.question, a)
          if a in self.answers:
               return self.answers[a].classify(i, printing=printing, indent=indent+"  ")
          else:
               return self.default

     def setdefaults(self):
          d = {}
          for x in self.answers:
               x = self.answers[x]
               merge(d, x.setdefaults())
          self.default = d
          return d

     def testclassifier(self, data):
          right = 0
          wrong = 0
          classification = {}
          if type(data) == "DATASET":
               data = data.instances
          for i in data:
               target = i.fvtable['A']
               classified = getBest(self.classify(i))
               state = str(sorted([(k, i.fvtable[k]) for k in i.fvtable if not k=='A']))
               if not state in classification:
                    classification[state] = {"right":0, "wrong":0, "classified":{}, "target":{}}
               if target == classified:
                    right += 1
                    classification[state]["right"] += 1
               else:
                    wrong += 1
                    classification[state]["wrong"] += 1
               try:
                    classification[state]["classified"][classified] += 1
               except:
                    classification[state]["classified"][classified] = 1
               try:
                    classification[state]["target"][target] += 1
               except:
                    classification[state]["target"][target] = 1
          self.data = data
          self.classification = classification
          self.right = right
          self.wrong = wrong
          self.accuracy = float(right)/float(right+wrong)

     def size(self):
          return 1+sum([self.answers[d].size() for d in self.answers])

def getWorstDecisions(c):
     c = c.classification
     d = []
     for k in c:
          rw = c[k]
          if rw['wrong'] > rw['right']:
               d.append((rw['wrong']-rw['right'], k, rw))
     return sorted(d)

def getBest(table):
     n = "unknown"
     for k in table:
          if n == "unknown":
               n = table[k]
               best = k
          elif table[k] > n:
               n = table[k]
               best = k
     return best

def merge(d0, d1):
     for x in d1:
          if x in d0:
               d0[x] += d1[x]
          else:
               d0[x] = d1[x]
               
class LEAFTABLE(ANSWERTABLE):

     """
     LEAFTABLEs are simpler than ANSWERTABLEs. You get to a LEAFTABLE if there are no
     more questions to ask. In which case you already know the answer.
     """
    
     def __init__(self, answer):
          self.answer = answer

     def __repr__(self):
          return "<id3.LEAFTABLE> (use print x.show() to see it properly)"
        
     def show(self, indent=''):
          return "\n%s%s"%(indent, showtable(self.answer))

     def classify(self, i, printing=False, indent=''):
          if printing:
               print '%s%s'%(indent, self.answer)
          return self.answer

     def normalise(self):
          normalise(self.answer)
   
     def setdefaults(self):
          self.default = self.answer
          return self.default

     def size(self):
          return 1

class DTREE:

     """
     A DTREE has a question (which is the feature that was used for splitting
     when it was constructed), an answer (which is the specific value of that
     feature which was used for the set of instances cover by this tree) and a
     set of subtrees.
     """
     def __init__(self, question, answer, subtrees=[]):
          self.question = question
          self.answer = answer
          self.subtrees = subtrees

     """
     answertree is used for converting a DTREE into an ANSWERTABLE: note that
     all the subtrees of a given tree will have the same name, so what we're
     doing here is promoting the question from the next level down and using all
     the potential answers as keys into a table.
     """

     def answertree(self):
          answers = {}
          for x in self.subtrees:
               answers[x.answer] = x.answertree()
          return ANSWERTABLE(x.question, answers)
        
     def __repr__(self):
          return "DTREE(%s, %s)"%(self.question, self.subtrees)

     def show(self, indent=''):
          s = self.question
          for a in self.answers:
               s += "\n%s%s: %s%s"%(indent+'    ', a, self.answers[a].show(indent+'    '))
          return s
        
class INSTANCE:

    """
    An INSTANCE is basically a set of feature:value pairs. We also keep the
    actual list of features because we sometimes need to go through them in
    the order in which they were specified in the table. So this is just a
    table of feature:value pairs and a list of features
    """
    
    def __init__(self, features, values):
        self.fvtable = {}
        self.features = features
        for f, v in zip(features, values):
            self.fvtable[f] = v

    def __repr__(self):
        s = "{"
        for f in self.features:
            s += "'%s':'%s',"%(f, self.fvtable[f])
        return s[:-1]+"}"

class DATASET:

    """
    A DATASET is a set of INSTANCEs. A DATASET may be constructed by splitting
    a larger DATASETs into pieces, in which case each child has a question (the
    feature that was used for splitting it) and an answer (the value that the
    question had for this split).

    We assume that final column in a set of INSTANCEs is the classification.
    """

    def __init__(self, instances, q=False, a=False):
        self.instances = instances
        self.features = instances[0].features
        self.question = q
        self.answer = a
        self.targetClass = self.features[-1]

    def __repr__(self):
        if self.question:
            return "DATASET(%s->%s)"%(self.question, self.answer)
        return "DATASET(%s)"%(self.instances)

    def show(self, indent=''):
        classes = self.splitOnF(self.targetClass)
        return '%s'%([(x.answer, len(x.instances)) for x in classes])

    """
    splitOnF partitions a DATASET into a set of DATASETs grouped on the value
    of f:
    
    >>> for x in data.splitOnF("outlook"): print "%s\n   %s\n"%(x, x.instances)
    
      DATASET(outlook->Overcast)
         [{'outlook':'Overcast','temperature':'Hot','humidity':'High',
          'wind':'Weak','C':'Yes'}, {'outlook':'Overcast','temperature':'Cool',
          'humidity':'Normal','wind':'Strong','C':'Yes'},
          {'outlook':'Overcast','temperature':'Mild','humidity':'High',
          'wind':'Strong','C':'Yes'}, {'outlook':'Overcast',
          'temperature':'Hot','humidity':'Normal','wind':'Weak','C':'Yes'}]
      
      DATASET(outlook->Sunny)
         [{'outlook':'Sunny','temperature':'Hot','humidity':'High',
         'wind':'Weak','C':'No'}, {'outlook':'Sunny','temperature':'Hot',
         'humidity':'High','wind':'Strong','C':'No'}, {'outlook':'Sunny',
         'temperature':'Mild','humidity':'High','wind':'Weak','C':'No'},
         {'outlook':'Sunny','temperature':'Cool','humidity':'Normal',
         'wind':'Weak','C':'Yes'}, {'outlook':'Sunny','temperature':'Mild',
         'humidity':'Normal','wind':'Strong','C':'Yes'}]
      
      DATASET(outlook->Rain)
         [{'outlook':'Rain','temperature':'Mild','humidity':'High',
         'wind':'Weak','C':'Yes'}, {'outlook':'Rain','temperature':'Cool',
         'humidity':'Normal','wind':'Weak','C':'Yes'}, {'outlook':'Rain',
         'temperature':'Cool','humidity':'Normal','wind':'Strong','C':'No'},
         {'outlook':'Rain','temperature':'Mild','humidity':'Normal',
         'wind':'Weak','C':'Yes'}, {'outlook':'Rain','temperature':'Mild',
         'humidity':'High','wind':'Strong','C':'No'}]
    """
    def splitOnF(self, f):
        splits = {}
        for i in self.instances:
            v = i.fvtable[f]
            try:
                splits[v].append(i)
            except:
                splits[v] = [i]
        return [DATASET(splits[s], f, s) for s in splits]
    
    """
    justCountSplitOnF just counts how long each DATASET would have been
    without actually constructing it (saves space)
    """
    def justCountSplitOnF(self, f):
        splits = {}
        for i in self.instances:
            v = i.fvtable[f]
            try:
                splits[v] += 1.0
            except:
                splits[v] = 1.0
        return splits

    """
    entropy: look it up
    """
    def entropy(self):
        E = 0
        t = float(len(self.instances))
        for c in self.justCountSplitOnF(self.targetClass).values():
            e = c/t
            E -= e*np.log2(e)
        return E

    """
    gain: look it up
    """
    def gain(self, f):
        g = self.entropy()
        if g == 0.0:
            return False
        n = float(len(self.instances))
        for s in self.splitOnF(f):
            g -= len(s.instances)/n*s.entropy()
        return g

    def chooseFeatureToSplit(self, features, indent=''):
        maxgain = 0
        bestFeature = False
        for f in features:
            if features[f]:
                g = self.gain(f)
                if g and g > maxgain:
                    bestFeature = f
                    maxgain = g
        return bestFeature

    def id3(self, features=False, indent='', showprogress=False):
         if features == False:
              features = list2table(self.features[:-1])
         if self.instances == [] or features == []:
              return self
         if showprogress:
              if self.answer:
                   print "%ssplitting at level %s, answer=%s"%(indent, len(indent)/2, self.answer)
              else:
                   print "%ssplitting at level %s"%(indent, len(indent)/2)
         f = self.chooseFeatureToSplit(features, indent)
         if not f:
              return self
         if showprogress:
              print "%s%s chosen"%(indent, f)
         """
         This is a neat way of removing f from the set of features
         under consideration without copying the list
         """
         features[f] = False
         dtrs = []
         for d in self.splitOnF(f):
              dtrs.append(d.id3(features=features, indent=indent+'  ', showprogress=showprogress))
         """
         Now make f available for consideration again (so you can use
         it when you go back up the recursion tree to consider a different
         branch)
         """
         features[f] = True
         d = DTREE(self.question, self.answer, dtrs)
         if indent == '':
              d = d.answertree()
              d.setdefaults()
              d.normalise()
              d.features = features
              return d
         else:
              return d

    def answertree(self):
        answers = {}
        for c in self.splitOnF(self.targetClass):
            answers[c.answer] = len(c.instances)
        return LEAFTABLE(answers)

    def show(self):
        s = ""
        for x in self.features:
            s += "%s,"%(x)
        for i in self.instances:
            s += "\n"
            for f in self.features:
                s += "%s,"%(i.fvtable[f])
        return s
        
def list2table(l):
    t = {}
    for x in l:
        t[x] = True
    return t

"""
For reading training data from a .CSV file
"""
def csvstring2data(s, separator=",", start=0, end=100000000000):
    featuretable = {}
    featurelist = []
    rawdata = []
    for row in s.splitlines()[start:end]:
        if featurelist == []:
            featurelist = ["F%s"%(i) for i in range(len(row.strip().split(separator))-1)]+["A"]
            for f in featurelist:
                featuretable[f] = {}
        else:
            row = row.strip()
            if row == "":
                continue
            row = [x.strip() for x in row.split(separator)]
            rawdata.append(INSTANCE(featurelist, row))
            for x, f in zip(row, featurelist):
                f = featuretable[f]
                if not x in f:
                    f[x] = len(f)
    return DATASET(rawdata)

def csvfile2data(f="ptbtraining.tsv", separator="\t", start=0, end=1000000000):
     return csvstring2data(open(f).read(), separator=separator, start=start, end=end)


    
