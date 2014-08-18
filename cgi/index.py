#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import datetime
import meowaux as mew
cgitb.enable()

signupnav="""
<form class="navbar-form navbar-right" role='form' action='/register' method='POST'>
<div class='form-group'>
<button class='btn btn-warning' type='submit'>Register!</button>
</div>
</form>
"""

login_signup_nav="""

<ul class='nav navbar-nav' style='float:right; margin-top:7px;' >
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

#"""
#<form class="navbar-form navbar-right" role='form' action='/login' method='POST'>
#<div class='form-group'>
#<!-- <input type="text" size='8' class="form-control" placeholder="Username"> -->
#<!-- <input type="password" size='12' class="form-control" placeholder="Password"> -->
#<button class='btn btn-success' type='submit'>Login</button>
#</div>
#</form>
#"""


cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )


loggedInFlag = False
if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) != 0) ):
  loggedInFlag = True

msg,msgType = mew.processCookieMessage( cookie, cookie_hash )

template = mew.slurp_file("template/landing.html")
tmp_str = mew.replaceTemplateMessage( template, msg, "nominal" )


nav = mew.slurp_file("template/navbarflush_template.html")
footer = mew.slurp_file("template/footer_template.html")
analytics = mew.slurp_file("template/analytics_template.html")


tmp_str = mew.replaceTemplateMessage( template, msg, "nominal" )
tmp_str = tmp_str.replace( "<!--FOOTER-->", footer)
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics)

if loggedInFlag:
  userData = mew.getUser( cookie_hash["userId"] )
  userName = userData["userName"]

  unamestr = "[" + str(userName) + "]"

  if userData["type"] == "anonymous":
    unamestr = "&lt; " + str(userName) + " &gt;"
    nav = nav.replace( "<!--NAVBAR_USER_CONTEXT-->", signupnav)
  else:
    nav = nav.replace( "<!--NAVBAR_USER_CONTEXT-->",
        "<ul class=\"nav navbar-nav navbar-right\"> <li><a href='/logout'>Logout</a></li> </ul>")

  nav = nav.replace( "<!--NAVBAR_USER_DISPLAY-->",
      "<ul class=\"nav navbar-nav\"> <li><a href=\"/user\">" + unamestr + "</a></li> </ul>")
else:
  nav = nav.replace( "<!--NAVBAR_USER_CONTEXT-->", login_signup_nav)

tmp_str = tmp_str.replace( "<!--NAVBAR_FLUSH-->", nav)

print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str



