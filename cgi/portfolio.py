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



def renderProjectTable( olioList ):
  tableProjectHTML = [ "<thead><tr><th>" + "</th><th style='text-align:center;' >".join( [ "Project",
                                        "&nbsp;", "&nbsp;", "Access", "&nbsp;" ] ) + "</th></tr></thead>" ]
  for projectDat in olioList:
    projectId = projectDat["id"]
    if projectDat["permission"] == "world-read":
      perm = "<i class='fa fa-heart'></i> " + projectDat["permission"] 
    else:
      perm = "<i class='fa fa-lock'></i> " + "private"

    nam = projectDat["name"]

    bbs = "<button type='button' class='btn btn-default btn-xs'>"
    bbe = "</button>"

    x = [ "<a href='project?projectId=" + str(projectDat["id"]) + "'>" + nam + "</a>",
          "<a href='sch?project=" + projectDat["id"] + "' >" +
              bbs + "<img src='/img/alignment-unalign.svg' width='20px' /><br/>sch" + bbe + "</a>",
          "<a href='brd?project=" + projectDat["id"] + "' >" +
              bbs + "<img src='/img/circuit-board.svg' width='20px' /><br/>brd" + bbe + "</a>",
          perm, "<a href='#'><i class='fa fa-cloud-download fa-lg'></i></img></a>" ]

    trs = "<tr> <td style='word-break:break-all;' > "
    tre = "</td> </tr>"
    tableProjectHTML.append( trs  + "</td> <td style='word-break:break-word; text-align:center; ' >".join(x) + tre )

  hs = "<table class='table table-striped table-bordered table-condensed' >"
  he = "</tbody></table>"

  return hs + "".join( tableProjectHTML ) + he

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

componentLibraryAccordian = mew.renderAccordian( "json/component_list_default.json", "componentaccordian", userId )
footprintLibraryAccordian = mew.renderAccordian( "json/footprint_list_default.json", "footprintaccordian", userId )

template = mew.slurp_file("template/portfolio.html")

createproj = mew.slurp_file("template/portfolio_create_form.html")

nav = mew.slurp_file("template/navbar_template.html")
nav = mew.processLoggedInNavTemplate( nav, str(userName), str(userData["type"]) )

footer = mew.slurp_file("template/footer_template.html")
analytics = mew.slurp_file("template/analytics_template.html")

tmp_str = template
tmp_str = mew.replaceTemplateMessage( tmp_str, message, messageType )

tmp_str = tmp_str.replace( "<!--ACCORDIAN_COMPONENTS-->", componentLibraryAccordian )
tmp_str = tmp_str.replace( "<!--ACCORDIAN_MODULES-->",    footprintLibraryAccordian )

projectTable = renderProjectTable( olioList )
tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
tmp_str = tmp_str.replace( "<!--BREADCRUMB-->", mew.breadcrumb( str(userName) ) )

tmp_str = tmp_str.replace( "<!--PROJECT_TABLE-->", projectTable )
tmp_str = tmp_str.replace( "<!--PROJECT_CREATE_FORM-->", createproj )

tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )

print "Content-Type: text/html;charset=utf-8"
print cookie.output()
print
print tmp_str


