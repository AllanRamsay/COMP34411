
import threading
import time

def interruptThread(n):
    def interrupt():
        print "Interruption called in %s"%(threading.currentThread())
        raise Exception("timed out")
    threading.Timer(n, interrupt).start()

def testthread():
    print "Started %s"%(threading.currentThread())
    interruptThread(1)
    time.sleep(10)
    print "Finished %s"%(threading.currentThread())

def writestuff():
    print "writing things"
    time.sleep(30)
    print "writing more things"
    
def newthread(n, target=testthread):
    t = threading.Thread(target=target)
    t.start()
    return t
