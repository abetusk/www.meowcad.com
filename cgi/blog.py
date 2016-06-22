#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import datetime
import meowaux as mew
cgitb.enable()

login_signup="""
<ul class='nav navbar-nav' style='float:right; margin-top:7px; margin-right:5px; ' >
  <li>

    <form action='/login' style='display:inline;' >
      <button class='btn btn-success' type='submit'>Log in</button>
    </form>

    <form action='/register' style='display:inline;' >
      <button class='btn btn-warning' type='submit'>Register!</button>
    </form>

  </li>
</ul>
"""

cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )

msg,msgType = mew.processCookieMessage( cookie, cookie_hash )

loggedInFlag = False
if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) != 0) ):
  loggedInFlag = True

template = mew.slurp_file("template/blog.html")

nav = mew.slurp_file("template/navbarflush_template.html")
footer = mew.slurp_file("template/footer_template.html")
analytics = mew.slurp_file("template/analytics_template.html")


tmp_str = mew.replaceTemplateMessage( template, msg, "nominal" )
tmp_str = tmp_str.replace( "<!--FOOTER-->", footer)
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics)

if loggedInFlag:
  userData = mew.getUser( cookie_hash["userId"] )
  nav = mew.processLoggedInNavTemplate( nav, userData["userName"], userData["type"] )
else:
  nav = nav.replace( "<!--NAVBAR_USER_CONTEXT-->", login_signup )


tmp_str = tmp_str.replace( "<!--NAVBAR_FLUSH-->", nav)


print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str



