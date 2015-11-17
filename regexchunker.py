import re, sys
import tag
from useful import *
from startservers import startservers

def untitle(s):
    return s.lower()

def tagPattern(p):
    if p.isupper():
        return "\S+///%s"%(p)
    else:
        return "%s///\S+"%(p)

def patchPattern(p):
    if p[0] == "*":
        p = p[1:]
        if p.isupper():
            p = "\S+///(?P<tag>%s)"%(p)
        else:
            p = "%s///(?P<tag>\S+)"%(p)
        return "(?P<target>%s)"%(p)
    else:
        return tagPattern(p)

def readPatch(patch):
    [lhs, rhs] = patch.split("==>")
    lhs = re.compile("\s+").split(lhs.strip())
    if len(lhs) == 1:
        lhs = ["*%s"%(lhs[0])]
    lhs = "\s+".join(map(patchPattern, lhs))
    return (re.compile("(\s+|^)"+lhs+"(\s+|$)"), rhs.strip())

def extracttext(taggedphrase, hd):
    taggedphrase = taggedphrase.split(" ")
    print taggedphrase
    if len(taggedphrase) > 1:
        x = taggedphrase[hd].split("///")
        taggedphrase[hd] = "%s!///%s"%(x[0], x[1])
    return "(%s)"%(re.compile("\s*(?P<form>\S+)///\S+\s*").sub("\g<form>-", " ".join(taggedphrase))[:-1])
    
def compilePattern(pattern):
    pattern = map(lambda x: x.strip(), pattern.split("==>"))
    hd = 0
    lhs = pattern[0].split(" ")
    for i in range(len(lhs)):
        if lhs[i][0] == "*":
            hd = i
            lhs[i] = lhs[i][1:]
    lhs = r"\s+".join(map(tagPattern, lhs))
    return [re.compile(lhs), pattern[1].strip(), hd]

def compilePatterns(patterns):
    return map(compilePattern, patterns)

patches = map(readPatch,[
    "aaa ==> AA",
    "zzz ==> ZZ",
    "emdash ==> MDASH",
    "that ==> THAT",
    "one ==> NN",
    "(hundred|thousand|million) ==> NN",
    "(first|second|third|fourth|fifth|sixth) ==> JJ",
    "*may V. ==> VM",
    "of ==> OF",
    "AA NP *NN(S?) ==> VV",
    "AA *N(N|P) (IN|DT|NN|RB) ==> VV",
    "former ==> JJ",
    "*her (DT|ZZ) ==> NP",
    "- ==> DASH",
    "(!|\,|\?) ==> PU",
    "(she|he|we) *NN ==> VV",
    "DT *VVG ==> JJ",
    "(a|the) *VV ==> NN",
    "s ==> S",
    "let *s ==> NP",
    "i *NN ==> VV",
    "S *VV(\S?) ==> NN",
    "VM *NN ==> VV",])

patterns = compilePatterns([
    "(N.|V.|JJ|IN) DASH *NN ==> NN",
    "(N.|V.|JJ|IN|RB) DASH *VV ==> VV",
    "(N.|V.|JJ|IN|RB) DASH *JJ ==> JJ",
    "very *RB ==> RB",
    "RB *JJ ==> JJ",
    "(JJ|NN) *NN ==> NN",
    "DT *DT ==> DT",
    "too *DT ==> DT",
    "(DT|THAT) *NN ==> NP",
    "DT *JJ ==> NP",
    "DT ==> NP",
    "N(P|N)(S?) S *NN(S?) ==> NP",
    "P(R|N) ==> NP",
    "NN ==> NP",
    "*NP(S?) of NP ==> NP",
    "*NP all ==> NP",])

def patchsub(m, rhs):
    s = m.group(0)
    target = m.group("target")
    tag = m.group("tag")
    return s.replace(target, target.replace(tag, rhs))

def applyPatch(patch, text):
    return patch[0].sub(lambda m: patchsub(m, patch[1]), text)

def patchText(text, patches=patches):
    for patch in patches:
        text = applyPatch(patch, text)
    return text

INFLECTIONS = {"v":{"ing":"G", "ng":"G", "ed":"D", "s":"S"},
               "n":{"s":"S"},}

def applyInflectionalMorphology(text, tagger=False):
    s = []
    if tagger:
        text = tagger.tag(text)
    for form, label in text:
        form = form.strip()
        label = label[0][0]
        if label[0] == "J":
            t = "a"
        else:
            t = label[0].lower()
        try:
            root = tag.wordnet.morphy(form.lower(), t)
            if root and len(root) <= len(form):
                try:
                    for affix in INFLECTIONS[t]:
                        if form[-len(affix):] == affix:
                            label += INFLECTIONS[t][affix]
                            break
                except:
                    pass
        except:
            pass
        s.append([form, label])
    return s
            
def applyPattern(pattern, text):
    return pattern[0].sub(lambda m: "%s///%s"%(extracttext(m.group(0), pattern[2]), pattern[1]), text)

def chunk(text0, patterns=patterns, tagger=False):
    changed = True
    if tagger:
        text0 = " ".join(map(lambda x: "%s///%s"%(x[0], x[1]), (tagger.tag(text0))))
    text1 = text0
    while changed:
        changed = False
        for pattern in patterns:
            text1 = applyPattern(pattern, text0)
            if not text1 == text0:
                changed = True
                text0 = text1
                break
    return map(lambda x: x.split("///"), text1.split(" "))
        
def allsynsets(n=-1):
    synsets = []
    for ss in tag.wordnet.all_synsets(tag.wordnet.VERB):
        sentences = map(str, ss.examples)
        if not sentences == []:
            synsets.append([ss.lemmas, sentences])
            n -= 1
            if n == 0:
                break
    return synsets

def splitpunctuation(text):
    return re.compile("\.|;|-|\?|!|:|,").sub(" \g<0> ", text).replace("  ", " ").strip()

def preprocess(text):
    return replaceAll(text,
                      [("it's", "it is"), ("its", "it s"), ("'s", " s"), ("won't", "will not"), ("n't", " not"), ("cannot", "can not"), ("AM", "AMGMT"), ("A.M.", "AMGMT"), ("P.M.", "PMGMT"), ("--", " emdash "), ("I'm", "I am"), ("'ve", " have")])

tagpattern = re.compile("(?P<form>\S+)///(?P<tag>\S+)")
phrasePattern = re.compile(".*<sub>NP(\S?)</sub></span>.*")

def colour(c, txt):
    return """<span style="color:%s">%s</span>"""%(c, txt)

def subspan(m, id, onclick):
    return """<span id='%s' onclick="add2list('%s',%s,'%s')">%s<sub>%s</sub></span>"""%(id, id, onclick, onclick, m.group("form"), m.group("tag"))

def html(words, wordOrPhrase, sentenceCounter, markNPs=False):
    if markNPs:
        onclick = 'misparsed'
    else:
        onclick = 'mistagged'
    s = ""
    for wordCounter in range(len(words)):
        word = words[wordCounter]
        if not type(word) == "str":
            tag = word[1]
            if not type(tag) == "str":
                tag = ",".join(map(lambda x: "%s<sub><small>%.2f</small></sub>"%(x[0], x[1]), sortTable(tag) if type(tag) == "dict" else tag))
            word = "%s///%s"%(word[0], tag)
        id = "%s-%s-%s"%(wordOrPhrase, sentenceCounter, wordCounter)
        word = tagpattern.sub((lambda m: subspan(m, id, onclick)), word).strip()
        if markNPs and phrasePattern.match(word):
            word = colour("blue", word)
        s += "%s\n"%(word)
    return s

def tagX(text, tagger):
    text = untitle(text)
    text = tagger.tag(text, getAll=True)
    text1 = []
    for word in text:
        word[1] = sortTable(word[1])
    return text

def li(s):
    return """
  <li>
    %s
  </li>"""%(s)

def checksentence(s0, out, tagger, sentencecounter=1, patches=patches, patterns=patterns, stages={1,2,3,4,5}, html=html):
    allhtml = []
    s0 = splitpunctuation(untitle(preprocess(s0).strip()))
    sdict = s0.split(" ")
    try:
        sdict = zip(sdict, map(sortTable, tagger.initialtags(sdict)))
    except:
        sdict = zip(sdict, map(sortTable, tagger.mxl.initialtags(sdict)))
    if html:
        sdhtml = html(sdict, "Y", sentencecounter)
    laststage = max(stages)
    if 1 in stages:
        if html:
            allhtml.append(li(sdhtml))
    if laststage > 1:
        s0 = tagger.tag("aaa %s zzz"%(s0))
        if html:
            s0html = html(s0[1:-1], "X", sentencecounter).split("\n")
            zipped = zip(sdict, s0[1:-1], s0html)
            for i in range(len(zipped)):
                a, b, c = zipped[i]
                if not a[1][0][0] == b[1][0][0]:
                    s0html[i] = colour("blue", s0html[i])
            if 2 in stages:
                allhtml.append(li("\n".join(s0html)))
    if laststage > 2:
        s1 = applyInflectionalMorphology(s0)
        if html:
            s1html = html(s1[1:-1], "A", sentencecounter)
            if 3 in stages:
                allhtml.append(li(s1html))
    if laststage > 3:
        s2 = patchText(" ".join(map(lambda x: "%s///%s"%(x[0], x[1]), s1)), patches=patches)
        if html:
            s2html = html(s2.replace("  ", " ").split(" ")[1:-1], "A", sentencecounter)
            s1html = s1html.split("\n")
            s2html = s2html.split("\n")
            for i in range(len(s2html)):
                if not s2html[i] == s1html[i]:
                    s2html[i] = """<font color="blue">%s</font>"""%(s2html[i])
            if 4 in stages:
                allhtml.append(li("\n".join(s2html).replace("'A-", "'B-")))
    if laststage > 4:
        s3 = chunk(s2, patterns, tagger=tagger)
        if html and 5 in stages:
            allhtml.append(li(html(s3.replace("  ", " ").split(" ")[1:-1], "C", sentencecounter, markNPs=True)))
    out(r"""
<form>
   <ul>""")
    for h in allhtml:
        out(h)
    out("""
  </ul>
</form>
""")
    try:
        return s3
    except:
        return

def justTag(sentence, tagger):
    return map(lambda x: x.split("///"), checksentence(sentence, lambda x:x, tagger, html=False).split(" "))[1:-1]

def justTagAll(sentences, tagger):
    tagged = []
    for x in sentences:
        for s in x[1]:
            tagged.append(justTag(s, tagger))
    return tagged

def checksentences(sentences, tagger, patches=patches, patterns=patterns, outfile=sys.stdout, stages={1,2,3,4,5}):
    with safeout(outfile) as out:
        out("""
<ol>
""")
        sentencecounter = 0
        for x in sentences:
            for s0 in x[1]:
                if len(sentences) < 200:
                    print s0
                sentencecounter += 1
                out("<li>")
                checksentence(s0, out, tagger, sentencecounter, patches=patches, patterns=patterns, stages=stages)
                out("</li>")
        out(r"""
</ol>
</body>
</html>
""")

def splitTSV(s):
    return {y[0]:y[1] for y in [x.split("\t") for x in s.split("\n")]}

def respond(args, tagger):
    if type(args) == "str":
        args = splitTSV(args)
    try:
        stages = map(int, args['stages'].split("&"))
    except:
        stages = [1,2,3,4,5]
    sw = stringwriter()
    if 'showWNEntries' in args:
        try:
            start = int(args['start'])
        except:
            start = 0
        try:
            end = int(args['end'])
        except:
            end = 20
        checksentences(sentences[start:end], tagger, outfile=sw, stages=stages)
        return sw.txt
    elif 'parseOneSentence' in args:
        sentence = args['parseThisSentence']
        with safeout(sw) as out:
            checksentence(sentence, out, tagger, stages=stages)
        return sw.txt
    elif 'justTag' in args:
        sentence = args['parseThisSentence']
        with safeout(sw) as out:
            out("%s.\n"%(justTag(sentence, tagger)))
        return sw.txt

def testrespond(tagger):
    print respond("parseThisSentence\tthe cat sat on the mat\nparseOneSentence\tTrue",
                  tagger)
    
def starttaggerservers(tagger):
    startservers(respond=lambda x: respond(x, tagger))
