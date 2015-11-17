
class stringwriter:

    def __init__(self):
        self.txt = ""
        self.cursor = 0
        
    def write(self, s):
        self.txt += "%s"%(s)

    def read(self, n=1):
        s = self.txt[self.cursor:n]
        self.cursor += n
        return s

    def readline(self):
        txt, self.txt = self.txt.split("\n", 1)
        self.cursor += len(txt)
        return txt
        
