#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import meowaux as mew
cgitb.enable()

cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )

loggedInFlag = False
if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 1) ):
  loggedInFlag = True

if not loggedInFlag:
  print "Location:index"
  print cookie.output()
  print
  sys.exit(0)

userId = ""
if "userId" in cookie_hash:
  userId = cookie_hash["userId"]

if os.environ['REQUEST_METHOD'] == 'POST':

  h = {}

  form = cgi.FieldStorage()
  for k in form:
    h[k] = form[k].value


  if ("action" in h) and (h["action"] == "password"):

    if "passwordOrig" not in h:

      cookie["message"] = "No password"
      cookie["messageType"] = "error"
      print "Location:user"
      print cookie.output()
      print
      sys.exit(0)

    if h["password"] != h["passwordAgain"]:

      cookie["message"] = "Password do not match"
      cookie["messageType"] = "error"
      print "Location:user"
      print cookie.output()
      print
      sys.exit(0)

    if not mew.passwordTest( h["password"] ):

      cookie["message"] = "Passwords must be greater than 7 characters long, contain at least one numeral" + \
          " and be of mixed case.  Passwords greater than 20 characters have no restrictions."
      cookie["messageType"] = "error"
      print "Location:user"
      print cookie.output()
      print
      sys.exit(0)


    if mew.userPasswordTest( userId, h["passwordOrig"] ):

      mew.setUserPassword( userId, h["password"] )
      cookie["message"] = "Password updated!"
      cookie["messageType"] = "success"
      print "Location:user"
      print cookie.output()
      print
      sys.exit(0)

    cookie["message"] = "Invalid password"
    cookie["messageType"] = "error"
    print "Location:user"
    print cookie.output()
    print
    sys.exit(0)


  print "Location:user"
  print cookie.output()
  print
  sys.exit(0)


msg,msgType = mew.processCookieMessage( cookie, cookie_hash )

template = mew.slurp_file("template/user.html")

nav = mew.slurp_file("template/navbar_template.html")

footer = mew.slurp_file("template/footer_template.html")
analytics = mew.slurp_file("template/analytics_template.html")

userData = mew.getUser( cookie_hash["userId"] )
userName = userData["userName"]

unamestr = "["  + str(userName) + "]"

if userData["type"] == "anonymous":
  print "Location:/register"
  print cookie.output()
  print
  sys.exit(0)


nav = mew.processLoggedInNavTemplate( nav, userData["userName"], userData["type"] )

tmp_str = template

tmp_str = mew.replaceTemplateMessage( tmp_str , msg, msgType )
tmp_str = tmp_str.replace( "<!--BREADCRUMB-->", mew.breadcrumb( str(userName), userId ) )

tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )


print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str

