#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import meowaux as mew
import Cookie
cgitb.enable()

#### DEBUG
#print "Content-Type: text/html;charset=utf-8"
#print



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

email = ""
if "email" in form:
  email = form["email"].value


userId = -1
if loggedInFlag:
  userId = cookie_hash["userId"]

feedback = form["feedback"].value

r = mew.feedback( userId, email, feedback )

if r:
  cookie["message"] = "Thank you!  Your feedback has been sent!"
  cookie["messageType"] = "success"

  if loggedInFlag:
    print "Location:portfolio"
  else:
    print "Location:register"
  print cookie.output()
  print

else:
  cookie["message"] = "We're sorry, an error occured!  Please contact as at info@meowcad.com instead!" 
  cookie["messageType"] = "error"
  print "Location:feedback"
  print cookie.output()
  print
  sys.exit(0)


