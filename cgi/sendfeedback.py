#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import meowaux as mew
import Cookie
cgitb.enable()


cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )

loggedInFlag = False
if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 1) ):
  loggedInFlag = True


form = cgi.FieldStorage()
if "feedback" not in form:
  cookie["message"] = "Please provide feedback text" 
  cookie["messageType"] = "error"
  print "Location:feedback"
  print cookie.output()
  print
  sys.exit(0)


userId = -1
if loggedInFlag:
  userId = cookie_hash["userId"]

feedback = form["feedback"].value

mew.feedback( userId, feedback )

cookie["message"] = "Feedback sent"
cookie["messageType"] = "success"

print "Location:feedbacksent"
print cookie.output()
print

