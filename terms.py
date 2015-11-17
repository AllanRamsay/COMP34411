import re, sys, os
from readrules import ops
from useful import *

def proving(INDENT, functor, args, rule):
    print '%s%s%s using %s'%(INDENT, functor, args, rule)
    return True

def failed(INDENT, functor, args):
    print '%s%s%s failed'%(INDENT, functor, args)
    return False

class TermException(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "TermException(%s)"%(self.msg)
    
vpattern = re.compile("(?P<VNAME>[A-Z]\w*)")

def toList(x):
    try:
        return x.toList()
    except:
        return x


class TERM:

    def __init__(self, functor, args=[]):
        if functor.islower():
            self.functor = "%s%s"%(functor, len(args))
        else:
            self.functor = functor
        self.args = args
        self.consequent = self
        self.antecedent = []

    def __repr__(self):
        if self.args == []:
            return self.functor
        elif self.functor in ops:
            return "%s %s %s"%(str(self.args[0]), self.functor, str(self.args[1]))
        else:
            return "%s(%s)"%(self.functor, ", ".join([str(x) for x in self.args]))
        
    def __str__(self):
        return self.__repr__()

    def __call__(self, contn):
        print eval("%s"%(self.functor))

    """
    If one of the arguments of the head is a complex term,
    you have to replace it by a variable which is unified
    with that term. Arguments of the head that are just
    variables can be left as they are.

    If one of the arguments of a subgoal is a complex term,
    you simply call the subgoal with that item as the
    argument
    """
    
    def defn(self):
        x = str(self.toList())
        allvars = {i.group("VNAME"):True for i in vpattern.finditer(x)}
        args = []
        argsv = {}
        vinitials = ""
        i = 0
        for arg in self.consequent.args:
            if type(arg) == "VARIABLE":
                args.append(arg.functor)
            else:
                v = "_V%s_"%(i)
                args.append(v)
                try:
                    argsv[v] = vpattern.sub("\g<VNAME>", str(arg.toList()))
                except:
                    argsv[v] = arg
                i += 1
        for v in allvars:
            if not v in args:
                w = "_V%s_"%(i)
                i += 1
                vinitials += "\n    %s = VARIABLE('%s')"%(v, w)
        keys = sorted(argsv.keys())
        if keys == []:
            unifiers = self.subgoals("CONTN")
        elif len(keys) == 1:
            unifiers = "unify(%s, %s, %s, INDENT)"%(keys[0],argsv[keys[0]], self.continuation("CONTN"))
        else:
            unifiers = "unify(["
            for a in keys:
                unifiers += "%s, "%(a)
            unifiers += "], ["
            for a in keys:
                unifiers += "%s, "%(argsv[a])
            unifiers += "], %s, INDENT)"%(self.continuation("CONTN"))
        args = ",".join(args)
        if not args == "":
            args += ","
        return """def %s((%s), CONTN, INDENT, RULES):%s
    proving(INDENT, "%s", (%s), "%s ==> %s")
    %s
    failed(INDENT, "%s", (%s))
"""%(self.consequent.functor, args, vinitials, self.consequent.functor, args, self.antecedent, self.consequent, unifiers, self.consequent.functor, args)
    
    def subgoals(self, contn):
        args = ", ".join([vpattern.sub("\g<VNAME>", str(toList(a))) for a in self.args])
        return "RULES['%s']((%s,), %s, INDENT+' ', RULES)"%(self.functor, args, contn)

    def continuation(self, contn):
        return contn

    def deref(self):
        args = []
        for a in self.args:
            try:
                args.append(a.deref())
            except:
                args.append(a)
        return TERM(self.functor, args)
            
    def toList(self):
        args = []
        for arg in self.args:
            try:
                args.append(arg.toList())
            except:
                args.append(arg)
        return [self.functor]+args
    
class CONJUNCTION(TERM):

    def __init__(self, functor, args):
        TERM.__init__(self, functor, args)
        self.conj1 = args[0]
        self.conj2 = args[1]
    
    def subgoals(self, contn):
        return "%s"%(self.conj1.subgoals("lambda : %s"%(self.conj2.subgoals(contn))))

class RULE(TERM):

    def __init__(self, functor, args):
        TERM.__init__(self, functor, args)
        self.antecedent = args[0]
        self.consequent = args[1]
    
    def subgoals(self, contn):
        return self.antecedent.subgoals(contn)

    def continuation(self, contn):
        return "lambda : %s"%(self.subgoals(contn))
        
class VARIABLE(TERM):

    def __init__(self, functor):
        TERM.__init__(self, functor)
        self.value = "???"
        
    def __repr__(self):
        d = self.deref()
        try:
            return d.functor
        except:
            return str(d)
        
    def subgoals(self, contn):
        raise TermException("Cannot use variable as subgoal: %s"%(self.functor))

    def toList(self):
        return self

    def deref(v):
        while type(v) == "VARIABLE" and not v.value == "???":
            v = v.value
        return v
        
class ATOM(TERM):

    def __init__(self, functor):
        TERM.__init__(self, functor)
        
    def subgoals(self, contn):
        return "%s"%(contn)

    def toList(self):
        return self.functor

def deref(t):
    while type(t) == "VARIABLE":
        if t.value == "???":
            return t
        t = t.value
    return t

class SUCCESS(Exception):

    def __init__(self, msg):
        self.msg = msg
        pass
    
def tryit(c):
    try:
        c()
    except SUCCESS as e:
        raise e
    except Exception as e:
        return e
    
def unify(t1, t2, cont, INDENT):
    t1 = deref(t1)
    t2 = deref(t2)
    # print "unify(%s (%s), %s (%s))"%(t1, type(t1), t2, type(t2))
    if t1 == t2:
        tryit(cont)
    elif type(t1) == "VARIABLE":
        t1.value = t2
        tryit(cont)
        t1.value = "???"
    elif type(t2) == "VARIABLE":
        t2.value = t1
        tryit(cont)
        t2.value = "???"
    elif type(t1) == "TERM" and type(t1) == "TERM" and t1.functor == t2.functor:
        unify(t1.args, t2.args, cont, INDENT)
    elif type(t1) == "list" and type(t2) == "list":
        if len(t1) == len(t2):
            unify(t1[0], t2[0], lambda: unify(t1[1:], t2[1:], cont, INDENT), INDENT)
    return False
    
            
