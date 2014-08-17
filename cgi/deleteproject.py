#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import meowaux as mew
import Cookie
cgitb.enable()


#print "Content-type: text/html; charset=utf-8;"
#print

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
if "projectId" not in form:
  cookie["message"] = "Invalid project ID"
  cookie["messageType"] = "error"
  print "Location:portfolio"
  print cookie.output()
  print
  sys.exit(0)

projectId = form["projectId"].value

userId = cookie_hash["userId"]
userData = mew.getUser( userId )
userName = userData["userName"]

proj = mew.getProject( projectId )

r = mew.deleteProject( userId, projectId ) 

if r is None:
  cookie["message"] = "Error occured"
  cookie["messageType"] = "error"
  print "Location:project?projectId=" + str(projectId)
  print cookie.output()
  print
  sys.exit(0)


cookie["message"] = "Project '" + str(proj["name"]) + "' deleted"
cookie["messageType"] = "status"

print "Location:portfolio"
print cookie.output()
print
#print tmp_str

