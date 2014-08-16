#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import datetime
import meowaux as mew
cgitb.enable()

stickyUsername = ""
stickyEmail = ""

def processSignup(ch):

  if "username" not in ch: return False, "badusername", "Please provide a username"
  if "password" not in ch: return False, "badpassword", "Please provide a password"

  username = ch["username"]
  password = ch["password"]

  if len( username ) == 0: return False, "badusername", "The username field is empty"
  if len( password ) == 0: return False, "badpassword","The password field is empty"

  x = mew.getUserName( username )

  if x:
    return False, "badusername", "We're sorry, but the username '" + str(username) + "' is already taken!"

  if not mew.passwordTest( password ):
    return False, "badpassword", "Passwords must be at least 7 charactesr long with numerals and mixed case or be longer than 20 characters."

  user = mew.createUser( username, password )

  if ("email" in ch) and len(ch["email"]) > 0:
    mew.addemail( user["id"], ch["email"] )

  return True, "ok", user["id"]


signup="""
<ul class='nav navbar-nav' style='float:right; margin-top:7px;' >
  <li>

    <form action='/signup' style='display:inline;' method='POST' >
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

if os.environ['REQUEST_METHOD'] == 'POST':

  form = cgi.FieldStorage()

  h = {}
  for k in form:
    h[k] = form[k].value

  v,typ,x = processSignup(h)
  if v:
    userId = x
    mew.createProject( userId, "My-New-Project", "user" )
    cookie["message"] = "Welcome to MeowCAD!  Please login to continue!"
    cookie["messageType"] = "success"

    print "Location:login"
    print cookie.output()
    print
    sys.exit(0)

  cookie["message"] = x
  cookie["messageType"] = "error"

  if (typ == "badpassword") and ("username" in h) and (len(h["username"]) > 0):
    cookie["signup_username"] = h["username"]
  else:
    mew.expireCookie( cookie, "signup_username" )

  if ("email" in h) and (len(h["email"]) > 0):
    cookie["signup_email"] = h["email"]
  else:
    mew.expireCookie( cookie, "signup_email" )

  if typ == "badusername":
    cookie["signup_focus"] = "username"
  elif typ == "badpassword":
    cookie["signup_focus"] = "password"
  else:
    cookie["signup_focus"] = "username"

  print "Location:signup"
  print cookie.output()
  print
  sys.exit(0)


loggedInFlag = False
if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) != 0) ):
  loggedInFlag = True

msg,msgType = mew.processCookieMessage( cookie, cookie_hash )

template = mew.slurp_file("template/signup.html")

nav = mew.slurp_file("template/navbar_template.html")

if not loggedInFlag:
  nav = nav.replace("<!--NAVBAR_USER_CONTEXT-->", loginform )

footer = mew.slurp_file("template/footer_template.html")
analytics = mew.slurp_file("template/analytics_template.html")

if loggedInFlag:
  userData = mew.getUser( cookie_hash["userId"] )
  userName = userData["userName"]

  unamestr = "["  + str(userName) + "]"

  if userData["type"] == "anonymous":
    unamestr = "&lt; " + str(userName) + " &gt;"
  else:
    print "Location:portfolio"
    print cookie.output()
    print
    sys.exit(0)

  nav = nav.replace( "<!--NAVBAR_USER_DISPLAY-->", 
      "<ul class=\"nav navbar-nav\"> <li><a href=\"/user/" + str(userData["id"]) + "\">" + unamestr + "</a></li> </ul>")
else:
  nav = nav.replace( "<!--NAVBAR_USER_CONTEXT-->", loginform )



tmp_str = mew.replaceTemplateMessage( template, msg, msgType )

tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )

if "signup_username" in cookie_hash:
  tmp_str = tmp_str.replace( "<!--STICKY_USERNAME-->", 
                            '<input type="hidden" id="sticky_username" value="' +  cookie_hash["signup_username"]  + '" >' ) 

if "signup_email" in cookie_hash:
  tmp_str = tmp_str.replace( "<!--STICKY_EMAIL-->", 
                            '<input type="hidden" id="sticky_email" value="' +  cookie_hash["signup_email"]  + '" >' ) 

print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str



