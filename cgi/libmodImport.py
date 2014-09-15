#!/usr/bin/python

import re
import cgi
import cgitb
import sys
import json
import uuid
import subprocess as sp
import Cookie
import redis
import meowaux as mew
import os

cgitb.enable();

staging_base = "/home/meow/stage"

u_id = -1


print "Content-Type: application/json"
print


cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )
if ( ("userId" not in cookie_hash) or ("sessionId" not in cookie_hash)  or
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 0) ):
  print "{ \"type\" : \"error\", \"message\" : \"Authentication failure\" }"
  sys.exit(0)

def log_line(s):
  flog = open( "/tmp/modlibImport.log", "a")
  flog.write( s )
  flog.close()


form = cgi.FieldStorage()

if "fileData" not in form:
  print "{ \"type\" : \"error\", \"message\" : \"'fileData' not in form\" }"
  sys.exit(0)

projectId = None
if "projectId" in form:
  #log_line( "got project " + str(form.getvalue("projectId")) + "\n" )
  pass
else:
  #log_line( "no projectId (ok)\n" ) 
  pass

if "fileData" in form:

  typ = form.getvalue("type")

  u_id = uuid.uuid4()
  fn = staging_base + "/" + str(u_id)
  f = open( fn, "wb" )
  f.write( form.getvalue('fileData') )
  f.close()

  fileName = str(u_id)
  #if "fileName" in form:
  #  fileName = form["fileName"].value

  ## FUCKING STUPIDITY.
  # RIP OUT THAT FUCKING JQUERY.UPLOADFILE.JS AS SOON
  # AS FUCKING POSSIBLE
  #if "fileNames" in form:
  #  fileName = str(form.getvalue("fileNames"))
  if "FORCEDFILE" in form:
    fileName = str(form.getvalue("FORCEDFILE"))

  qid = mew.queueImport( cookie_hash["userId"], cookie_hash["sessionId"], projectId, str(u_id), fileName )

  try:
    print "{ \"type\" : \"success\", \"message\" : \"" + str(u_id) + "\", \"queueId\": \"" + qid + "\"  }"
  except Exception as e:
    print "{ \"type\" : \"error\", \"message\" : \"" + str(e) + "\" }"
    





