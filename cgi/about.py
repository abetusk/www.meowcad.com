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

msg,msgType = mew.processCookieMessage( cookie, cookie_hash )

loggedInFlag = False
if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) != 0) ):
  loggedInFlag = True


template = mew.slurp_file("template/about.html")
tmp_str = mew.replaceTemplateMessage( template, msg, "nominal" )
tmp_str = template.replace( "<!--LEFT-->", mew.slurp_file("template/left_template_world.html") )

if loggedInFlag:
  userData = mew.getUser( cookie_hash["userId"] )
  userName = userData["userName"]
  tmp_str = tmp_str.replace("<!--USERINDICATOR-->", mew.userIndicatorString( cookie_hash["userId"], userName ) )
else:
  tmp_str = tmp_str.replace("<!--USERINDICATOR-->", "<a href='login'>[Login]</a> &nbsp; &nbsp; &nbsp; &nbsp; <a href='signup'>Signup</a>")

#tmp_str = tmp_str.replace( "<!--LEFT-->", mew.slurp_file("template/left_template.html") )


print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str



