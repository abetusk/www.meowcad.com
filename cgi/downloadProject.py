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

brdgrb_exec = "/home/meow/pykicad/brdgerber.py"
grbngc_exec = "/home/meow/bin/gbl2ngc"
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
    zip_uid = uuid.uuid4()


    # Put json data structures into files
    #
    sch_json_uid, brd_json_fn = dumpToFile( json.dumps(json_message["board"], indent=2) )
    brd_json_uid, sch_json_fn = dumpToFile( json.dumps(json_message["schematic"], indent=2) )

    log_line( "brd: " + brd_json_fn )
    log_line( "sch: " + sch_json_fn )

    # Create KiCAD schematic and board files
    #
    kicad_sch = sp.check_output( [jsonsch_exec, sch_json_fn ] );
    sch_uid, sch_fn  = dumpToFile( kicad_sch )

    kicad_brd = sp.check_output( [jsonbrd_exec, brd_json_fn ] );
    brd_uid, brd_fn = dumpToFile( kicad_brd )

    # Go through relevant layers and create gerber and gcode files for each
    #
    layers = { -1: ".drl", 0 : "-B_Cu.gbl", 15 : "-F_Cu.gtl", 20 : "-B_SilkS.gbo", 21 : "-F_SilkS.gto", 28 : "-Edge_Cuts.gbr" }
    gerber_files = []
    gcode_files = []
    for layer in layers:

      grbr = sp.check_output( [brdgrb_exec, str(brd_fn), str(layer), str(font_file) ] )
      gerber_uid, gerber_fn = dumpToFile( grbr )
      gerber_files.append( { "id": gerber_uid , "filename" : gerber_fn, "layer" : layer } )

      radius_decithou = "0.002"
      gcode = sp.check_output( [ grbngc_exec, "--radius", radius_decithou, "--input", gerber_fn  ] )
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


    for f in gerber_files:
      z.write( f["filename"], projname + "/gerber/board" + layers[ int(f["layer"]) ] )

    for f in gcode_files:
      z.write( f["filename"], projname + "/gcode/board" + layers[ int(f["layer"]) ] )

    z.close()

  except Exception as e:
    error_and_quit(e, "...")


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

if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash) and
     ( mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 1) ):
    userId = cookie_hash["userId"]
    sessionId = cookie_hash["sessionId"]
    if "projectId" in fields:
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






