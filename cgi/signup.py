#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import datetime
import meowaux as mew
cgitb.enable()

loginform = """
<ul class='nav navbar-nav' style='float:right; margin-top:7px;' >
  <li>
    <form action='/login' style='display:inline;' >
      <button class='btn btn-success' type='submit'>Log in</button>
    </form>
  </li>
</ul>
"""

cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )

loggedInFlag = False
if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) != 0) ):
  loggedInFlag = True

msg,msgType = mew.processCookieMessage( cookie, cookie_hash )

template = mew.slurp_file("test/signup.html")

nav = mew.slurp_file("test/navbar_template.html")

if not loggedInFlag:
  nav = nav.replace("<!--NAVBAR_USER_CONTEXT-->", loginform )

footer = mew.slurp_file("test/footer_template.html")
analytics = mew.slurp_file("test/analytics_template.html")


tmp_str = mew.replaceTemplateMessage( template, msg, "nominal" )

tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )


print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str



