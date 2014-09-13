#!/usr/bin/python

import os
import sys
import meowaux as mew
import time
import redis
import subprocess as sp
import re
import json

ODIR = "/home/meow"
#ODIR = "./tmp"
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

        lmi_out = sp.check_output( [ "./libmodimport.py", 
                         "-i", ODIR + "/stage/" + fileId, 
                         "-o", ODIR + "/usr/" + userId ] )

        print "??", fileId, userId

        lmll_out = sp.check_output( [ "./libmodloclist.py",
                                      ODIR + "/usr/" + userId + "/json/" ] )

        processed_loclist_fn = lmi_out.split("\n")

        for fn in processed_loclist_fn:
          if len(fn)==0: continue
          print ">>>>", fn

          fqfn = ODIR + "/usr/" + userId + "/json/.store/" + fn

          if fqfn.endswith("_component_list.json") and os.path.isfile( fqfn ):
            f = open(fqfn)
            comp_list_json = json.load(f)
            f.close()

            for libname in comp_list_json:
              for v in comp_list_json[libname]["list"]:
                loc = v["data"]

                png_fn = re.sub( "\.json$", ".png", loc )

                print libname, loc, png_fn

                myenv = os.environ.copy()
                myenv["NODE_PATH"] = "../js"
                sp.check_call( [ "node", "../js/libsnap.js",
                                 "-i", loc,
                                 "-W", "200",
                                 "-H", "200",
                                 "-u", userId,
                                 "-o", ODIR + "/usr/" + userId + "/" + png_fn ], env=myenv )
                                 #ODIR + "/usr/" + userId + "/json/" ], env=env )

        qid = db.lpop( "importq" )
      except Exception,ee:
        print "blonk", str(ee)
        return None


while True:
  print ">"

  process_imports()
  time.sleep(sleepy)
