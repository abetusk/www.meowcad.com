#!/usr/bin/python
#
# This will uncompress (if need be) the input,
# process it to find the KiCAD library and/or module
# fileas, generate their JSON MeowCAD counterparts
# and put it into the destination location.
#
# This program will generate the corresponding .mod or .lib
# files, as appropriate, in the output directory.
#
# This will also generate files of the form:
#
# <out_dir>/json/<UUID>-(footprint|component)_(location|list).json
#
# where appropriate that hold the dropdown json list
# information and the location information.
#
# This can be used by later processes to incorporate the json
# files into the global, portfolio or project json files.
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
from signal import signal, SIGPIPE, SIG_DFL

g_verbose_flag = False

UUID = str(uuid.uuid4())
TMP_DIR = "/tmp/" + UUID

LIB_LOC_JSON = {}
MOD_LOC_JSON = {}

LIB_ELE_LIST_JSON = {}
MOD_ELE_LIST_JSON = {}

SRC_DIR = os.path.join( TMP_DIR, "src" )
DST_DIR = os.path.join( TMP_DIR, "dst" )

sp.check_call( [ "mkdir",  "-p",  TMP_DIR ] )
sp.check_call( [ "mkdir",  "-p",  SRC_DIR ] )
sp.check_call( [ "mkdir",  "-p",  DST_DIR ] )

libjson_exec = "/home/meow/pykicad/libjson.py"
modjson_exec = "/home/meow/pykicad/modjson.py"

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
parser.add_argument('-N','--name', help='Name of final module or library to use' )
#parser.add_argument('-p','--project-id', help='Project ID' )
args = vars(parser.parse_args())

inp_fn = args["input"]
out_dir = args["output_dir"]
g_verbose_flag = args["verbose"]
nice_modlib_name = args["name"]
#showmime = args["mime"]

# DEBUG
if g_verbose_flag:
  print "#TMP_DIR:", TMP_DIR

# If we don't have a nice name, take it from the file provided
#
if nice_modlib_name is None:
  nice_modlib_name = os.path.splitext( os.path.splitext( os.path.basename( inp_fn ) )[0] )[0]

# Make sure it's safe
#
nice_modlib_name = re.sub( "[^a-zA-Z0-9-_%]", "", nice_modlib_name )
nice_modlib_name = re.sub( "^-*", "", nice_modlib_name )

# Degenerate case, just use the UUID generated above
#
if len(nice_modlib_name) == 0:
  nice_modlib_name = UUID

if g_verbose_flag:
  print "nice name:", nice_modlib_name


####
#

def process_modlib( inp_fn, out_name ):

  t = kicad_magic( inp_fn )
  if t == "unknown": 
    return

  a,ktype = t.split('/')
  fin_rel_dir = out_name

  if ktype == "lib":
    #lib_dir = os.path.join( TMP_DIR, "eeschema", "json", fin_rel_dir )
    lib_dir = os.path.join( DST_DIR, "eeschema", "json", fin_rel_dir )
    sp.call(" mkdir -p " + lib_dir , shell=True  )
    try:
      liblist_str = sp.check_output( [ libjson_exec, inp_fn, lib_dir + "/" ] )

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

      return [ os.path.join( "eeschema", "json", fin_rel_dir ) ] 

    except Exception,e:
      print "modjson failed:", str(e)




  if ktype == "mod":
    #mod_dir = os.path.join( TMP_DIR, "pcb", "json", fin_rel_dir )
    mod_dir = os.path.join( DST_DIR, "pcb", "json", fin_rel_dir )
    sp.call(" mkdir -p " + mod_dir  , shell=True  )

    try:
      modlist_str = sp.check_output( [ modjson_exec, inp_fn, mod_dir + "/" ] )

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

      return [ os.path.join( "pcb", "json", fin_rel_dir ) ] 

    except Exception,e:
      print "modjson failed:", str(e)

  return []

def process_dir( base_dir, out_name  ):

  r = []

  for root,dirs,files in os.walk( base_dir ):
    for f in files:

      abs_fn = os.path.join( root, f )

      t = kicad_magic( abs_fn )
      if t == "unknown": 
        os.remove( abs_fn )
        continue

      X = process_modlib( abs_fn, out_name )
      for x in X:
        r.append( x )

  return r


def process_file( inp_fn, nice_name  ):

  typ = magic.from_file( inp_fn, mime=True )

  if typ=="unknown": return []
  if len(typ.split("/")) != 2:  return []
  app,mtype = typ.split("/")

  if mtype == "gzip":
    tcmd = "gunzip -c " + inp_fn + " | file -i -b - | cut -f1 -d';' | cut -f2 -d'/' "

    # http://stackoverflow.com/questions/10479825/python-subprocess-call-broken-pipe
    #
    x = sp.check_output( tcmd, shell=True, preexec_fn = lambda: signal(SIGPIPE, SIG_DFL) )
    x = x.rstrip()

    if x == "x-tar":
      if g_verbose_flag:
        print ".tar.gz"

      cmd = "tar xfz " + inp_fn + " -C " + SRC_DIR
      sp.call( cmd, shell=True )
      return process_dir( SRC_DIR, nice_name )

    else:
      if g_verbose_flag:
        print ".gz"

      cmd = "gunzip -c " + inp_fn + " > " + os.path.join( SRC_DIR, "tmp" )
      sp.call( cmd, shell=True )
      return process_dir ( SRC_DIR, nice_name )

  elif mtype == "zip":
    cmd = "unzip -q " + inp_fn + " -d " + os.path.join( SRC_DIR )
    sp.call( cmd, shell=True )
    return process_dir( SRC_DIR, nice_name )

  elif mtype == "x-bzip2":
    tcmd = "bunzip2 -c " + inp_fn + " | file -i -b - | cut -f1 -d';' | cut -f2 -d'/' "
    x = sp.check_output( tcmd, shell=True, preexec_fn = lambda: signal(SIGPIPE, SIG_DFL) )
    x = x.rstrip()

    if x == "x-tar":
      if g_verbose_flag:
        print ".tar.bz2"

      cmd = "tar jxf " + inp_fn + " -C " + SRC_DIR
      sp.call( cmd, shell=True )
      return process_dir( SRC_DIR, nice_name )

    else:
      if g_verbose_flag:
        print ".bz2"

      cmd = "bunzip2 -c " + inp_fn + " > " + os.path.join( SRC_DIR, "tmp" )
      sp.call( cmd, shell=True )
      return process_dir ( SRC_DIR, nice_name )

  elif mtype == "x-tar":
    if g_verbose_flag:
      print ".tar"

    cmd = "tar xf " + inp_fn + " -C " + SRC_DIR
    sp.call( cmd, shell=True )
    return process_dir( SRC_DIR, nice_name )


  elif mtype == "directory":
    if g_verbose_flag:
      print "dir"

    return process_dir( inp_fn, nice_name )

  elif app == "text" and mtype == "plain":
    if g_verbose_flag:
      print "text plain"

    return process_modlib( inp_fn, nice_name )

  return []


def process_file_old( inp_fn, nice_fn = None, recur=0, processed={} ):

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
    process_file( TMP_DIR + "/" + bn, nice_fn, recur+1 )

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
    process_file( TMP_DIR + "/" + bn, nice_fn, recur+1 )

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

    process_modlib( TMP_DIR, inp_fn, nice_fn )



src_dirs = process_file( inp_fn, nice_modlib_name )

if g_verbose_flag:
  print "got:", src_dirs

if src_dirs > 0:

  for src_dir in src_dirs:

    if g_verbose_flag:
      print "processing:", out_dir, src_dir

    stale_out_dir = os.path.join( out_dir, src_dir )
    if g_verbose_flag:
      print "rm -rf", stale_out_dir

    sp.call( "rm -rf " + stale_out_dir, shell=True ) 
    sp.call( "cp -R " + DST_DIR + "/* " + out_dir , shell=True )

shutil.rmtree( TMP_DIR )

sp.check_call( [ "mkdir", "-p", os.path.join( out_dir, "json" ) ] )


# Setup for a later process to process the location and list json files.
#

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

