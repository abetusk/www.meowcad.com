#!/usr/bin/python
#
# Generate the location and list JSON files
# for use by the schematic and board editor.
#

import json
import urllib
import re
import os
import os.path
import sys
import subprocess as sp
import meowaux as mew

def get_name(x):
  return x["name"].lower()


init_base = "/var/www/json"

init_comp_loc_fn = init_base + "/component_location.json"
init_comp_lst_fn = init_base + "/component_list_default.json"
init_foot_loc_fn = init_base + "/footprint_location.json"
init_foot_lst_fn = init_base + "/footprint_list_default.json"

comp_loc = json.loads( mew.json_slurp_file( init_comp_loc_fn ) )
comp_lst = json.loads( mew.json_slurp_file( init_comp_lst_fn ) )
foot_loc = json.loads( mew.json_slurp_file( init_foot_loc_fn ) )
foot_lst = json.loads( mew.json_slurp_file( init_foot_lst_fn ) )

if len(sys.argv) < 2:
  print "provide input base directory"
  sys.exit(1)

base = sys.argv[1]

if len(base)==0:
  print "provide input base directory"
  sys.exit(1)

if base[ len(base)-1 ] != '/':
  base += "/"

processed_fn = []

for fn in os.listdir( base ):

  if fn.endswith("_component_location.json"):
    f = open(base + fn)
    x = json.load(f)
    f.close()

    for k in x:
      comp_loc[k] = x[k]

    processed_fn.append( base + "/" + fn )

  if fn.endswith("_component_list.json"):

    f = open( base + fn)
    x = json.load(f);
    f.close()

    for k in x:
      comp_lst.append( x[k] )

    processed_fn.append( base + "/" + fn )

  if fn.endswith("_footprint_location.json"):

    f = open(base + fn)
    x = json.load(f)
    f.close()

    for k in x:
      foot_loc[k] = x[k]

    processed_fn.append( base + "/" + fn )

  if fn.endswith("_footprint_list.json"):

    f = open( base + fn)
    x = json.load(f);
    f.close()

    for k in x:
      foot_lst.append( x[k] )

    processed_fn.append( base + "/" + fn )

for i,v in enumerate(comp_lst):
  comp_lst[i]["list"] = sorted( comp_lst[i]["list"], key=get_name )

for i,v in enumerate(foot_lst):
  foot_lst[i]["list"] = sorted( foot_lst[i]["list"], key=get_name )

comp_lst = sorted( comp_lst, key=get_name )
foot_lst = sorted( foot_lst, key=get_name )

#f = open( base + "/json/component_location.json", "w" )
f = open( base + "/component_location.json", "w" )
f.write( json.dumps( comp_loc, indent=2 ) )
f.close()

#f = open( base + "/json/component_list_default.json", "w" )
f = open( base + "/component_list_default.json", "w" )
f.write( json.dumps( comp_lst, indent=2 ) )
f.close()

#f = open( base + "/json/footprint_location.json", "w" )
f = open( base + "/footprint_location.json", "w" )
f.write( json.dumps( foot_loc, indent=2 ) )
f.close()

#f = open( base + "/json/footprint_list_default.json", "w" )
f = open( base + "/footprint_list_default.json", "w" )
f.write( json.dumps( foot_lst, indent=2 ) )
f.close()

sp.call(" mkdir -p " + base + "/.store", shell=True )
for fn in processed_fn:
  bn = os.path.basename( fn )
  os.rename( fn, base + "/.store/" + bn )

