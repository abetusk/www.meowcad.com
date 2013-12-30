#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import meowaux as mew
cgitb.enable()

cookie_hash = mew.getCookieHash( os.environ )

if ( ("userId" not in cookie_hash) or ("sessionId" not in cookie_hash)  or
         (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 0) ):
  print "Location:https://localhost/bleepsix/cgi/login"
  print
  sys.exit(0)

userId = cookie_hash["userId"]
sessionId = cookie_hash["sessionId"]
userData = mew.getUser( userId )
userName = userData["userName"]

r = mew.deactivateSession( userId, sessionId )

cookie = Cookie.SimpleCookie()
cookie["message"] = str(userName) + " logged out"

#print "Content-type: text/html; charset=utf-8;"
print "Location:https://localhost/bleepsix/cgi/login"
print cookie.output()
print


