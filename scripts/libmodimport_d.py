#!/usr/bin/python

import os
import sys
import meowaux as mew
import time
import redis
import subprocess as sp

#ODIR = "/home/meow"
ODIR = "./tmp"
sleepy = 5

def process_imports():
  db = redis.Redis()

  qid = db.lpop( "importq" )

  while qid is not None:

    h = db.hgetall( "importq:" + qid )

    #DEBUG
    print qid, h

    userId = h["userId"]
    fileId = h["fileUUID"]

    if h["type"] == "portfolio":

      try:
        sp.check_call( [ "./libmodimport.py", 
                        "-i", ODIR + "/stage/" + fileId, 
                        "-o", ODIR + "/usr/" + userId ] )
        sp.check_call( [ "./libmodloclist.py",
                        ODIR + "/usr/" + userId + "/json/" ] )

        qid = db.lpop( "importq" )
      except:
        print "blonk"
        return None


while True:
  print ">"

  process_imports()
  time.sleep(sleepy)
