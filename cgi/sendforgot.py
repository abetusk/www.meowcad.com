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

if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 1) ):
  print "Location:portfolio"
  print cookie.output()
  print
  sys.exit(0)

email = ""

form = cgi.FieldStorage()
if "email" not in form:
  cookie["message"] = "Please provide username or email" 
  cookie["messageType"] = "error"
  print "Location:forgot"
  print cookie.output()
  print
  sys.exit(0)

email = form["email"].value
message = ""
if "message" in form:
  message = form["message"].value

r = mew.passwordreset( email, message )

if r:
  cookie["message"] = "Your password reset request has been sent.  Please keep an eye out in or mailbox for the email with instructions on how to reset your password."
  cookie["messageType"] = "success"

  print "Location:sink"
  print cookie.output()
  print

else:
  cookie["message"] = "We're sorry, an error occured!  Please contact as at info@meowcad.com instead!" 
  cookie["messageType"] = "error"
  print "Location:feedback"
  print cookie.output()
  print
  sys.exit(0)


