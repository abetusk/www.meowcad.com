#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import datetime
import meowaux as mew
cgitb.enable()

signupform = """
<ul class='nav navbar-nav' style='float:right; margin-top:7px;' >
  <li>
    <form action='/signup' style='display:inline;' method='POST' >
      <button class='btn btn-warning' type='submit'>Sign up!</button>
    </form>
  </li>
</ul>
"""


cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )

if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash) and
      mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) ):
  cookie["message"] = "Already logged in"
  cookie["messageType"] = "status"
  print "Location:portfolio"
  print cookie.output()
  print
  sys.exit(0)


cookie_hash = mew.getCookieHash( os.environ )
msg,msgType = mew.processCookieMessage( cookie, cookie_hash )

template = mew.slurp_file("test/login.html")
nav = mew.slurp_file("test/navbar_template.html")
nav = nav.replace("<!--NAVBAR_USER_CONTEXT-->", signupform)
footer = mew.slurp_file("test/footer_template.html")
analytics = mew.slurp_file("test/analytics_template.html")

tmp_str = mew.replaceTemplateMessage( template, msg, "nominal" )
#tmp_str = tmp_str.replace( "<!--LEFT-->", mew.slurp_file("template/left_template_world.html") )

tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )

print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str



