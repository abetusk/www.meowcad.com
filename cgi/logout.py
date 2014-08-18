#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import datetime
import Cookie
import meowaux as mew
cgitb.enable()

# http://stackoverflow.com/questions/5411538/how-to-redirect-from-an-html-page
#  answered Mar 23 '11 at 21:04 Billy Moon
#
redirect = """
<!DOCTYPE HTML>
<html lang="en-US">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="1;url=/">
        <script type="text/javascript">
            window.location.href = "/";
        </script>
        <title>Page Redirection</title>
    </head>
    <body>
        <!-- Note: don't tell people to `click` the link, just tell them that it is a link. -->
        If you are not redirected automatically, follow the <a href='/'>link.</a>
    </body>
</html>
"""

cookie_hash = mew.getCookieHash( os.environ )

if ( ("userId" not in cookie_hash) or ("sessionId" not in cookie_hash)  or
         (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 0) ):
  print "Location:/index"
  print
  sys.exit(0)

userId = cookie_hash["userId"]
sessionId = cookie_hash["sessionId"]
userData = mew.getUser( userId )
userName = userData["userName"]

r = mew.deactivateSession( userId, sessionId )

cookie = Cookie.SimpleCookie()
cookie["message"] = str(userName) + " logged out"

expiration = datetime.datetime.now() + datetime.timedelta(days=-1)
exp_str = expiration.strftime("%a, %d-%b-%Y %H:%M:%S PST")

if "userId" in cookie_hash:
  cookie["userId"] = cookie_hash["userId"]
  cookie["userId"]["expires"] = exp_str
  cookie["userId"]["path"] = "/"

if "sessionId" in cookie_hash:
  cookie["sessionId"] = cookie_hash["sessionId"]
  cookie["sessionId"]["expires"] = exp_str
  cookie["sessionId"]["path"] = "/"

if "userName" in cookie_hash:
  cookie["userName"] = cookie_hash["userName"]
  cookie["userName"]["expires"] = exp_str
  cookie["userName"]["path"] = "/"

print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print redirect

#print "Location:/index"
#print cookie.output()
#print


