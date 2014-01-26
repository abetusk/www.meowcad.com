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

olioList = mew.getAllProjects()

tableProjectHTML = [ "<thead><tr><th>Name</th> <th></th> <th></th> <th>Permission</th> <th>User</th> </tr></thead> <tbody>" ]
for projectDat in olioList:
  projectId = projectDat["id"]

  #projectDat = olioList[projectId]

  if projectDat["permission"] == "world-read":
    perm = "<img src='/img/heart.png' width='12px'></img> " + projectDat["permission"] 
  else:
    perm = "<img src='/img/locked.png' width='12px'></img> " + projectDat["permission"] 


  x = [  str(projectDat["name"]) ,
        "<a href='bleepsix_sch?sch=" + projectDat["sch"] + "' >Schematic</a>", 
        "<a href='bleepsix_pcb?brd=" + projectDat["brd"] + "' >PCB</a>", 
        perm,
        str(projectDat["userName"])
        ]
        #projectDat["permission"] ]
  trs = "<tr> <td> "
  tre = "</td> </tr>"
  tableProjectHTML.append( trs  + "</td> <td>".join(x) + tre )

hs = "<table class='pure-table pure-table-horizontal' width='100%'>"
he = "</tbody></table>"

userData = mew.getUser( userId )
userName = userData["userName"]

template = mew.slurp_file("template/browse.html")
tmp_str = template.replace("<!--USER-->", userName )
tmp_str = tmp_str.replace( "<!--PROJECTS-->", hs + "\n".join(tableProjectHTML) + he )
tmp_str = tmp_str.replace( "<!--LEFT-->", mew.slurp_file("template/left_template.html") )
tmp_str = tmp_str.replace( "<!--USERINDICATOR-->", mew.userIndicatorString( userId, userName ) )
tmp_str = tmp_str.replace( "<!--HEADING-->", mew.message("&nbsp; &nbsp;") )
tmp_str = mew.replaceTemplateMessage( tmp_str, message, messageType )

print "Content-Type: text/html;charset=utf-8"
print cookie.output()
print

print tmp_str


