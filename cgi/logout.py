#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import datetime
import Cookie
import meowaux as mew
cgitb.enable()

cookie_hash = mew.getCookieHash( os.environ )

mew.log( str(cookie_hash) )

if ( ("userId" not in cookie_hash) or ("sessionId" not in cookie_hash)  or
         (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 0) ):
  print "Location:/index"
  print
  sys.exit(0)

userId = cookie_hash["userId"]
sessionId = cookie_hash["sessionId"]
userData = mew.getUser( userId )
userName = userData["userName"]


r = mew.deactivateSession( userId, sessionId )

cookie = Cookie.SimpleCookie()
cookie["message"] = str(userName) + " logged out"

expiration = datetime.datetime.now() + datetime.timedelta(days=-1)
exp_str = expiration.strftime("%a, %d-%b-%Y %H:%M:%S PST")
cookie["userId"] = cookie_hash["userId"]
cookie["userId"]["expires"] = exp_str
cookie["userId"]["path"] = "/"
cookie["sessionId"] = cookie_hash["sessionId"]
cookie["sessionId"]["expires"] = exp_str
cookie["sessionId"]["path"] = "/"
cookie["userName"] = cookie_hash["userName"]
cookie["userName"]["expires"] = exp_str
cookie["userName"]["path"] = "/"

print "Location:index"
print cookie.output()
print


