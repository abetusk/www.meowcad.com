#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import meowaux as mew
import Cookie
cgitb.enable()

#
#print "Content-type: text/html; charset=utf-8;"
#print

cookie = Cookie.SimpleCookie()

cookie_hash = mew.getCookieHash( os.environ )

if ( ("userId" not in cookie_hash) or ("sessionId" not in cookie_hash)  or
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 0) ):
  cookie["message"] = "Session expired"
  print "Location:https://localhost/bleepsix/cgi/login"
  print cookie.output()
  print
  sys.exit(0)

form = cgi.FieldStorage()
if ("password" not in form) or ("passwordAgain" not in form):
  cookie["message"] = "Passwords must be non-empty " 
  cookie["messageType"] = "error"
  print "Location:https://localhost/bleepsix/cgi/usersettings"
  print cookie.output()
  print
  sys.exit(0)

if form["password"].value != form["passwordAgain"].value:
  cookie["message"] = "Passwords do not match"
  cookie["messageType"] = "error"
  print "Location:https://localhost/bleepsix/cgi/usersettings"
  print cookie.output()
  print
  sys.exit(0)

userId = cookie_hash["userId"]
userData = mew.getUser( userId )
userName = userData["userName"]

password = form["password"].value
if mew.setUserPassword( userId, password ):
  cookie["message"] = "Error occursd"
  cookie["messageType"] = "error"
else:
  cookie["message"] = "Password updated"
  cookie["messageType"] = "success"

print "Location:https://localhost/bleepsix/cgi/usersettings"
print cookie.output()
print
#print tmp_str

