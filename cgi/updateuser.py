#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import hashlib
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
if ("password" not in form) or ("passwordAgain" not in form) or ("passwordOrig" not in form):
  cookie["message"] = "All passwords must be non-empty " 
  cookie["messageType"] = "error"
  print "Location:usersettings"
  print cookie.output()
  print
  sys.exit(0)

if form["password"].value != form["passwordAgain"].value:
  cookie["message"] = "Passwords do not match"
  cookie["messageType"] = "error"
  print "Location:usersettings"
  print cookie.output()
  print
  sys.exit(0)

userId = cookie_hash["userId"]
userData = mew.getUser( userId )
userName = userData["userName"]

passOrig = form["passwordOrig"].value

passHash = hashlib.sha512( str(userId) + str(passOrig) ).hexdigest()
if passHash != userData["passwordHash"]:
  cookie["message"] = "Authorization failed"
  cookie["messageType"] = "error"
  print "Location:usersettings"
  print cookie.output()
  print
  sys.exit(0)




password = form["password"].value
if mew.setUserPassword( userId, password ):
  cookie["message"] = "Error occured"
  cookie["messageType"] = "error"
else:
  cookie["message"] = "Password updated"
  cookie["messageType"] = "success"

print "Location:usersettings"
print cookie.output()
print
#print tmp_str

