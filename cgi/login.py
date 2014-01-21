#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import datetime
import meowaux as mew
cgitb.enable()

cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )

if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash) and
      mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) ):
  cookie["message"] = "Already logged in"
  cookie["messageType"] = "status"
  print "Location:portfolio"
  print cookie.output()
  print
  sys.exit(0)


cookie_hash = mew.getCookieHash( os.environ )
msg,msgType = mew.processCookieMessage( cookie, cookie_hash )

template = mew.slurp_file("template/login.html")

tmp_str = mew.replaceTemplateMessage( template, msg, "nominal" )

print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str



