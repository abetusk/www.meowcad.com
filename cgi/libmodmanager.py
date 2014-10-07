#!/usr/bin/python
#
#  Copyright (C) 2013 Abram Connelly
#
#  This file is part of bleepsix.
#
#  bleepsix is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  bleepsix is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with bleepsix.  If not, see <http://www.gnu.org/licenses/>.
#

# Description
# -----------

# This program manages the JSON location, lists and library/module
# element dispatch.
#
# There are 6 main operations:
#   - COMP_LOC
#   - COMP_LIST
#   - COMP_ELE
#   - MOD_LOC
#   - MOD_LIST
#   - MOD_ELE
#
# (COMP|MOD)_LOC gives the JSON location list
# (COMP|MOD)_LIST gives the JSON set heirarchy
# (COMP|MOD)_ELE gives the JSON component/module
#
# Commands are taken in as a JSON messages as follows
#
# INPUT
# -----
#
# { "op" : ((COMP|MOD)_(LOC|LIST)),
#   "userId" : <userId>,
#   "sesseionId" : <sessionId>
# }
#
#
# INPUT
# -----
# { "op" : ((COMP|MOD)_ELE),
#   "name" : <name>,
#   "location" : <location>
#   "userId" : <userId>,
#   "sesseionId" : <sessionId>
# }
#

import re,cgi,cgitb,sys
import os
import urllib
import meowaux as mew
import Cookie
import json
import os.path

cgitb.enable()

def log_line( l ):
  logf = open("/tmp/meow.log", "a")
  logf.write( l  + "\n")
  logf.close()

def error_and_quit(err, notes = None):
  print "Content-Type: application/json; charset=utf-8"
  print
  ret_obj = { "type" : "error", "message": str(err)  }
  if notes:
    ret_obj["notes"] = notes
  print json.dumps(ret_obj)
  sys.exit(0)


def json_slurp_file(fn):
  data = "{ \"type\" : \"error\", \"reason\" : \"error\" }"
  try:
    with open(fn) as fp:
      data = fp.read()
  except Exception as ee:
    data = "{ \"type\" : \"error\", \"reason\" : \"" + str(ee) + "\" }"
  return data


def comp_loc( userId, projectId ):
  return mew.file_cascade( userId, projectId, os.path.join("json", "component_location.json") )

def comp_list( userId, projectId ):
  return mew.file_cascade( userId, projectId, os.path.join("json", "component_list_default.json") )

def comp_ele( userId, projectId, json_data ):
  loc = urllib.unquote( json_data["location"] )
  return mew.file_cascade( userId, projectId, loc )


def mod_loc( userId, projectId ):
  return mew.file_cascade( userId, projectId, os.path.join("json", "footprint_location.json") )

def mod_list( userId, projectId ):
  return mew.file_cascade( userId, projectId, os.path.join("json", "footprint_list_default.json") )

def mod_ele( userId, projectId, json_data ):
  loc = urllib.unquote( json_data["location"] )
  return mew.file_cascade( userId, projectId, loc )


v = ""

try:
  v = sys.stdin.read()
  json_container = json.loads( v )

except Exception as ee:
  error_and_quit( str(ee) + " (1) " + str(v) )

if ( "op" not in json_container ):
  error_and_quit( "invalid message" )

op = json_container["op"]

userId = None
sessionId = None
projectId = None

if ( ("userId" in json_container) and ("sessionId" in json_container) ):
  if mew.authenticateSession( json_container["userId"], json_container["sessionId"] ):
    userId = json_container["userId"]
    sessionId = json_container["sessionId"]

if "projectId" in json_container:
  projectId = json_container["projectId"]
  p = mew.getProject( projectId )
  if p["permission"] == "world-read":
    userId = p["userId"]

#  elif ( ("sessionId" in json_container) and
#         (userId == p["userId"] ) and
#          mew.authenticateSession( userId, sessionId ) ):
#    userId = p["userId"]


#if ( ( "userId" in json_container ) and
#     ( "sessionId" in json_container) ):
#
#  userId = json_container["userId"]
#  sessionId = json_container["sessionId"]
#
#  if "projectId" in json_container:
#    projectId = json_container["projectId"]
#
#  if not mew.authenticateSession( userId, sessionId ):
#    error_and_quit( "authentication error" )



str_obj = "{ \"type\" : \"error\", \"message\":\"invalid op\" }"
if op   == "COMP_LOC":      str_obj = comp_loc( userId, projectId )
elif op == "COMP_LIST":     str_obj = comp_list( userId, projectId )
elif op == "COMP_ELE":
  if "location" not in json_container:
    error_and_quit( "specify 'location'" )
  str_obj = comp_ele( userId, projectId, json_container )


elif op == "MOD_LOC":       str_obj = mod_loc( userId, projectId )
elif op == "MOD_LIST":      str_obj = mod_list( userId, projectId )
elif op == "MOD_ELE":
  if "location" not in json_container:
    error_and_quit( "specify 'location'" )
  str_obj = mod_ele( userId, projectId, json_container )


elif op == "PIC":
  if "location" not in json_container:
    error_and_quit( "specify 'location'" )

  with open( "/var/www/img/ghost_big.png" ) as f:
    print "Content-Type: image/png"
    print
    print f.read()
  sys.exit(0)


print "Content-Type: application/json; charset=utf-8"
print
print str_obj


