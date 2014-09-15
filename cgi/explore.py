#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import meowaux as mew
cgitb.enable()


h = {}
form = cgi.FieldStorage()
for k in form:
  h[k] = form[k].value


cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )

loggedInFlag = False
if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 1) ):
  loggedInFlag = True

userId = None
if "userId" in cookie_hash:
  userId = cookie_hash["userId"]

msg,msgType = mew.processCookieMessage( cookie, cookie_hash )

template = mew.slurp_file("template/explore.html")
nav = mew.slurp_file("template/navbar_template.html")
footer = mew.slurp_file("template/footer_template.html")
analytics = mew.slurp_file("template/analytics_template.html")

userData = {}
if loggedInFlag:
  userData = mew.getUser( cookie_hash["userId"] )
  userName = userData["userName"]

  unamestr = "["  + str(userName) + "]"

  if userData["type"] == "anonymous":
    print "Location:/register"
    print cookie.output()
    print
    sys.exit(0)


if loggedInFlag:
  nav = mew.processLoggedInNavTemplate( nav, userData["userName"], userData["type"] )
else:
  nav = mew.loggedOutNavTemplate( nav )

tmp_str = template

tmp_str = mew.replaceTemplateMessage( tmp_str , msg, msgType )

if loggedInFlag:
  tmp_str = tmp_str.replace( "<!--BREADCRUMB-->", mew.breadcrumb( str(userName) ) )
tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )

start = 0
end = 10

if "s" in h: start = h["s"]
if "e" in h: end = h["e"]

explore_table = ""
if loggedInFlag:
  explore_table = mew.constructExploreHTMLList( userId, start, end )
else:
  explore_table = mew.constructExploreHTMLList( None, start, end )

tmp_str = tmp_str.replace( "<!--PROJECT_LISTINGS-->", explore_table )


print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str



