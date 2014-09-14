#!/usr/bin/python
#
# 'daemon' to exclusively process
# the snapshots for modules and libraries.
# It takes about a secnod (on a 3Ghz core)
# and can add up for libraries that are
# large.
#
# To spread out the conversion time
# and decouple the different portions of
# the service, this has been put into it's
# own service.
#
#

import os
import os.path
import sys
import meowaux as mew
import time
import subprocess as sp
import re
import json

ODIR = "/home/meow"
LIBMOD_SNAP_QUEUE_DIR = os.path.join( ODIR , "queue" )

sleepy = 5
verbose = True

def process_imports():

  qfns = []
  for f in os.listdir( LIBMOD_SNAP_QUEUE_DIR ):
    if os.path.isfile( os.path.join( LIBMOD_SNAP_QUEUE_DIR, f ) ) and f.endswith(".q"):
      qfns.append( f )
  #qfns = [ f for f in os.listdir( LIBMOD_SNAP_QUEUE_DIR ) if os.path.isfile( os.path.join( LIBMOD_SNAP_QUEUE_DIR, f ) ) ]

  for qfn in qfns:

    if verbose:
      print "libmod_snap_d>> processing", qfn

    fqfn_queue_file = os.path.join( LIBMOD_SNAP_QUEUE_DIR, qfn )

    fp = open( fqfn_queue_file, "r" )
    for line in fp:

      if verbose:
        print "libmod_snap_d>>>", line

      if line[0] == '#': continue
      line = line.rstrip()
      fileId, fn, userId, portfolioId = line.split(',')
      try:

        if len(fn)==0: continue

        if verbose:
          print "libmod_snap_d>>>>", fn

        base_fqfn = os.path.join( ODIR, "usr", userId )
        if len(portfolioId) > 0:
          base_fqfn = os.path.join( ODIR, "usr", userId, portfolioId )

        fqfn = os.path.join( base_fqfn, "json", ".store", fn )
        if (fqfn.endswith("_component_list.json") or fqfn.endswith("_footprint_list.json")) and os.path.isfile( fqfn ):
          f = open(fqfn)
          list_json = json.load(f)
          f.close()

          for libname in list_json:
            for v in list_json[libname]["list"]:
              loc = v["data"]

              png_fn = re.sub( "\.json$", ".png", loc )
              png_fn = re.sub( "/json/", "/png/", png_fn )

              if verbose:
                print "libmod_snap_d>>>> snap:", libname, loc, png_fn

              exec_snap = ""
              if fqfn.endswith("_component_list.json"):
                exec_snap = "../js/libsnap.js"
              elif fqfn.endswith("_footprint_list.json"):
                exec_snap = "../js/modsnap.js"


              myenv = os.environ.copy()
              myenv["NODE_PATH"] = "../js"
              sp.check_call( [ "mkdir", "-p", os.path.join( base_fqfn, os.path.dirname( png_fn ) )  ] )
              sp.check_call( [ "node", exec_snap,
                               "-i", loc,
                               "-W", "200",
                               "-H", "200",
                               "-u", userId,
                               "-o", os.path.join( base_fqfn, png_fn) ], env=myenv )

      except Exception,ee:
        print "libmod_snap_d error:", str(ee)
        return None

      pass

    # for open ...
    pass
    fp.close()

    print fqfn_queue_file, os.path.join( LIBMOD_SNAP_QUEUE_DIR, ".store", qfn )

    os.rename( fqfn_queue_file, os.path.join( LIBMOD_SNAP_QUEUE_DIR, ".store", qfn ) )

  # for listdir
  pass

while True:
  print ">"

  process_imports()
  time.sleep(sleepy)
