#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import meowaux as mew
cgitb.enable()

cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )

loggedInFlag = False
if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 1) ):
  loggedInFlag = True

message,messageType = mew.processCookieMessage( cookie, cookie_hash )

template = mew.slurp_file("template/feedback.html")


if loggedInFlag:
  userId = cookie_hash["userId"]
  userData = mew.getUser( userId )
  userName = userData["userName"]

  #tmp_str = template.replace("<!--USER-->", userName)
  #tmp_str = tmp_str.replace( "<!--LEFT-->", mew.slurp_file("template/left_template.html") )

  if userData["type"] == "anonymous":
    tmp_str = template.replace( "<!--LEFT-->", mew.slurp_file("template/left_template_anonymous.html") )
  else:
    tmp_str = template.replace( "<!--LEFT-->", mew.slurp_file("template/left_template.html") )

  tmp_str = tmp_str.replace( "<!--USERINDICATOR-->", mew.userIndicatorString( userId, userName ) )
else:
  a = "<a href='login'>[Login]</a> &nbsp; &nbsp; &nbsp; &nbsp; <a href='signup'>Signup</a>"

  tmp_str = template.replace( "<!--LEFT-->", mew.slurp_file("template/left_template_world.html") )
  tmp_str = tmp_str.replace( "<!--USERINDICATOR-->", a )
tmp_str = mew.replaceTemplateMessage( tmp_str, message, messageType )


print "Content-Type: text/html;charset=utf-8"
print cookie.output()
print
print tmp_str

