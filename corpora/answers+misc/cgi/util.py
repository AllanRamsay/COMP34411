#!/usr/bin/env python

import os
import string
import time
import md5
import base64
import posixfile
import sys

#
# the base directory of all this
#
ROOTDIR="/mnt/www/cgi/cotton/senseval"
LOGFILE=os.path.join(ROOTDIR, "log")
USERFILE=os.path.join(ROOTDIR, "users")

#
# time restraints XXX update these
#
trial_to_train = 14 * (3600 * 24) # 14 days
train_to_test = 5 * (3600 * 24)    # 5 days
test_to_answer = 5 * (3600 * 24)   # 5 days

# the amount of time for which an authentication holds
reserve_auth_time=1500

#
# a list of the tasks and their values in the cgi option
# menu
#
tasks = [("swedish-lex-sample", "Swedish Lexical Sample"),
         ("chinese-lex-sample", "Chinese Lexical Sample"),
         ("korean-lex-sample", "Korean Lexical Sample"),
         ("danish-lex-sample", "Danish Lexical Sample"),
         ("dutch-all-words", "Dutch All Words"),
         ("estonian-all-words", "Estonian All Words"),
         ("english-lex-sample", "English Lexical Sample"),
         ("english-all-words", "English All Words"),
         ("italian-lex-sample", "Italian Lexical Sample"),
         ("basque-lex-sample", "Basque Lexical Sample"),
         ("spanish-lex-sample", "Spanish Lexical Sample"),
         ("czech-all-words",  "Czech All Words"),
         ("japanese-lex-sample", "Japanese Lexical Sample")
         ]
tasks.sort()
         
def cgihdr():
    print "Content-type: text/html"
    print

#
# exception interface, names should be self explanatory
#
class InvalidUserName(Exception): pass
class InvalidPW(Exception): pass
class StageUnavailable(Exception): pass

#
# get a timestamp
#
def getts():
    return time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))

#
# logging utility
#
def log(s, *args):
    ts = getts()
    fp = open(LOGFILE, "a+")
    if args:
        s = s % (tuple(args))
    fp.write("%s: %s\n" % (ts, s.rstrip()))
    fp.close()

#
# check the validity of a username
#
def check_username(uname):
    errs = []
    if uname.find(":") != -1:
        errs.append("username can't contain a colon (:)")
    try:
        User(uname)
        errs.append("name in use: '%s'" % uname)
    except KeyError:
        pass
    return errs

#
# tell whether or not data for a stage task combo is
# available
#
def stage_available(stage, task):
    tmp = os.path.join(ROOTDIR, task)
    path = os.path.join(tmp, "%s.tgz" % stage)
    return os.path.exists(path)

# uh, this creates a newuser.
#
# XXX there is some confusion over the names "sample", "train", and
# "test".
#
# In "reality", "sample" means data that participants use in order
# to see what the format will be like
#
# "training" means data that has answers for participants to train their
# systems on and test means data without answers.f
#
def newuser(uname, email, systems, pw, task, organiz=""):
    # username:email:password:lang:task:trialts:traints:testts:answerts
    if uname.find(":") != -1:
        raise InvalidUserName(uname, "can't contain a ':'")
    try:
        User(uname)
        raise InvalidUserName(uname, "name in use")
    except KeyError:
        pw_checksum = base64.encodestring(md5.md5(pw).digest())[:-1]
        ustr = "%s:%s:%s:%s:%s:::::%s\n" % (uname,
                                            email,
                                            systems,
                                            pw_checksum,
                                            task,
                                            organiz)
        log("newuser: %s", ustr)
        fp = posixfile.open(USERFILE, "a+")
        fp.lock("w|")
        try:
            fp.write(ustr)
        finally:
            fp.lock("u")
            fp.close()

#
# user class, interface still in rapid change stage so no more
# to say just yet...
#
class User:

    def __init__(self, uname):
        fp = open(USERFILE)
        found = 0
        for line in fp.readlines():
            if not line.strip(): continue
            (self.username,
             self.email,
             self.systems,
             self.pw_checksum,
             self.task,
             self.trial_ts,
             self.train_ts,
             self.test_ts,
             self.answer_ts, self.organization) = string.split(line, ":")
            if self.username == uname:
                found = 1
                break
        fp.close()
        if not found:
            raise KeyError(uname)

    def __str__(self):
        return "%s:%s:%s:%s:%s:%s:%s:%s:%s:%s" % (self.username,
                                                  self.email,
                                                  self.systems,
                                                  self.pw_checksum,
                                                  self.task,
                                                  self.trial_ts,
                                                  self.train_ts,
                                                  self.test_ts,
                                                  self.answer_ts,
                                                  self.organization)

    def save(self):
        lines = open(USERFILE).readlines()
        for x in range(len(lines)):
            line = lines[x]
            name = string.split(line, ":")[0]
            if name == self.username:
                lines[x] = str(self) 
                break
        data = string.join(lines, "")
        fp = posixfile.open(USERFILE, "a+")
        fp.lock("w|")
        try:
            fp.truncate(0)
            fp.write(data)
        finally:
            fp.lock("u")
            fp.close()
    
    def checkpw(self, pw):
        user = User(self.username)
        checksum = base64.encodestring(md5.md5(pw).digest())[:-1]
        if checksum != user.pw_checksum:
            log("checking password for %s (failed)", self.username)
            return 0
        log("checking password for %s (succeeded)", self.username)
        return 1

    def setpw(self, pw):
        log("set password of %s", self.username)
        user = User(self.username)
        checksum = base64.encodestring(md5.md5(pw).digest())[:-1]
        user.pw_checksum = checksum
        user.save()

    def has_trial(self):
        return self.trial_ts != ""
    def has_train(self):
        return self.train_ts != ""
    def has_test(self):
        return self.test_ts != ""
    def has_answers(self):
        return self.answer_ts != ""

    def get_remaining_stage(self):
        if not self.has_trial():
            return "trial"
        if not self.has_train():
            return "train"
        if not self.has_test():
            return "test"
        return "answers" 

    def get_filename(self, stage):
        path = self.get_path_for_stage(stage)
        _, fn = os.path.split(path)
        return fn

    #
    # internal methods
    #
    def get_data_dir(self):
        """
        return the directory containing the various stages of
        data (train, training, etc)
        """
        return os.path.join(ROOTDIR, self.task)

    def get_path_for_stage(self, stage):
        """
        .get_path_for(str: stage) -> str: path

        given a stage (trial, train, or test), return
        the path to the appropriate data
        """
        if not stage in ("trial", "train", "test"):
            raise ValueError("no such stage: " + stage)
        return os.path.join(self.get_data_dir(),
                            "%s.tgz" % stage)


    def get_data_for_stage(self, stage):
        """
        .get_data_for_stage(str: stage) -> str: data

        get the data for the stage in question if it's available
        marking the timestamp for this user.
        """
        log("get_data_for_stage(%s) by %s", stage, self.username)
        path = self.get_path_for_stage(stage)
        if os.path.exists(path):
            log("request from %s to get data for stage %s",
                self.username,
                stage)
            data = open(path).read()
            setattr(self, "%s_ts" % stage, getts())
            self.save()
            return data
        else:
            raise StageUnavailable(stage, self.task)


    def upload_answers(self, infile, sysname):
        """
        .upload_answers(file: infile, string: sysname) -> None
        
        upload the users answers into the answers directory
        """
        log("upload answers from %s (sysname %s)",
            self.username,
            sysname)
        answer_dir = os.path.join(ROOTDIR, "answers")
        fname = "%s-%s" % (self.username, sysname)
        path = os.path.join(answer_dir, fname)
        out = open(path, "w")
        # read in without filling memory
        while 1:
            line = infile.readline()
            if not line:
                break
            out.write(line)
        out.close()
        

        

        
        
        

