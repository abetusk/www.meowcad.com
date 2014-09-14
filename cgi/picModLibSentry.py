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
  logf = open("/tmp/picmodlibsentry.log", "a")
  logf.write( l  + "\n")
  logf.close()

def error_and_quit():
  if g_debug:
    log_line("error, quitting")
  print "Status: 404 Not Found"
  print
  print "File not found"
  sys.exit(0)

fields = cgi.FieldStorage()
if "data" not in fields:
  if g_debug:
    log_line("no data")
  error_and_quit()

userId = None
sessionId = None
projectId = None

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

#raw_name = urllib.unquote( fields["data"].value )
raw_name = fields["data"].value
jsfnstr = mew.file_cascade_fn( userId, projectId, raw_name )
jsfn = json.loads( jsfnstr )

if jsfn["type"] != "success":
  log_line( jsfnstr )
  log_line( "raw_name: " + str(raw_name) )
  error_and_quit()

fn = jsfn["filename"]

try:
  with open( fn ) as pic_fd:
    d = pic_fd.read()

  print "Content-Type: image/png"
  print
  print d

except IOError as e:

  if g_debug:
    s_e = str(e)
    log_line("error opening file (2) " + fileId + ", got '" + s_e + "'")
  error_and_quit()

