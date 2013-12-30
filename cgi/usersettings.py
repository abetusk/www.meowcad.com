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
  print "Location:https://localhost/bleepsix/cgi/login"
  print
  sys.exit(0)

message = ""
messageType = "none"
if "message" in cookie_hash:
  message = cookie_hash["message"]
  message = re.sub( '^\s*"', '', message );
  message = re.sub( '"\s*$', '', message );
  if "messageType" in cookie_hash:
    messageType = cookie_hash["messageType"]

  expiration = datetime.datetime.now() + datetime.timedelta(days=-1)
  cookie["message"] = ""
  cookie["message"]["expires"] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S PST")

userId = cookie_hash["userId"]
userData = mew.getUser( userId )
userName = userData["userName"]

template = mew.slurp_file("../template/usersettings.html")
tmp_str = template.replace("<!--USER-->", userName )
tmp_str = tmp_str.replace("<!--USERID-->", userId )
tmp_str = tmp_str.replace( "<!--LEFT-->", mew.slurp_file("../template/left_template.html") )
tmp_str = tmp_str.replace( "<!--USERINDICATOR-->", mew.userIndicatorString( userId, userName ) )

if messageType == 'error':
  tmp_str = tmp_str.replace( "<!--MESSAGE-->", mew.errorMessage( message ) )
elif messageType == 'success':
  tmp_str = tmp_str.replace( "<!--MESSAGE-->", mew.successMessage( message ) )
else:
  tmp_str = tmp_str.replace( "<!--MESSAGE-->", mew.message( message ) )


print "Content-Type: text/html;charset=utf-8"
print cookie.output()
print
print tmp_str

