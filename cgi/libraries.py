#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import datetime
import Cookie
import meowaux as mew
cgitb.enable()

cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )

if ( ("userId" not in cookie_hash) or ("sessionId" not in cookie_hash)  or
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 0) ):
  print "Location:login"
  print
  sys.exit(0)

message,messageType = mew.processCookieMessage( cookie, cookie_hash )

userId = cookie_hash["userId"]
userData = mew.getUser( userId )
userName = userData["userName"]

template = mew.slurp_file("template/libraries.html")
tmp_str = template.replace("<!--USER-->", userName )
tmp_str = tmp_str.replace("<!--USERID-->", userId )
tmp_str = tmp_str.replace( "<!--LEFT-->", mew.slurp_file("template/left_template.html") )
tmp_str = tmp_str.replace( "<!--USERINDICATOR-->", mew.userIndicatorString( userId, userName ) )
tmp_str = mew.replaceTemplateMessage( tmp_str, message, messageType )

print "Content-Type: text/html;charset=utf-8"
print cookie.output()
print
print tmp_str

