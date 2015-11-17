
HD = 0
TL = 1
KEY = 0
VALUE = 1

vcounter = 0

class var:

    def __init__(self):
	global vcounter
	self.name = str(vcounter)
	vcounter = vcounter+1

    def __str__(self):
	return '<'+self.name+'>'

    def __repr__(self):
	return str(self)

class dag:

    def __init__(self, list):
	b = {}
	if list == []:
	    self.list = []
	else:
	    x = list[HD]
	    l = auxSetPath(x[0], x[1], b)
	    for x in list:
		l = merge(l, auxSetPath(x[0], x[1], b), b)
	    self.list = l
	# self.list = [doAuxsetPath(x[0], x[1], b) for x in list]

    def __str__(self):
	s = '[:'
	l = self.list
	for i in range(0, len(l)):
	    s = s+str(l[i])
	    if i < len(l)-1:
		s = s+', '
	return s+':]'

    def __repr__(self):
	return str(self)

    def unify(self, other):
	return UNIFY(self, other)

    def addPath(self, path, value):
	return UNIFY(self, setPath(path, value))

    def getPath(self, path):
	return auxGetPath(path, self.list)

class keyvalpair:

    def __init__(self, key, value):
	self.key = key
	self.value = value

    def __str__(self):
	return str(self.key)+'->'+str(self.value)

    def __repr__(self):
	return str(self)

def makeDag(l):
    d = dag(l)
    return d

def sort(x):
    return x.__class__.__name__ 

def uc(x):
    return x >= 'A' and x <= 'Z'

def isvarString(x):
    return sort(x) == 'str' and len(x) > 0 and uc(x[HD])

def isvar(x):
    return sort(x) == 'var'

def iskeyvalpair(x):
    return sort(x) == 'keyvalpair'

def islist(x):
    return sort(x) == 'list'

def isdag(x):
    return sort(x) == 'dag'

def conv2dag(x):
    return doconv2dag(x, {})

def doconv2dag(x, b):
    if islist(x):
	return [doconv2dag(y, b) for y in x]
    elif iskeyvalpair(x):
	return keyvalpair(x.key, doconv2dag(x.value, b))
    elif isvarString(x):
	if not(x in b):
	    b[x] = var()
	return b[x]
    else:
	return x

def lookup(k, b):
    if isvar(k) and k in b:
	return lookup(b[k], b)
    else:
	return k

def bind(x0, x1, b={}):
    if isvar(x0):
	x0 = lookup(x0, b)
    if isvar(x1):
	x1 = lookup(x1, b)
    if x0 == x1:
	return [b]
    if isvar(x0):
	b[x0] = x1
	return [b]
    if isvar(x1):
	b[x1] = x0
	return [b]
    if islist(x0):
	return islist(x1) and bindLists(x0, x1, b)
    if x0 == x1:
	return [b]

def bindLists(l0, l1, b):
    while not(l0 == []) and not(l1 == []):
	x0 = l0[HD]
	x1 = l1[HD]
	k0 = x0.key
	k1 = x1.key
	if k0 == k1:
	    if not(bind(x0.value, x1.value, b)):
		return False
	    l0 = l0[TL:]
	    l1 = l1[TL:]
	elif k0 < k1:
	    l0 = l0[TL:]
	else:
	    l1 = l1[TL:]
    return [b]

def merge(x0, x1, b):
    if isvar(x0):
	v0 = lookup(x0, b)
	if isvar(v0):
	    if v0 in b:
		v = var()
		b[v0] = v
		return v
	    else:
		return v0
	else:
	    x0 = v0
    if isvar(x1):
	v1 = lookup(x1, b)
	if isvar(v1):
	    if v1 in b:
		v = var()
		b[v1] = v
		return v
	    else:
		return v1
	else:
	    x1 = v1
    if isdag(x0) and isdag(x1):
	x = mergeLists(x0.list, x1.list, b)
	return dag(x)
    if isdag(x1):
	x1 = x1.list
    if islist(x0) and islist(x1):
	return mergeLists(x0, x1, b)
    elif x0 == x1:
	return x0
    else:
	throw(str(x0)+'\='+str(x1))

def mergeLists(l0, l1, b):
    l = []
    while not(l0==[]) and not(l1==[]):
	x0 = l0[HD]
	x1 = l1[HD]
	k0 = x0.key
	k1 = x1.key
	if k0 == k1:
	    x = merge(x0.value, x1.value, b)
	    l.append(keyvalpair(k0, x))
	    l0 = l0[TL:]
	    l1 = l1[TL:]
	elif k0 < k1:
	    l.append(keyvalpair(x0.key, instantiate(x0.value, b)))
	    l0 = l0[TL:]
	else:
	    l.append(keyvalpair(x1.key, instantiate(x1.value, b)))
	    l1 = l1[TL:]
    return l+instantiateList(l0, b)+instantiateList(l1, b)

def instantiateList(l, b):
    return [keyvalpair(x.key, instantiate(x.value, b)) for x in l]

def instantiate(x, b):
    if isvar(x):
	x = lookup(x, b)
	if isvar(x):
	    return x
	else:
	    return instantiate(x, b)
    elif islist(x):
	return instantiateList(x, b)
    else:
	return x
	
def UNIFY(x, y):
    b = {}
    if bind(x.list, y.list, b):
	d = dag([])
	d.list = merge(x.list, y.list, b)
	return d
    else:
	return False

def auxSetPath(path, value, b=False):
    if sort(b) == 'Bool':
	b = {}
    if len(path)==1:
	return [keyvalpair(path[HD], doconv2dag(value, b))]
    else:
	return [keyvalpair(path[HD], auxSetPath(path[TL:], value, b))]

def setPath(path, value):
    return dag(auxSetPath(path, value))
	
def getKey(key, l):
    for x in l:
	if x.key == key:
	    return x.value
    raise Exception("No such key as '"+str(key)+"' in "+str(l))

def auxGetPath(path, dag):
    x = getKey(path[HD], dag)
    if len(path) == 1:
	return x
    else:
	return auxGetPath(path[TL:], x)

def sharePaths(paths):
    v = var()
    dags = [setPath(path, v) for path in paths]
    return unifyPaths(dags)

def unifyPaths(paths):
    p0 = paths[HD]
    for p1 in paths[TL:]:
	p0 = UNIFY(p0, p1)
	if not(p0):
	    return False
    return p0
