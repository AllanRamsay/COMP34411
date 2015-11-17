import re

avpattern = re.compile("""average accuracy over all folds \(precision = 1\): (?P<avparse>0.\d+)
average classifier accuracy (?P<avclsf>0.\d+)""", re.DOTALL)

sizePattern = re.compile("len\(training\) (?P<len>\d+),")

def plot(ifile):
    s = 0
    sizes = []
    ifile = open(ifile).read()
    for i in sizePattern.finditer(ifile):
        t = i.group("len")
        if not t == s:
            sizes.append(t)
            s = t
    averages = []
    for i in avpattern.finditer(ifile):
        averages.append("%s\t%s"%(i.group("avparse"), i.group("avclsf")))
    for a, b in zip(sizes, averages):
        print "%s\t%s"%(a, b)
