from nltk.corpus import wordnet

"""
I'm using istitle to spot things that begin with upper case

For tweets we will probably want something that spots hash tags
"""
def isname(word):
    if word.istitle():
        for x in ['a', 'n', 'v', 'r']:
            if wordnet.morphy(word.lower(), x):
                return False
        return True
    else:
        return False
    
def getnames(words):
    names = []
    last = "."
    for word in words:
        if word.istitle() and not last in ".:!?":
            names.append(word)
        last = word
    return names
