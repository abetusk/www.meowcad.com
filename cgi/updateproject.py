#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import meowaux as mew
import Cookie
cgitb.enable()


### DEBUG
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

if "shortDescription" in form:
  descr = form["shortDescription"].value

  userId = cookie_hash["userId"]

  r = mew.updateProjectShortDescription( userId, projectId, descr ) 

  if r is None:
    cookie["message"] = "Error occured"
    cookie["messageType"] = "error"
  else:
    cookie["message"] = "Project updated"
    cookie["messageType"] = "success"

  print "Location:project?projectId=" + str(projectId)
  print cookie.output()
  print
  sys.exit(0)

#if "permissionOption" not in form:
#  cookie["message"] = "Permission option must be non-empty " 
#  cookie["messageType"] = "error"
#  #print "Location:manageproject?projectId=" + str(projectId)
#  print "Location:project?projectId=" + str(projectId)
#  print cookie.output()
#  print
#  sys.exit(0)

if "permissionOption" in form:

  formPerm = form["permissionOption"].value

  perm = "none"
  if formPerm == "public":
    perm = "world-read"
  elif formPerm == "private":
    perm = "user"

  userId = cookie_hash["userId"]
  userData = mew.getUser( userId )
  userName = userData["userName"]

  userData = mew.getUser( userId )

  #if userData["type"] == "user":
  if True:

    r = mew.updateProjectPermission( userId, projectId, perm ) 

    #if mew.updateProjectPermission( userId, projectId, perm ) is None:
    if r is None:
      cookie["message"] = "Error occured"
      cookie["messageType"] = "error"
    else:
      cookie["message"] = "Project updated"
      cookie["messageType"] = "success"

  else:
    cookie["message"] = "Anonymous users cannot update project permissions"
    cookie["messageType"] = "error"

  #print "Location:manageproject?projectId=" + str(projectId)
  print "Location:project?projectId=" + str(projectId)
  print cookie.output()
  print
  #print tmp_str

  sys.exit(0)


cookie["message"] = "Nothing to update"
cookie["messageType"] = "error"

print "Location:project?projectId=" + str(projectId)
print cookie.output()
print
sys.exit(0)

