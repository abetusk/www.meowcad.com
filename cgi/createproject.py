#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import meowaux as mew
import Cookie
cgitb.enable()


cookie = Cookie.SimpleCookie()

cookie_hash = mew.getCookieHash( os.environ )

if ( ("userId" not in cookie_hash) or ("sessionId" not in cookie_hash)  or
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 0) ):
  cookie["message"] = "Session expired"
  print "Location:login"
  print cookie.output()
  print
  sys.exit(0)

form = cgi.FieldStorage()
if ("name" not in form) :
  cookie["message"] = "Provide a project name" 
  cookie["messageType"] = "error"
  print "Location:portfolio"
  print cookie.output()
  print
  sys.exit(0)

projectName = form["name"].value

permission = "user"
if ("permissionOption" in form) and (form["permissionOption"].value == "public"):
  permission = "world-read"

userId = cookie_hash["userId"]
userData = mew.getUser( userId )
userName = userData["userName"]

proj = mew.createProject( userId, projectName, permission )
if proj is None:
  cookie["message"] = "Error occured"
  cookie["messageType"] = "error"
  print "Location:portfolio"
  print cookie.output()
  print
  sys.exit(0)


cookie["message"] = "Project created"
cookie["messageType"] = "success"

#print "Location:manageproject?projectId=" + str(proj["id"])
#print "Location:project?projectId=" + str(proj["id"])
print "Location:portfolio"
print cookie.output()
print
#print tmp_str

