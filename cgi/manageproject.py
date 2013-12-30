#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import datetime
import Cookie
import meowaux as mew
cgitb.enable()

cookie = Cookie.SimpleCookie()

cookie_hash = mew.getCookieHash( os.environ )

if ( ("userId" not in cookie_hash) or ("sessionId" not in cookie_hash)  or
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 0) ):
  print "Location:https://localhost/bleepsix/cgi/login"
  print
  sys.exit(0)

userId = cookie_hash["userId"]
userData = mew.getUser( userId )
userName = userData["userName"]

msg = ""
msgType = "none"

error = False
form = cgi.FieldStorage()
if "projectId" in form:
  projectId = form["projectId"].value
  projectData = mew.getProject( projectId )
  if ( "name" not in projectData) or (userId != projectData["userId"]):
    error = True
    msg = "Invalid project"
  else:
    projectName = projectData["name"]

    if "message" in cookie_hash:
      msg = str(cookie_hash["message"])
      msg = re.sub( '^\s*"', '', msg )
      msg = re.sub( '"\s*$', '', msg )

      if "messageType" in cookie_hash:
        msgType = cookie_hash["messageType"]
        msgType = re.sub( '^\s*"', '', msgType )
        msgType = re.sub( '"\s*$', '', msgType )


      expiration = datetime.datetime.now() + datetime.timedelta(days=-1)
      cookie["message"] = ""
      cookie["message"]["expires"] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S PST")
      cookie["messageType"] = ""
      cookie["messageType"]["expires"] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S PST")

else:
  error = True
  msg = "Project not provided"

template = mew.slurp_file("../template/manageproject.html")
tmp_str = template.replace("<!--USER-->", userName )
tmp_str = tmp_str.replace( "<!--USERINDICATOR-->", mew.userIndicatorString( userId, userName ) )

if not error:

  proj = mew.getProject( projectId )
  if proj["permission"] == 'world-read':
    tmp_str = tmp_str.replace("<!--PRIVATERADIO-->", \
        "<input id='private' type='radio' name='permissionOption' value='private' > </input>" )
    tmp_str = tmp_str.replace("<!--PUBLICRADIO-->",  \
        "<input id='public' type='radio' name='permissionOption' value='public' checked> </input>" )

  else:
    tmp_str = tmp_str.replace("<!--PRIVATERADIO-->", \
        "<input id='private' type='radio' name='permissionOption' value='private' checked> </input>" )
    tmp_str = tmp_str.replace("<!--PUBLICRADIO-->",  \
       "<input id='public' type='radio' name='permissionOption' value='public' > </input>" )
 
  tmp_str = tmp_str.replace("<!--PROJECTNAME-->", str(projectName) )
  tmp_str = tmp_str.replace("<!--PROJECTID-->", str(projectId) )
  tmp_str = tmp_str.replace("<!--HEADING-->",  mew.message( "&nbsp; &nbsp;" ) )

  if msgType == "error":
    tmp_str = tmp_str.replace("<!--MESSAGE-->", mew.errorMessage( msg ) )
  elif msgType == "success":
    tmp_str = tmp_str.replace("<!--MESSAGE-->", mew.successMessage( msg ) )
  else:
    tmp_str = tmp_str.replace("<!--MESSAGE-->", mew.message( msg ) )

else:
  tmp_str = tmp_str.replace("<!--MESSAGE-->", mew.errorMessage( msg ) )

tmp_str = tmp_str.replace( "<!--LEFT-->", mew.slurp_file("../template/left_template.html") )

print "Content-Type: text/html;charset=utf-8"
print cookie.output()
print
print tmp_str

