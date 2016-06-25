#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import meowaux as mew
cgitb.enable()


login_signup_nav="""

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

if os.environ['REQUEST_METHOD'] == 'POST':
  print "Location:feedback"
  print cookie.output()
  print
  sys.exit(0)

loggedInFlag = False
if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 1) ):
  loggedInFlag = True

message,messageType = mew.processCookieMessage( cookie, cookie_hash )

template = mew.slurp_file("template/feedback.html")

nav = mew.slurp_file("template/navbar_template.html")

footer = mew.slurp_file("template/footer_template.html")
analytics = mew.slurp_file("template/analytics_template.html")

if loggedInFlag:
  userData = mew.getUser( cookie_hash["userId"] )
  userName = userData["userName"]

  nav = mew.processLoggedInNavTemplate( nav, userData["userName"], userData["type"] )
else:
  nav = nav.replace( "<!--NAVBAR_USER_CONTEXT-->", login_signup_nav )


tmp_str = template
tmp_str = mew.replaceTemplateMessage( template, message, messageType )

tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )


print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str

