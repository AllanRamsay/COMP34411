
def getWordList(ifile="lemma.al.txt"):
    tags = {"n":"[nroot, noun]", "v":"[vroot, tverb]"}
    tags = {"a":"[aroot, adj]"}
    words = []
    for line in open(ifile):
        [a, b, c, d] = line.strip().split(" ")
        if d in tags:
            words.append((d, c))
    words.sort()
    for d, c in words:
        print "%s ## %s."%(c, tags[d])
