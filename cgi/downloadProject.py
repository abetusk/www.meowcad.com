#!/usr/bin/python
#

import os
import cgi
import cgitb
import sys
import meowaux as mew
import urllib
import Cookie
import json
import uuid
import subprocess as sp
import zipfile as zf

cgitb.enable();

jsonsch_exec = "/home/meow/pykicad/jsonsch.py"
jsonbrd_exec = "/home/meow/pykicad/jsonbrd.py"
json2kicad_pcb_exec = "/home/meow/pykicad/json2kicad_pcb.py"

brdgrb_exec = "/home/meow/pykicad/brdgerber.py"
grbngc_exec = "/home/meow/bin/gbl2ngc"
drlngc_exec = "/home/meow/bin/drl2ngc"
font_file = "/home/meow/pykicad/aux/hershey_ascii.json"

staging_base = "/home/meow/stage"



#print "Content-Type: text/html"
#print

cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )

g_debug = False
def log_line( l ):
  logf = open("/tmp/downloadProject.log", "a")
  logf.write( l  + "\n")
  logf.close()


def error_and_quit():
  if g_debug:
    log_line("error, quitting")
  print "Status: 404 Not Found"
  print
  print "File not found"
  sys.exit(0)

def dumpToFile( data ):
  u_id = uuid.uuid4()
  fn = staging_base + "/" + str(u_id)
  f = open( fn, "w" )
  #f.write( json.dumps(json_message["data"], indent=2) )
  f.write( data )
  f.close()

  return u_id, fn

def readyProjectZipfile( json_message ):

  try:

    ## hacky to put here but quick and dirty, get the
    ## number of distinct layers.
    ## 
    ## Do the minimal thing of just getting to 4 layer boards.
    ## Only check explicitely layer 1 and 2 to see if we
    ## should include them in the output.  If layer 1
    ## exists, force the existence of layer 2 and vice versa.
    ##
    layer_map = {}
    brd = json_message["board"]["element"]
    for ele in brd:
      if ele["type"] == "track":
        layer_map[int(ele["layer"])] = True
    if 1 in layer_map: layer_map[2] = True
    if 2 in layer_map: layer_map[1] = True

    zip_uid = uuid.uuid4()

    # Put json data structures into files
    #
    sch_json_uid, brd_json_fn = dumpToFile( json.dumps(json_message["board"], indent=2) )
    brd_json_uid, sch_json_fn = dumpToFile( json.dumps(json_message["schematic"], indent=2) )

    log_line( "brd: " + brd_json_fn )
    log_line( "sch: " + sch_json_fn )

    # Create KiCAD schematic and board files
    #
    kicad_sch = sp.check_output( [jsonsch_exec, sch_json_fn] )
    sch_uid, sch_fn  = dumpToFile( kicad_sch )

    kicad_brd = sp.check_output( [jsonbrd_exec, brd_json_fn] )
    brd_uid, brd_fn = dumpToFile( kicad_brd )

    kicad_pcb = sp.check_output( [json2kicad_pcb_exec, brd_json_fn] )
    kicad_pcb_uid, kicad_pcb_fn = dumpToFile( kicad_pcb )

    # Go through relevant layers and create gerber and gcode files for each
    #
    ## from http://en.wikibooks.org/wiki/Kicad/file_formats
    ##
    ## 0 Back - Solder
    ## 1 Inner1-Cu, 2 Inner2-Cu (so says KiCAD)
    ## 3-14 Inner
    ## 15 Component-F
    ## 16 Adhestive/glue-B, 17 Adhestive/glue-F
    ## 18 Solder Paste-B, 19 Solder Paste-F
    ## 20 SilkScreen-B, 21 SilkScreen-F
    ## 22 SolderMask-B, 23 SolderMask-F
    ## 24 Drawings
    ## 25 Comments
    ## 26 ECO1, 27 ECO2
    ## 28 Edge Cuts
    #
    #layers = { -1: ".drl", 0 : "-B_Cu.gbl", 15 : "-F_Cu.gtl", 20 : "-B_SilkS.gbo", 21 : "-F_SilkS.gto", 28 : "-Edge_Cuts.gbr" }
    layers = { -1: ".drl",
                0 : "-B_Cu.gbl",
                1 : "-Inner1_Cu.gbl",
                2 : "-Inner2_Cu.gbl",
                15 : "-F_Cu.gtl",
                20 : "-B_SilkS.gbo",
                21 : "-F_SilkS.gto",
                22 : "-B_SolderM.gbs",
                23 : "-F_SolderM.gts",
                28 : "-Edge_Cuts.gbr" }
    gerber_files = []
    gcode_files = []
    for layer in layers:

      # skip if layer 1 or layer 2 aren't in the layers
      #
      if layer>0 and layer<15 and (layer not in layer_map): continue

      grbr = sp.check_output( [brdgrb_exec, "-i", str(brd_fn), "-L", str(layer), "-F", str(font_file) ] )
      gerber_uid, gerber_fn = dumpToFile( grbr )
      gerber_files.append( { "id": gerber_uid , "filename" : gerber_fn, "layer" : layer } )

      if layer >= 0:
        radius_decithou = "0.002"
        gcode = sp.check_output( [ grbngc_exec, "--radius", radius_decithou, "--input", gerber_fn  ] )
        gcode_uid, gcode_fn = dumpToFile( gcode )
        gcode_files.append( { "id" : gcode_uid, "filename" : gcode_fn, "layer" : layer } )
      else:
        gcode = sp.check_output( [ drlngc_exec, "--input", gerber_fn  ] )
        gcode_uid, gcode_fn = dumpToFile( gcode )
        gcode_files.append( { "id" : gcode_uid, "filename" : gcode_fn, "layer" : layer } )

    projname = "project"

    zip_fn = str(staging_base) + "/" + str(zip_uid)

    # http://stackoverflow.com/questions/9289734/linux-how-to-add-a-file-to-a-specific-folder-within-a-zip-file
    z = zf.ZipFile( str(zip_fn), "a" )
    z.write( sch_json_fn, projname + "/json/schematic.json" )
    z.write( brd_json_fn, projname + "/json/board.json" )
    z.write( sch_fn, projname + "/KiCAD/schematic.sch" )
    z.write( brd_fn, projname + "/KiCAD/board.brd" )
    z.write( kicad_pcb_fn, projname + "/KiCAD/board.kicad_pcb" )

    for f in gerber_files:
      z.write( f["filename"], projname + "/gerber/board" + layers[ int(f["layer"]) ] )

    for f in gcode_files:
      z.write( f["filename"], projname + "/gcode/board" + layers[ int(f["layer"]) ] )

    z.close()

  except Exception as e:
    log_line( "ERROR: " + str(e) )
    error_and_quit()


  obj = { "type": "id", "id" : str(zip_uid), "notes" : "zip project file",
          "name" : json_message["name"] }
  return obj




userId = None
sessionId = None
projectId = None

fields = cgi.FieldStorage()
if ("userId" in fields) and ("sessionId" in fields):
  if mew.authenticateSession( fields["userId"].value, fields["sessionId"].value ):
    userId = fields["userId"].value
    sessionId = fields["sessionId"].value
    if "projectId" in fields:
      projectId = fields["projectId"].value
elif ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash) and
     ( mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 1) ):
    userId = cookie_hash["userId"]
    sessionId = cookie_hash["sessionId"]
    if "projectId" in fields:
      projectId = fields["projectId"].value
elif "projectId" in fields:
  projectId = fields["projectId"].value

#log_line( "u: " + str(userId) )
#log_line( "s: " + str(sessionId) )
#log_line( "p: " + str(projectId) )

if projectId is None:

  log_line( "--> None projectId" )

  error_and_quit()

proj = mew.getProject( projectId )
if proj["permission"] != "world-read":
  if (userId is None) or (userId != proj["userId"]):

    log_line("---> permission error")

    error_and_quit()

snapshot = {}
json_container = {}
try:
  snapshot = mew.getProjectSnapshot( projectId )
  json_container = { "board" : json.loads(snapshot["json_brd"]), 
                     "schematic" : json.loads(snapshot["json_sch"]),
                     "name" : mew.safe_str( proj["name"] ) + ".zip"  }
except Exception as e:

  log_line( "----> loads error: " + str(e) )
  error_and_quit()

obj = readyProjectZipfile( json_container )

print "Content-Type: application/json; charset=utf-8"
print
print json.dumps(obj)






