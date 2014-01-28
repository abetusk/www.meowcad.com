#!/usr/bin/python

import re
import cgi
import cgitb
import sys
import json
import uuid
import meowaux as mew
import subprocess as sp
from time import sleep

### DEBUG
#print "Content-Type: application/json; charset=utf-8"
#print

cgitb.enable();

#jsonsch_exec = "/tmp/pykicad/jsonsch.py"
#staging_base = "/tmp/stage"

jsonsch_exec = "/home/meow/pykicad/jsonsch.py"
staging_base = "/home/meow/stage"

##########################
#
def log_line( l ):
  #logf = open("/tmp/meowdm.log", "a")
  logf = open("/home/meow/log/meowdm.log", "a")
  logf.write( l  + "\n")
  logf.close()


##########################
#
def error_and_quit(err, notes = None):

  print "Content-Type: application/json"
  print

  ret_obj = { "type" : "error", "message": str(err)  }
  if notes:
    ret_obj["notes"] = notes
  print json.dumps(ret_obj)
  sys.exit(0)


##########################
#
def dumpToFile( data ):

  u_id = uuid.uuid4()
  fn = staging_base + "/" + str(u_id)

  f = open( fn, "w" )
  f.write( data )
  f.close()

  return u_id, fn


##########################
#
def makeKiCADSchematic( json_message ):
  u_id, sch_json_fn = dumpToFile( json.dumps(json_message["data"], indent=2) )

  try:
    kicad_sch = sp.check_output( [jsonsch_exec, sch_json_fn ] );
    u_id, fn  = dumpToFile( kicad_sch )
  except Exception as e:
    error_and_quit(e)

  obj = { "type" : "id", "id" : str(u_id), "notes" : "KiCAD Schematic File ID"  }
  return obj


##########################
#
def makeJSONSchematic( json_message ):
  u_id, sch_json_fn = dumpToFile( json.dumps(json_message["data"], indent=2) )
  obj = { "type" : "id", "id" : str(u_id), "notes" : "JSON KiCAD Schematic File ID"  }
  return obj


##########################
#
def makePNG( json_message ):
  u_id, fn = dumpToFile( str(json_message["data"]) )

  if "clientToken" not in json_message:
    error_and_quit("no client token")

  clientToken = str( json_message["clientToken"] )

  png_uid = uuid.uuid4()
  png_fn = staging_base + "/" + str(png_uid)

  try:
    cut     = sp.Popen( [ "cut", "-f", "2" , "-d", ",", fn], \
        stdout = sp.PIPE )
    base64  = sp.Popen( [ "base64" , "--decode" ], \
        stdin = cut.stdout, stdout = sp.PIPE )
    convert = sp.Popen( [ "convert", "-", "-flatten", "-crop", "900x525+50+50", png_fn ], \
        stdin = base64.stdout, stdout = sp.PIPE )

    if convert.wait() is None:
      error_and_quit( "Popen wait failed", png_fn )

    # it's created, update database
    #
    mew.createPic( png_uid, json_message["userId"], json_message["clientToken"] )

  except Exception as e:
    error_and_quit(e, png_fn);

  obj = { "type" : "id", "id" : str(png_uid), "notes" : "PNG file id" }
  return obj


##########################
#
def startupProject( json_message ):
  userId = json_message["userId"]

  # find the most recent project worked on
  #
  recentProj = mew.getProjectRecent( userId )

  if "project" in recentProj :
    proj = mew.getProject( recentProj["project"] )

    if ("project" in proj) :
      obj = {}
      obj["type"]         = "success"
      obj["notes"]        = "recent project"
      obj["projectId"]    = proj["project"]
      return obj

  # otherwise get the first valid project in the portfolio
  #
  olio = mew.getPortfolios( userId )

  if len(olio) > 0:

    obj = {}
    obj["type"]         = "success"
    obj["notes"]        = "first in portfolio"
    obj["projectId"]    = olio[0]["id"]
    obj["json_sch"]     = olio[0]["json_sch"]
    obj["json_brd"]     = olio[0]["json_brd"]

    return obj

  # otherwise create a new project
  #
  proj = mew.createProject( userId, mew.randomName( "./american-english.json", 3 ), "user" )

  obj = {} 
  obj["type"]           = "success"
  obj["notes"]          = "could not find recent project or a project in the portfolio"
  obj["projectId"]      = proj["id"]

  return obj


##########################
#
#  Main dispatch
#

try:
  json_container = json.load(sys.stdin);
except Exception as e:
  error_and_quit(e)

if ( ( "userId" not in json_container ) or
     ( "sessionId" not in json_container ) or
     ( "type" not in json_container ) or
     ( "data" not in json_container) ):
  error_and_quit( "invalid message" )

userId = json_container["userId"]
sessionId = json_container["sessionId"]

if not mew.authenticateSession( userId, sessionId ):
  error_and_quit( "authentication error" )

msg_type = json_container["type"]

obj = { "type" : "error" , "message" : "invalid function" }
if msg_type == "createKiCADSchematic":
  obj = makeKiCADSchematic( json_container )
elif msg_type == "createJSONSchematic":
  obj = makeJSONSchematic( json_container )
elif msg_type == "createPNG":
  obj = makePNG( json_container );
elif msg_type == "startupProject":
  obj = startupProject( json_container )

s = "nothing"
args = cgi.FieldStorage()
for i in args.keys():
  s += ", " + str(i) + " " + str( args[i].value )

obj["args"] = s

print "Content-Type: application/json; charset=utf-8"
print
print json.dumps(obj)


#print "Content-Type: text/html;charset=utf-8"
#print
#form = cgi.FieldStorage()
#for key in form :
#  s += str(key) + str(form[key].value) + ":::"

