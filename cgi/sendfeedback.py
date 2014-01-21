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
if "feedback" not in form:
  cookie["message"] = "Please provide feedback text" 
  cookie["messageType"] = "error"
  print "Location:newproject"
  print cookie.output()
  print
  sys.exit(0)


userId = cookie_hash["userId"]
feedback = form["feedback"].value

mew.feedback( userId, feedback )

cookie["message"] = "Feedback sent"
cookie["messageType"] = "success"

print "Location:feedbacksent"
print cookie.output()
print
#print tmp_str

