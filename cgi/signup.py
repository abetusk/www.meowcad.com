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

loggedInFlag = False
if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) != 0) ):
  loggedInFlag = True



msg,msgType = mew.processCookieMessage( cookie, cookie_hash )

#msg = ""
#if "message" in cookie_hash:
#  msg = str(cookie_hash["message"])
#  msg = re.sub( '^\s*"', '', msg )
#  msg = re.sub( '"\s*$', '', msg )
#
#  expiration = datetime.datetime.now() + datetime.timedelta(days=-1)
#  cookie["message"] = ""
#  cookie["message"]["expires"] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S PST")


#template = mew.slurp_file("../template/signup.html")
template = mew.slurp_file("template/signup.html")
tmp_str = mew.replaceTemplateMessage( template, msg, "nominal" )


#if len(msg) > 0:
#  tmp_str = template.replace("<!--MESSAGE-->", mew.nominalMessage(msg) )
#else:
#  tmp_str = template.replace("<!--MESSAGE-->", mew.message("") )


if loggedInFlag:
  userData = mew.getUser( cookie_hash["userId"] )
  userName = userData["userName"]
  tmp_str = tmp_str.replace("<!--USERINDICATOR-->", mew.userIndicatorString( cookie_hash["userId"], userName ) )
else:
  #tmp_str = tmp_str.replace("<!--USERINDICATOR-->", "<a href='login'>[Login]</a> &nbsp; &nbsp; &nbsp; &nbsp; <a href='signup'>Signup</a>")
  tmp_str = tmp_str.replace("<!--USERINDICATOR-->", "<a href='login'>[Login]</a> &nbsp; &nbsp; &nbsp; &nbsp; Signup")


print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str



