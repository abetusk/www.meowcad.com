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

## DEBUG
#print "Content-Type: text/html;charset=utf-8"
#print


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

cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )

form = cgi.FieldStorage()
project = {}
if "projectId" in form:
  project = mew.getProject( str(form["projectId"].value) )


if not project or ("id" not in project):
  cookie["message"] = "We're sorry, we couldn't find that project!"
  cookie["messageType"] = "error"
  print "Location:login"
  print cookie.output()
  print
  sys.exit(0)

projectId = project["id"]

userId = None
userName = None
sessionId = None

loggedInFlag = False
authorizedFlag = False

if ( ("userId" in cookie_hash) and ("sessionId" in cookie_hash)  and
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) != 0) ):
  loggedInFlag = True

if loggedInFlag:
  userId = cookie_hash["userId"]
  sessionId = cookie_hash["sessionId"]
  #olioList = mew.getPortfolios( cookie_hash["userId"] )
  userData = mew.getUser( userId )
  userName = userData["userName"]



if (not loggedInFlag) and (project["permission"] != "world-read"):
  cookie["message"] = "We're sorry, we couldn't find that project!"
  cookie["messageType"] = "error"
  print "Location:login"
  print cookie.output()
  print
  sys.exit(0)

if loggedInFlag and (project["userId"] == userId):
  authorizedFlag = True

if loggedInFlag and (project["permission"] != "world-read") and (project["userId"] != userId):
  cookie["message"] = "We're sorry, we couldn't find that project!"
  cookie["messageType"] = "error"
  print "Location:login"
  print cookie.output()
  print
  sys.exit(0)

#userName = userData["userName"]
projectUserId = mew.getProjectUserId( project["id"] )
projectUserName = mew.getProjectUserName( project["id"] )


message,messageType = mew.processCookieMessage( cookie, cookie_hash )

template = mew.slurp_file("template/project.html")
nav = mew.slurp_file("template/navbar_template.html")

if loggedInFlag:
  nav = mew.processLoggedInNavTemplate( nav, str(userName), str(userData["type"]) )
else:
  nav = mew.loggedOutNavTemplate( nav )


footer = mew.slurp_file("template/footer_template.html")
analytics = mew.slurp_file("template/analytics_template.html")
permission_pane = mew.slurp_file("template/project_manage_pane.html")

tmp_str = template

if authorizedFlag:
  tmp_str = tmp_str.replace( "<!--PERMISSION_PANE_HEADER-->", 
                            "<li><a href='#PanelManage' data-toggle='tab'>Manage</a></li>" )
  tmp_str = tmp_str.replace( "<!--PERMISSION_PANE-->", permission_pane )
  privateChecked = "checked"
  publicChecked = ""
  if project and ("permission" in project) and (project["permission"] == "world-read"):
    privateChecked = ""
    publicChecked = "checked"

  tmp_str = tmp_str.replace( "<!--PRIVATERADIO-->",
                             "<input id='private' type='radio' name='permissionOption' value='private' " +
                             privateChecked + "> </input>" )
  tmp_str = tmp_str.replace( "<!--PUBLICRADIO-->",
                             "<input id='public' type='radio' name='permissionOption' value='public' " +
                             publicChecked + " ></input>" )

  hidinp = "<input type='hidden' name='projectId' id='projectId' value='" + project["id"] + "'></input>";
  tmp_str = tmp_str.replace( "<!--PROJECTID_HIDDEN_INPUT-->", hidinp )

  hidnam = "<input type='hidden' name='projectName' id='projectName' value='" + project["name"] + "'></input>";
  tmp_str = tmp_str.replace( "<!--PROJECTNAME_HIDDEN_INPUT-->", hidnam )


tmp_str = tmp_str.replace( "<!--PROJECT_HEART_COUNT-->", str( mew.getHeartCount( project["id"] ) ) )
tmp_str = tmp_str.replace( "<!--PROJECT_COMMENT_COUNT-->", str( mew.getCommentCount( project["id"] ) ) )
tmp_str = tmp_str.replace( "<!--PROJECT_DOWNLOAD_COUNT-->", str( mew.getDownloadCount( project["id"] ) ) )

descr = cgi.escape( str( project["shortDescription"] ) )
tmp_str = tmp_str.replace( "<!--PROJECT_SHORT_DESCRIPTION-->", descr )

tmp_str = mew.replaceTemplateMessage( tmp_str, message, messageType )
tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
tmp_str = tmp_str.replace( "<!--BREADCRUMB-->", mew.breadcrumb( str(projectUserName), projectUserId, project["name"], project["id"]) )
tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )

componentLibraryAccordian = mew.renderAccordian( "json/component_list_default.json",
                                                 "componentaccordian",
                                                 userId,  project["id"] )
footprintLibraryAccordian = mew.renderAccordian( "json/footprint_list_default.json",
                                                 "footprintaccordian",
                                                 userId,  project["id"] )


tmp_str = tmp_str.replace( "<!--ACCORDIAN_COMPONENTS-->", componentLibraryAccordian )
tmp_str = tmp_str.replace( "<!--ACCORDIAN_MODULES-->",    footprintLibraryAccordian )


aa = "<img class='img-rounded' "
zz = "style='width:100%; border:1px solid gray; max-width: 350px; '></img>"

picdata = mew.getProjectPic( userId, project["id"] )
if picdata["type"] == "default":
  extra = ""
  if authorizedFlag:
    extra = "&userId=" + userId + "&projectId=" + projectId
    tmp_str = tmp_str.replace( "<!--JS_SCH-->", "gotosch();" )
    tmp_str = tmp_str.replace( "<!--JS_BRD-->", "gotobrd();" )
  else:
    tmp_str = tmp_str.replace( "<!--JS_SCH-->", "gotoviewsch();" )
    tmp_str = tmp_str.replace( "<!--JS_BRD-->", "gotoviewbrd();" )

  tmp_str = tmp_str.replace( "<!--SCHPIC-->", aa + "src='mewpng?f=img/" + picdata["schPicId"] + extra + "' " + zz )
  tmp_str = tmp_str.replace( "<!--BRDPIC-->", aa + "src='mewpng?f=img/" + picdata["brdPicId"] + extra + "' " + zz )

else:

  if authorizedFlag:
    tmp_str = tmp_str.replace( "<!--SCHPIC-->",
            aa +
            "src='mewpng?f=img/" + picdata["schPicId"] +
            "&userId=" + projectUserId +
            "&projectId=" + projectId +
            "' " + zz )

    tmp_str = tmp_str.replace( "<!--BRDPIC-->",
            "src='mewpng?f=img/" + picdata["brdPicId"] +
            "&userId=" + projectUserId +
            "&projectId=" + projectId +
            "' " + zz )

    tmp_str = tmp_str.replace( "<!--JS_SCH-->", "gotosch();" )
    tmp_str = tmp_str.replace( "<!--JS_BRD-->", "gotobrd();" )

  else:
    tmp_str = tmp_str.replace( "<!--SCHPIC-->",
            aa +
            "src='mewpng?f=img/" + picdata["schPicId"] +
            "&userId=" + projectUserId +
            "&projectId=" + projectId +
            "' " + zz )

    tmp_str = tmp_str.replace( "<!--BRDPIC-->",
            aa +
            "src='mewpng?f=img/" + picdata["brdPicId"] +
            "&userId=" + projectUserId +
            "&projectId=" + projectId +
            "' " + zz )

    tmp_str = tmp_str.replace( "<!--JS_SCH-->", "gotoviewsch();" )
    tmp_str = tmp_str.replace( "<!--JS_BRD-->", "gotoviewbrd();" )

print "Content-Type: text/html;charset=utf-8"
print cookie.output()
print
print tmp_str


