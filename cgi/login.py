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
  print "Location:https://localhost/bleepsix/cgi/portfolio"
  print cookie.output()
  print
  sys.exit(0)


msg = ""

cookie_hash = mew.getCookieHash( os.environ )
if "message" in cookie_hash:
  msg = str(cookie_hash["message"])
  msg = re.sub( '^\s*"', '', msg )
  msg = re.sub( '"\s*$', '', msg )

  expiration = datetime.datetime.now() + datetime.timedelta(days=-1)
  cookie["message"] = ""
  cookie["message"]["expires"] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S PST")

template = mew.slurp_file("../template/login.html")

if len(msg) > 0:
  tmp_str = template.replace("<!--MESSAGE-->", mew.nominalMessage(msg) )
else:
  tmp_str = template.replace("<!--MESSAGE-->", mew.message("") )

print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str



