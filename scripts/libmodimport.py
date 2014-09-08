#!/usr/bin/python

import re
import sys
import json
import uuid
import meowaux as mew
import subprocess as sp
import argparse
import magic
import os.path
import shutil

TMP_DIR = "/tmp/" + str(uuid.uuid4())

# DEBUG
print TMP_DIR

sp.call(" mkdir -p " + TMP_DIR, shell=True  )

#libjson_exec = "/home/meow/pykicad/libjson.py"
#libsnap_exec = "/home/meow/www.meowcad.com/js/libsnap.js"
#
#modjson_exec = "/home/meow/pykicad/modjson.py"
#libsnap_exec = "/home/meow/www.meowcad.com/js/modsnap.js"

libjson_exec = "/home/abram/prog/pykicad/libjson.py"
libsnap_exec = "/home/abram/prog/www.meowcad.com/js/libsnap.js"

modjson_exec = "/home/abram/prog/pykicad/modjson.py"
libsnap_exec = "/home/abram/prog/www.meowcad.com/js/modsnap.js"


def kicad_magic( fn ):
  f = open(fn)
  l = f.readline()
  f.close()

  if re.search( "^\s*EESchema-LIBRARY", l, re.IGNORECASE ):
    return "kicad/lib"

  if re.search( "^\s*PCBNEW-LibModule-", l, re.IGNORECASE ):
    return "kicad/mod"

  if re.search( "^\s*EESchema\s*Schematic\s", l, re.IGNORECASE ):
    return "kicad/sch"

  if re.search( "^\s*PCBNEW-BOARD\s", l ):
    return "kicad/pcb"

  if re.search( "^\s*\(kicad_pcb ", l ):
    return "kicad/pcb-s-exp"

  return "unknown"


parser = argparse.ArgumentParser(description='Description of your program')
parser.add_argument('-i','--input', help='Input file', required=True)
parser.add_argument('-o','--output-dir', help='Output directory', required=True)
#parser.add_argument('-m','--mime', help='Output in MIME type', action='store_true' )
#parser.add_argument('-u','--user-id', help='User ID' )
#parser.add_argument('-p','--project-id', help='Project ID' )
args = vars(parser.parse_args())

inp_fn = args["input"]
out_dir = args["output_dir"]
#userId = args["user_id"]
#projectId = args["project_id"]
#showmime = args["mime"]

if out_dir is None:
  out_dir = "./"


def process_modlib( root, fn ):

  t = kicad_magic( os.path.join(root, fn) )
  if t == "unknown": 
    return

  a,ktype = t.split('/')

  rel_root = root[len(TMP_DIR)+1:]

  fin_rel_dir = rel_root + "-" + os.path.splitext( fn )[0]
  fin_rel_dir = re.sub( "[^a-zA-Z0-9-_%]", "", fin_rel_dir )
  fin_rel_dir = re.sub( "^-*", "", fin_rel_dir )

  fin_abs_dir = os.path.join( TMP_DIR, fin_rel_dir )

  if ktype == "lib":
    lib_dir = os.path.join( TMP_DIR, "eeschema", "json", fin_rel_dir )
    sp.call(" mkdir -p " + lib_dir , shell=True  )
    sp.call( [ libjson_exec, os.path.join(root, fn) , lib_dir + "/" ] )

  if ktype == "mod":
    mod_dir = os.path.join( TMP_DIR, "pcb", "json", fin_rel_dir )
    sp.call(" mkdir -p " + mod_dir  , shell=True  )
    k = sp.call( [ modjson_exec, os.path.join(root, fn) , mod_dir + "/" ] )


def process_dir( base_dir ):

  for root,dirs,files in os.walk( base_dir ):
    for f in files:

      t = kicad_magic( os.path.join( root, f ) )
      if t == "unknown": 
        os.remove( os.path.join(root, f) )
        continue

      #process_modlib( root, os.path.join(root, f) )
      process_modlib( root, f )


  for f in os.listdir( base_dir ):
    sp.call( [ "cp", "-R" , os.path.join(base_dir,f), out_dir ] )

    if os.path.isdir( os.path.join(base_dir,f) ):
      shutil.rmtree( os.path.join(base_dir,f) )
    else:
      os.unlink( os.path.join(base_dir,f) )
    #sp.call( [ "rm", "-rf", os.path.join(TMP_DIR,f)] )



def process_file( inp_fn, recur=0, processed={} ):

  if recur==3:
    print "maximum recursion reached, stopping"
    return

  typ = magic.from_file( inp_fn, mime=True )
  app,mtype = typ.split("/")

  #DEBUG
  print typ, app, mtype

  if mtype == "gzip":
    print "gzip"

    bn = os.path.splitext( os.path.basename( inp_fn ) )[0]
    cmd = "gunzip -c " + inp_fn + " > " + TMP_DIR  + "/" + bn
    x = sp.call( cmd, shell=True )
    process_file( TMP_DIR + "/" + bn, recur+1 )

  elif mtype == "zip":
    print "zip"

    cmd = [ "unzip", "-q", inp_fn , "-d", TMP_DIR ]
    x = sp.call( cmd )
    process_dir( TMP_DIR )

  elif mtype == "x-bzip2":
    print "bzip2"

    bn = os.path.splitext( os.path.basename( inp_fn ) )[0]
    cmd = "bunzip2 -c " + inp_fn + " > " + TMP_DIR  + "/" + bn
    x = sp.call( cmd, shell=True )
    process_file( TMP_DIR + "/" + bn, recur+1 )

  elif mtype == "x-tar":
    print "x-tar"

    bn = os.path.splitext( os.path.basename( inp_fn ) )[0]
    cmd = "tar xC " + TMP_DIR + " -f " + inp_fn 
    x = sp.call( cmd, shell=True )
    os.remove( inp_fn )
    process_dir( TMP_DIR )


  elif mtype == "directory":
    print "directory"

    cmd = [ "mv", inp_fn, TMP_DIR ]
    sp.call( [ "mv", inp_fn, TMP_DIR ] )

    process_dir( TMP_DIR )

  elif app == "text":
    process_modlib( TMP_DIR, inp_fn )



#if not os.path.isfile( inp_fn ):
#  sys.stderr.write( inp_fn + "\n" )
#  parser.print_help()
#  sys.exit(1)



process_file( inp_fn )

shutil.rmtree( TMP_DIR )

