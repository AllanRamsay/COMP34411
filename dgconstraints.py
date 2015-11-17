import re, sys

descrPattern = re.compile("\s*\[(?P<descr>.*?)\],\s*(?P<rest>.*)", re.DOTALL)

class DESCRIPTOR:

    def __init__(self, elements):
        self.keys = set(self.elements.keys())

    def __repr__(self):
        return "%s"%(self.elements)

    def unify(self, other):
        u = {}
        keys0 = self.keys
        keys1 = other.keys
        elements0 = self.elements
        elements1 = other.elements
        for k in keys0.intersection(keys1):
            v = unify(elements0[k], elements1[k])
            if not v:
                return False
            u[k] = v
        for k in keys0.difference(keys1):
            u[k] = elements0[k]
        for k in other.keys.difference(self.keys):
            u[k] = self.elements[k]
        return DESCRIPTOR(u)

class VARIABLE(DESCRIPTOR):

    def __init__(self, name):
        self.name = name
        self.value = "???"

    def __repr__(self):
        return "%s(=%s)"%(self.name, self.value)
            
def readDescriptor(s):
    m = descrPattern.match(s)
    return re.compile(";\s*").split(m.group("descr")), m.group("rest").strip()

rulePattern = re.compile("\s*(?P<lhs>.*?)\s*==>\s*(?P<rhs>\S*\s*>\s*\S*)\s*;\s*(?P<rest>.*\S)\s*", re.DOTALL)
def readRule(s):
    m = rulePattern.match(s)
    return m.group("lhs"), m.group("rhs"), m.group("rest")

"""
A rule looks like

QUEUE+STACK 
"""
test= """
[a=7;b=?X; +c]: ==> X>Y;
[p, q,r] ==> P>Q;
"""
