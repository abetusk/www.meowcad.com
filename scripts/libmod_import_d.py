#!/usr/bin/python

import os
import sys
import meowaux as mew
import time
import redis
import subprocess as sp
import re
import json
import uuid

ODIR = "/home/meow"
LIBMOD_SNAP_QUEUE_DIR = os.path.join( ODIR , "queue" )

sleepy = 5
verbose = True

def process_imports():
  db = redis.Redis()

  qid = db.lpop( "importq" )

  while qid is not None:

    h = db.hgetall( "importq:" + qid )

    userId = h["userId"]
    fileId = h["fileUUID"]

    if h["type"] == "portfolio":

      try:

        if verbose:
          print "libmodimport_d>> processing", fileId, userId

        lmi_out = sp.check_output( [ "./libmodimport.py", 
                         "-i", ODIR + "/stage/" + fileId, 
                         "-o", ODIR + "/usr/" + userId ] )

        lmll_out = sp.check_output( [ "./libmodloclist.py",
                                      ODIR + "/usr/" + userId + "/json/" ] )

        processed_loclist_fn = lmi_out.split("\n")

        tmpid = str( uuid.uuid4() )

        tmpfn = os.path.join( "/tmp", tmpid )
        tmpfp = open( tmpfn , "w" )
        for fn in processed_loclist_fn:
          if len(fn) == 0: continue
          fqfn = ODIR + "/usr/" + userId + "/json/.store/" + fn
          tmpfp.write( ",".join( [ fileId, fqfn, userId, "" ] ) + "\n" )
        tmpfp.close()

        os.rename( tmpfn, os.path.join( LIBMOD_SNAP_QUEUE_DIR, fileId + ".q" ) )

        qid = db.lpop( "importq" )
      except Exception,ee:
        print "libmodimport_d error:", str(ee)
        return None


while True:
  if verbose:
    print ">"

  process_imports()
  time.sleep(sleepy)
