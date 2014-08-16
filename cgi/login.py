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
  <button class='btn btn-warning' type='submit' onclick='location.href="/signup";' >Sign up!</button>
  <!--
    <form action='/signup' style='display:inline;' method='POST' >
      <button class='btn btn-warning' type='submit'>Sign up!</button>
    </form>
    -->
  </li>
</ul>
"""


cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )

if os.environ['REQUEST_METHOD'] == 'POST':
  print "Location:login"
  print cookie.output()
  print
  sys.exit(0)


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

template = mew.slurp_file("template/login.html")

nav = mew.slurp_file("template/navbar_template.html")
nav = nav.replace("<!--NAVBAR_USER_CONTEXT-->", signupform)

footer = mew.slurp_file("template/footer_template.html")
analytics = mew.slurp_file("template/analytics_template.html")

tmp_str = mew.replaceTemplateMessage( template, msg, msgType )

tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )

print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str



