from useful import *
import subprocess

def prolog(goal):
    x = subprocess.Popen(("sicstus --goal %s,halt."%(goal)).split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    return x
    
