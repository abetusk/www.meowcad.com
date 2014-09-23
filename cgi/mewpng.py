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

cgitb.enable();

#print "Content-Type: text/html"
#print

cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )

g_debug = False
def log_line( l ):
  logf = open("/tmp/mewpng.log", "a")
  logf.write( l  + "\n")
  logf.close()

def error_and_quit( e = ""):
  if g_debug:
    log_line("error, quitting")
  print "Status: 404 Not Found"
  print
  print "File not found", e
  sys.exit(0)

fields = cgi.FieldStorage()
if "f" not in fields:
  if g_debug:
    log_line("no data")
  error_and_quit()

raw_fn = fields["f"].value

userId = None
sessionId = None

authenticatedFlag = False
if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash) and
     ( mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 1) ):
    userId = cookie_hash["userId"]
    sessionId = cookie_hash["sessionId"]
    authenticatedFlag = True

viewUserId = userId
viewProjectId = None

if "userId" in fields:
  viewUserId = fields["userId"].value

if "projectId" in fields:
  viewProjectId = fields["projectId"].value

real_fn = None
if userId == viewUserId:
  real_fn_json = json.loads( mew.file_cascade_fn( viewUserId, viewProjectId, raw_fn ) )
  if real_fn_json["type"] == "success":
    real_fn = real_fn_json["filename"]
  else:
    error_and_quit()

else:
  proj = mew.getProject( viewProjectId )
  if proj is None: error_and_quit()

  if proj["permission"] == "world-read":
    real_fn_json = json.loads( mew.file_cascade_fn( viewUserId, viewProjectId, raw_fn ) )
    if real_fn_json["type"] == "success":
      real_fn = real_fn_json["filename"]
    else:
      error_and_quit()
  else:
    error_and_quit( "cp1" )

try:
  with open( real_fn ) as pic_fd:
    d = pic_fd.read()

  print "Content-Type: image/png"
  print
  print d

except IOError as e:

  if g_debug:
    s_e = str(e)
    log_line("error opening file (2) " + fileId + ", got '" + s_e + "'")
  error_and_quit( real_fn )

