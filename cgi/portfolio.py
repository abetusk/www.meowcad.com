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
  tableProjectHTML = [ "<thead><tr><th>" + "</th><th style='text-align:center;' >".join( [ "Project",
                                        "&nbsp;", "&nbsp;", "Access", "&nbsp;" ] ) + "</th></tr></thead>" ]
  for projectDat in olioList:
    projectId = projectDat["id"]
    if projectDat["permission"] == "world-read":
      perm = "<i class='fa fa-heart'></i> " + projectDat["permission"] 
    else:
      perm = "<i class='fa fa-lock'></i> " + "private"

      if publicOnlyFlag:
        continue

    nam = projectDat["name"]

    bbs = "<button type='button' class='btn btn-default btn-xs'>"
    bbe = "</button>"

    action = "onclick='downloadProject(\"" + projectDat["id"] + "\");'"

    x = [ "<a href='project?projectId=" + str(projectDat["id"]) + "'>" + nam + "</a>",
          "<a href='sch?project=" + projectDat["id"] + "' >" +
              bbs + "<img src='/img/alignment-unalign.svg' width='20px' /><br/>sch" + bbe + "</a>",
          "<a href='brd?project=" + projectDat["id"] + "' >" +
              bbs + "<img src='/img/circuit-board.svg' width='20px' /><br/>brd" + bbe + "</a>",
          perm, "<a href='#' " + action + " ><i class='fa fa-cloud-download fa-lg'></i></img></a>" ]

    trs = "<tr> <td style='word-break:break-all;' > "
    tre = "</td> </tr>"
    tableProjectHTML.append( trs  + "</td> <td style='word-break:break-word; text-align:center; ' >".join(x) + tre )

  hs = "<table class='table table-striped table-bordered table-condensed' >"
  he = "</tbody></table>"

  return hs + "".join( tableProjectHTML ) + he

authenticatedFlag = False

cookie = Cookie.SimpleCookie()
cookie_hash = mew.getCookieHash( os.environ )
if ( ("userId" not in cookie_hash) or ("sessionId" not in cookie_hash)  or
     (mew.authenticateSession( cookie_hash["userId"], cookie_hash["sessionId"] ) == 0) ):
  authenticatedFlag = True
  #print "Location:login"
  #print
  #sys.exit(0)

message,messageType = mew.processCookieMessage( cookie, cookie_hash )


viewUserId = cookie_hash["userId"]
userId = cookie_hash["userId"]

form = cgi.FieldStorage()
if "userId" in form:
  viewUserId = str(form["userId"].value)


#userId = cookie_hash["userId"]
sessionId = cookie_hash["sessionId"]
#olioList = mew.getPortfolios( cookie_hash["userId"] )
olioList = mew.getPortfolios( viewUserId )
userData = mew.getUser( userId )
userName = userData["userName"]
if userData["type"] == "anonymous":
  userName = "anonymous"

componentLibraryAccordian = mew.renderAccordian( "json/component_list_default.json", "componentaccordian", userId )
footprintLibraryAccordian = mew.renderAccordian( "json/footprint_list_default.json", "footprintaccordian", userId )

template = mew.slurp_file("template/portfolio.html")

createproj = mew.slurp_file("template/portfolio_create_form.html")
importform = mew.slurp_file("template/portfolio_import_form.html")

nav = mew.slurp_file("template/navbar_template.html")
nav = mew.processLoggedInNavTemplate( nav, str(userName), str(userData["type"]) )

footer = mew.slurp_file("template/footer_template.html")
analytics = mew.slurp_file("template/analytics_template.html")

tmp_str = template
tmp_str = mew.replaceTemplateMessage( tmp_str, message, messageType )

tmp_str = tmp_str.replace( "<!--ACCORDIAN_COMPONENTS-->", componentLibraryAccordian )
tmp_str = tmp_str.replace( "<!--ACCORDIAN_MODULES-->",    footprintLibraryAccordian )

publicOnlyFlag = True
if viewUserId == userId:
  publicOnlyFlag = False

projectTable = renderProjectTable( olioList, publicOnlyFlag  )
tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
tmp_str = tmp_str.replace( "<!--BREADCRUMB-->", mew.breadcrumb( str(userName) ) )

tmp_str = tmp_str.replace( "<!--PROJECT_TABLE-->", projectTable )

if userData["type"] != "anonymous":
  tmp_str = tmp_str.replace( "<!--PROJECT_CREATE_FORM_HEADER-->", 
                             "<li><a href='#PanelProjectCreate' data-toggle='tab'>New</a></li>" )
  tmp_str = tmp_str.replace( "<!--PROJECT_CREATE_FORM-->", createproj )

tmp_str = tmp_str.replace( "<!--PROJECT_IMPORT_FORM-->", importform )

tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )

print "Content-Type: text/html;charset=utf-8"
print cookie.output()
print
print tmp_str


