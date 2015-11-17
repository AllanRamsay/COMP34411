from nltk.corpus import verbnet
import re
import os

pp = "(PREP\[[^\]]*\] NP(\[[^\]]*\])?\s*)"
framePattern = re.compile("Syntax: (?P<frame>.*)")
membersPattern = re.compile("Members: (?P<members>.*)Thematic roles:", re.DOTALL)
NP = re.compile(r"NP\[[A-Z][a-z\d]*?( \+plural)?\]")
finalPPs = re.compile(r"%s+$"%(pp))
german = re.compile(r"%s VERB"%(pp))
shifted = re.compile(r"NP VERB %s"%(pp))
scomp = re.compile(r"NP\[\S* \+that_comp\]")

def l2s(l):
    s = ""
    for x in l:
        s += "%s "%(x)
    return s.strip()

def mergeNPs(frame):
    return NP.sub("NP", frame).replace("NP[Cause +genitive] LEX['s] NP", "NP").replace("NP LEX['s] NP", "NP").replace("NP LEX[and] NP", "NP").replace("NP[Patient +genitive] NP", "NP").replace("NP[Theme +genitive] NP", "NP")

def getFrames(verb, frames):
    for classid in verbnet.classids(verb):
        vnclass = verbnet.pprint(verbnet.vnclass(classid))
        members = re.compile("\s+").split(membersPattern.search(vnclass).group("members"))
        for i in framePattern.finditer(vnclass):
            frame = mergeintrans(mergeNPs("%s"%(i.group("frame"))))
            frame = scomp.sub("SCOMP", frame)
            frame = german.sub("VERB", frame)
            frame = shifted.sub("NP VERB NP", frame)
            frame = finalPPs.sub("", frame)
            if frame in frames:
                frames[frame] += members
            else:
                frames[frame] = members
    return frames

def getClasses():
    frames = {}
    for p, d, f in os.walk("/Users/ramsay/nltk_data/corpora/verbnet"):
        for w in f:
            if not "_" in w:
                getFrames(w.split("-")[0], frames)
    framelist = []
    for frame in frames:
        framelist.append(frame)
    framelist.sort()
    return frames, framelist

def showClasses((frames, framelist)):
    for f in framelist:
        print "%s, %s"%(f, l2s(frames[f][:6]))
                        
