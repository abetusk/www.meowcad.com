#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import meowaux as mew
cgitb.enable()

signup="""
<ul class='nav navbar-nav' style='float:right; margin-top:7px;' >
  <li>

    <form action='/signup' style='display:inline;' method='POST' >
      <button class='btn btn-warning' type='submit'>Sign up!</button>
    </form>

  </li>
</ul>
"""


login_signup_nav="""

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

loginform = """
<ul class='nav navbar-nav' style='float:right; margin-top:7px;' >
  <li>
    <form action='/login' style='display:inline;' method='POST' >
      <button class='btn btn-success' type='submit'>Log in</button>
    </form>
  </li>
</ul>
"""

cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )


loggedInFlag = False
if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 1) ):
  loggedInFlag = True

message,messageType = mew.processCookieMessage( cookie, cookie_hash )

messageTitle = "&nbsp;"
if len(message)==0:
  message = "<p style='text-align:center;'><img src='/img/icecream.png' style='opacity:0.5;' width='50%' ></img></p>"

template = mew.slurp_file("template/sink.html")

nav = mew.slurp_file("template/navbar_template.html")

footer = mew.slurp_file("template/footer_template.html")
analytics = mew.slurp_file("template/analytics_template.html")

if loggedInFlag:
  userData = mew.getUser( cookie_hash["userId"] )
  userName = userData["userName"]

  unamestr = "["  + str(userName) + "]"

  if userData["type"] == "anonymous":
    unamestr = "&lt; " + str(userName) + " &gt;"
    nav = nav.replace( "<!--NAVBAR_USER_CONTEXT-->", signup )
  else:
    nav = nav.replace( "<!--NAVBAR_USER_CONTEXT-->", 
        "<ul class=\"nav navbar-nav navbar-right\"> <li><a href='/logout/" + str(userData["id"]) + "'>Logout</a></li> </ul>")

  nav = nav.replace( "<!--NAVBAR_USER_DISPLAY-->",
      "<ul class=\"nav navbar-nav\"> <li><a href=\"/user/" + str(userData["id"]) + "\">" + unamestr + "</a></li> </ul>")
else:
  nav = nav.replace( "<!--NAVBAR_USER_CONTEXT-->", login_signup_nav )



tmp_str = template
#tmp_str = mew.replaceTemplateMessage( template, msg, "nominal" )

tmp_str = tmp_str.replace( "<!--SINK_TITLE-->", messageTitle )
tmp_str = tmp_str.replace( "<!--SINK_MESSAGE-->", message )
tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )


print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str

