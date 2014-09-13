#!/usr/bin/python
#
# This will uncompress (if need be) the input,
# process it to find the KiCAD library and/or module
# fileas, generate their JSON MeowCAD counterparts
# and put it into the destination location.
#
# This program will generate the corresponding .mod or .lib
# files, as appropriate, in the directory:
#
# <out_dir>/(eeschema|pcb)/json/<name>/<part>.json
#
# depending on type.
#
# This will also generate files of the form:
#
# <UUID>-(footprint|component)_(location|list).json
#
# where appropriate that hold the dropdown json list
# information and the location information.
#

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

g_verbose_flag = False

UUID = str(uuid.uuid4())
TMP_DIR = "/tmp/" + UUID

LIB_LOC_JSON = {}
MOD_LOC_JSON = {}

LIB_ELE_LIST_JSON = {}
MOD_ELE_LIST_JSON = {}

sp.call(" mkdir -p " + TMP_DIR, shell=True  )

libjson_exec = "/home/meow/pykicad/libjson.py"
libsnap_exec = "/home/meow/www.meowcad.com/js/libsnap.js"

modjson_exec = "/home/meow/pykicad/modjson.py"
libsnap_exec = "/home/meow/www.meowcad.com/js/modsnap.js"

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
parser.add_argument('-V','--verbose', help='Verbose', action='store_true' )
#parser.add_argument('-m','--mime', help='Output in MIME type', action='store_true' )
#parser.add_argument('-u','--user-id', help='User ID' )
#parser.add_argument('-p','--project-id', help='Project ID' )
args = vars(parser.parse_args())

inp_fn = args["input"]
out_dir = args["output_dir"]
g_verbose_flag = args["verbose"]
#userId = args["user_id"]
#projectId = args["project_id"]
#showmime = args["mime"]

# DEBUG
if g_verbose_flag:
  print "#TMP_DIR:", TMP_DIR

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
    try:
      liblist_str = sp.check_output( [ libjson_exec, os.path.join(root, fn) , lib_dir + "/" ] )

      liblist = liblist_str.split("\n")
      for name_loc in liblist:
        v = name_loc.split(' ')
        if len(v) < 2: continue
        name,loc = v[0], v[1][len(TMP_DIR)+1:]
        LIB_LOC_JSON[ name ] = { "name" : name, "location" : loc }

        list_ele = { "id" : name, "name" : name, "data" : loc, "type" : "element" }
        ele = { "id" : fin_rel_dir, "name" : fin_rel_dir }
        ele["data"] = os.path.join( "eeschema", "json", fin_rel_dir )
        ele["type"] = "list"
        ele["list"] = []
        if fin_rel_dir in LIB_ELE_LIST_JSON:
          ele = LIB_ELE_LIST_JSON[fin_rel_dir]
        ele["list"].append( list_ele )
        LIB_ELE_LIST_JSON[fin_rel_dir] = ele

    except Exception,e:
      print "modjson failed:", str(e)


  if ktype == "mod":
    mod_dir = os.path.join( TMP_DIR, "pcb", "json", fin_rel_dir )
    sp.call(" mkdir -p " + mod_dir  , shell=True  )

    try:
      modlist_str = sp.check_output( [ modjson_exec, os.path.join(root, fn) , mod_dir + "/" ] )

      modlist = modlist_str.split("\n")
      for name_loc in modlist:
        v = name_loc.split(' ')
        if len(v) < 2: continue
        name,loc = v[0], v[1][len(TMP_DIR)+1:]
        MOD_LOC_JSON[ name ] = { "name" : name, "location" : loc }

        list_ele = { "id" : name, "name" : name, "data" : loc, "type" : "element" }
        ele = { "id" : fin_rel_dir, "name" : fin_rel_dir }
        ele["data"] = os.path.join( "pcb", "json", fin_rel_dir )
        ele["type"] = "list"
        ele["list"] = []
        if fin_rel_dir in MOD_ELE_LIST_JSON:
          ele = MOD_ELE_LIST_JSON[fin_rel_dir]
        ele["list"].append( list_ele )
        MOD_ELE_LIST_JSON[fin_rel_dir] = ele

    except Exception,e:
      print "modjson failed:", str(e)


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
    if g_verbse_flag:
      print "# maximum recursion reached, stopping"
    return

  typ = magic.from_file( inp_fn, mime=True )
  app,mtype = typ.split("/")

  if g_verbose_flag:
    print "#", typ, app, mtype

  if mtype == "gzip":
    if g_verbose_flag: print "# gzip"

    bn = os.path.splitext( os.path.basename( inp_fn ) )[0]
    cmd = "gunzip -c " + inp_fn + " > " + TMP_DIR  + "/" + bn
    x = sp.call( cmd, shell=True )
    process_file( TMP_DIR + "/" + bn, recur+1 )

  elif mtype == "zip":
    if g_verbose_flag: print "# zip"

    cmd = [ "unzip", "-q", inp_fn , "-d", TMP_DIR ]
    x = sp.call( cmd )
    process_dir( TMP_DIR )

  elif mtype == "x-bzip2":
    if g_verbose_flag: print "# bzip2"

    bn = os.path.splitext( os.path.basename( inp_fn ) )[0]
    cmd = "bunzip2 -c " + inp_fn + " > " + TMP_DIR  + "/" + bn
    x = sp.call( cmd, shell=True )
    process_file( TMP_DIR + "/" + bn, recur+1 )

  elif mtype == "x-tar":
    if g_verbose_flag: print "# x-tar"

    bn = os.path.splitext( os.path.basename( inp_fn ) )[0]
    cmd = "tar xC " + TMP_DIR + " -f " + inp_fn 
    x = sp.call( cmd, shell=True )
    os.remove( inp_fn )
    process_dir( TMP_DIR )


  elif mtype == "directory":
    if g_verbose_flag: print "# directory"

    cmd = [ "mv", inp_fn, TMP_DIR ]
    sp.call( [ "mv", inp_fn, TMP_DIR ] )

    process_dir( TMP_DIR )

  elif app == "text":
    if g_verbose_flag: print "# text"

    process_modlib( TMP_DIR, inp_fn )



process_file( inp_fn )
shutil.rmtree( TMP_DIR )

sp.call(" mkdir -p " + out_dir  + "/json" , shell=True  )

if len(LIB_LOC_JSON) > 0:
  floc = open( os.path.join( out_dir, "json", UUID + "_component_location.json" ), "w" )
  floc.write( json.dumps( LIB_LOC_JSON, indent=2 ) )
  floc.close()

  print UUID + "_component_location.json"

if len(LIB_ELE_LIST_JSON) > 0:
  flist = open( os.path.join( out_dir, "json", UUID + "_component_list.json" ), "w" )
  flist.write( json.dumps( LIB_ELE_LIST_JSON, indent=2 ) )
  flist.close()

  print UUID + "_component_list.json"

if len(MOD_LOC_JSON) > 0:
  floc = open( os.path.join( out_dir, "json", UUID + "_footprint_location.json" ), "w" )
  floc.write( json.dumps( MOD_LOC_JSON, indent=2 ) )
  floc.close()

  print UUID + "_footprint_location.json"

if len(MOD_ELE_LIST_JSON) > 0:
  flist = open( os.path.join( out_dir, "json", UUID + "_footprint_list.json" ), "w" )
  flist.write( json.dumps( MOD_ELE_LIST_JSON, indent=2 ) )
  flist.close()

  print UUID + "_footprint_list.json"

