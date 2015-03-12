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

import json
cgitb.enable()

#### DEBUG
#print "Content-Type: text/html;charset=utf-8"
#print


def renderProjectTable( olioList, publicOnlyFlag = True ):
  if publicOnlyFlag:
    return mew.constructViewProjectListTable( olioList, showOwner=True )
  return mew.constructProjectListTable( olioList, showOwner=False )



authenticatedFlag = False
cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )
if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) != 0) ):
  authenticatedFlag = True

message,messageType = mew.processCookieMessage( cookie, cookie_hash )


viewUserId = None
if "userId" in cookie_hash:
  viewUserId = cookie_hash["userId"]
userId = None
if "userId" in cookie_hash:
  userId = cookie_hash["userId"]

form = cgi.FieldStorage()
if "userId" in form:
  viewUserId = str(form["userId"].value)


if viewUserId is None:
  print "Location:missing"
  print cookie.output()
  print
  sys.exit(0)

viewUserData = mew.getUser( viewUserId )

if viewUserId is None or "userName" not in viewUserData:
  print "Location:missing"
  print cookie.output()
  print
  sys.exit(0)


viewUserName = viewUserData["userName"]

#userId = cookie_hash["userId"]
sessionId = None
if "sessionId" in cookie_hash:
  sessionId = cookie_hash["sessionId"]

#olioList = mew.getPortfolios( cookie_hash["userId"] )

viewPrivate = False
if authenticatedFlag and viewUserId == userId:
  viewPrivate = True
olioList = mew.getPortfolios( viewUserId, viewPrivate )

userType = None
userName = None

if userId is not None:
  userData = mew.getUser( userId )
  userName = userData["userName"]
  if userData["type"] == "anonymous":
    userName = "anonymous"
  userType = userData["type"]

componentLibraryAccordian = mew.renderAccordian( "json/component_list_default.json", "componentaccordian", userId )
footprintLibraryAccordian = mew.renderAccordian( "json/footprint_list_default.json", "footprintaccordian", userId )

template = mew.slurp_file("template/portfolio.html")

createproj = mew.slurp_file("template/portfolio_create_form.html")
importform = mew.slurp_file("template/portfolio_import_form.html")

nav = mew.slurp_file("template/navbar_template.html")
#nav = mew.processLoggedInNavTemplate( nav, str(userName), str(userData["type"]) )

if userType is not None:
  nav = mew.processLoggedInNavTemplate( nav, str(userName), str(userType) )
else:
  nav = mew.loggedOutNavTemplate( nav )

footer = mew.slurp_file("template/footer_template.html")
analytics = mew.slurp_file("template/analytics_template.html")

tmp_str = template
tmp_str = mew.replaceTemplateMessage( tmp_str, message, messageType )

tmp_str = tmp_str.replace( "<!--ACCORDIAN_COMPONENTS-->", componentLibraryAccordian )
tmp_str = tmp_str.replace( "<!--ACCORDIAN_MODULES-->",    footprintLibraryAccordian )

publicOnlyFlag = True
if viewUserId == userId:
  publicOnlyFlag = False

projectTable = renderProjectTable( olioList, publicOnlyFlag )
tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
#tmp_str = tmp_str.replace( "<!--BREADCRUMB-->", mew.breadcrumb( str(userName) ) )
tmp_str = tmp_str.replace( "<!--BREADCRUMB-->", mew.breadcrumb( str(viewUserName), str(viewUserId) ) )

tmp_str = tmp_str.replace( "<!--PROJECT_TABLE-->", projectTable )

#if userData["type"] != "anonymous":
#if userType != "anonymous":
if userType is not None and userType == "user":
  tmp_str = tmp_str.replace( "<!--PROJECT_CREATE_FORM_HEADER-->", 
                             "<li><a href='#PanelProjectCreate' data-toggle='tab'>New</a></li>" )
  tmp_str = tmp_str.replace( "<!--PROJECT_CREATE_FORM-->", createproj )

  tmp_str = tmp_str.replace( "<!--PROJECT_IMPORT_FORM_HEADER-->",
                             "<li><a href='#PanelImport' data-toggle='tab'>Import</a></li>" )
  tmp_str = tmp_str.replace( "<!--PROJECT_IMPORT_FORM-->", importform )

tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )

print "Content-Type: text/html;charset=utf-8"
print cookie.output()
print
print tmp_str


