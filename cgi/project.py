#!/usr/bin/python
#
import re,cgi,cgitb,sys
import os
import urllib
import redis
import hashlib
import datetime
import Cookie
import meowaux as mew
cgitb.enable()

# Create DOM element helper functions
#

def renderProjectReadme():
  pass

def renderProjectBOM():
  pass

def renderProjectFiles():
  pass

def renderComponentAccordian( ):
  pass

def renderModuleAccordian( ):
  pass

#
##

form = cgi.FieldStorage()
project = {}
if "projectId" in form:
  project = mew.getProject( str(form["projectId"].value) )

  mew.log( str(project) )
else:
  cookie["message"] = "We're sorry, we couldn't find that project!"
  cookie["messageType"] = "error"
  print "Location:login"
  print cookie.output()
  print
  sys.exit(0)


cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )
if ( ("userId" not in cookie_hash) or ("sessionId" not in cookie_hash)  or
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 0) ):
  print "Location:login"
  print
  sys.exit(0)

message,messageType = mew.processCookieMessage( cookie, cookie_hash )

userId = cookie_hash["userId"]
sessionId = cookie_hash["sessionId"]
olioList = mew.getPortfolios( cookie_hash["userId"] )
userData = mew.getUser( userId )
userName = userData["userName"]

template = mew.slurp_file("template/project.html")
nav = mew.slurp_file("template/navbar_template.html")
nav = mew.processLoggedInNavTemplate( nav, str(userName), str(userData["type"]) )

footer = mew.slurp_file("template/footer_template.html")
analytics = mew.slurp_file("template/analytics_template.html")

tmp_str = template

tmp_str = tmp_str.replace( "<!--PROJECT_HEART_COUNT-->", str( mew.getHeartCount( project["id"] ) ) )
tmp_str = tmp_str.replace( "<!--PROJECT_COMMENT_COUNT-->", str( mew.getCommentCount( project["id"] ) ) )
tmp_str = tmp_str.replace( "<!--PROJECT_DOWNLOAD_COUNT-->", str( mew.getDownloadCount( project["id"] ) ) )

hidinp = "<input type='hidden' name='projectId' id='projectId' value='" + project["id"] + "'></input>";
tmp_str = tmp_str.replace( "<!--PROJECTID_HIDDEN_INPUT-->", hidinp )

hidnam = "<input type='hidden' name='projectName' id='projectName' value='" + project["name"] + "'></input>";
tmp_str = tmp_str.replace( "<!--PROJECTNAME_HIDDEN_INPUT-->", hidnam )

tmp_str = mew.replaceTemplateMessage( tmp_str, message, messageType )
tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
tmp_str = tmp_str.replace( "<!--BREADCRUMB-->", mew.breadcrumb( str(userName), project["name"], project["id"]) )
tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )

print "Content-Type: text/html;charset=utf-8"
print cookie.output()
print
print tmp_str


