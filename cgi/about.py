#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import datetime
import meowaux as mew
cgitb.enable()

login_signup="""
<ul class='nav navbar-nav' style='float:right; margin-top:7px;' >
  <li>

    <form action='/login' style='display:inline;' >
      <button class='btn btn-success' type='submit'>Log in</button>
    </form>

    <form action='/signup' style='display:inline;' >
      <button class='btn btn-warning' type='submit'>Sign up!</button>
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

template = mew.slurp_file("test/about.html")

nav = mew.slurp_file("test/navbarflush_template.html")
footer = mew.slurp_file("test/footer_template.html")
analytics = mew.slurp_file("test/analytics_template.html")


tmp_str = mew.replaceTemplateMessage( template, msg, "nominal" )
tmp_str = tmp_str.replace( "<!--FOOTER-->", footer)
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics)

if loggedInFlag:
  userData = mew.getUser( cookie_hash["userId"] )
  userName = userData["userName"]

  unamestr = str(userName)

  #tmp_str = tmp_str.replace("<!--USERINDICATOR-->", mew.userIndicatorString( cookie_hash["userId"], userName ) )
  if userData["type"] == "anonymous":
    unamestr = "<" + unamestr + ">"
    nav = nav.replace( "<!--NAVBAR_USER_CONTEXT-->", "Sign up!" )
  else:
    nav = nav.replace( "<!--NAVBAR_USER_CONTEXT-->", 
        "<ul class=\"nav navbar-nav navbar-right\"> <li><a href='/logout/" + str(userData) + "'>Logout</a></li> </ul>")


    #tmp_str = tmp_str.replace( "<!--LEFT-->", mew.slurp_file("template/left_template_anonymous.html") )
  #else:
  #  tmp_str = tmp_str.replace( "<!--LEFT-->", mew.slurp_file("template/left_template.html") )

  nav = nav.replace( "<!--NAVBAR_USER_DISPLAY-->", 
      "<ul class=\"nav navbar-nav\"> <li><a href=\"/user/" + str(userData) + "\">[" + unamestr + "]</a></li> </ul>")


else:
  nav = nav.replace( "<!--NAVBAR_USER_CONTEXT-->", login_signup )

  #tmp_str = tmp_str.replace("<!--USERINDICATOR-->", "<a href='login'>[Login]</a> &nbsp; &nbsp; &nbsp; &nbsp; <a href='signup'>Signup</a>")
  #tmp_str = tmp_str.replace( "<!--LEFT-->", mew.slurp_file("template/left_template_world.html") )

tmp_str = tmp_str.replace( "<!--NAVBAR_FLUSH-->", nav)

#tmp_str = tmp_str.replace( "<!--LEFT-->", mew.slurp_file("template/left_template.html") )


print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str



