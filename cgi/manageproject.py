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
  print "Location:login"
  print
  sys.exit(0)

userId = cookie_hash["userId"]
userData = mew.getUser( userId )
userName = userData["userName"]

msg,msgType = "", "none"

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
    msg,msgType = mew.processCookieMessage( cookie, cookie_hash )

else:
  error = True
  msg = "Project not provided"

template = mew.slurp_file("template/manageproject.html")
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

  tmp_str = mew.replaceTemplateMessage( tmp_str, msg, msgType )

  ### project details
  if proj["permission"] == "world-read":
    perm = "<img src='img/heart.png' width='12px'></img> " + proj["permission"]
  else:
    perm = "<img src='img/locked.png' width='12px'></img> " + proj["permission"]


  x = [ proj["name"],
        "<a href='bleepsix_sch?sch=" + proj["sch"] + "' >Schematic</a>",
        "<a href='bleepsix_pcb?brd=" + proj["brd"] + "' >PCB</a>",
        perm ]

  trs = "<tr> <td> "
  tre = "</td> </tr>"

  projectDetails = ""
  projectDetails += "<table class='pure-table pure-table-horizontal' width='100%'>"
  projectDetails += "<thead><tr><th>Name</th> <th></th> <th></th> <th>Permission</th> </tr></thead> <tbody>"
  projectDetails += trs +  "</td> <td>".join(x) + tre
  projectDetails += "</tbody></table>"



  tmp_str = tmp_str.replace("<!--PROJECTDETAILS-->", projectDetails )




else:
  tmp_str = tmp_str.replace("<!--MESSAGE-->", mew.errorMessage( msg ) )

tmp_str = tmp_str.replace( "<!--LEFT-->", mew.slurp_file("template/left_template.html") )

print "Content-Type: text/html;charset=utf-8"
print cookie.output()
print
print tmp_str

