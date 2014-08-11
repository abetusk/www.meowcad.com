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

def breadcrumb( username ):
  prefix = """
  <div class='col-lg-12'>
    <ul class='breadcrumb' >
      <li> <a href='#'>
  """
  suffix = """
  </a>  </li>
    </ul>
  </div>
  """
  return prefix + username + suffix

signupnav="""
<form class="navbar-form navbar-right" role='form' action='/signup' method='POST'>
<div class='form-group'>
<button class='btn btn-warning' type='submit'>Sign up!</button>
</div>
</form>
"""


newproject_form = """
<form action='newproject.py'>
  <button id='buttonNewProject' 
    class='pure-button pure-button-tiel'>
    Create New Project
  </button>
</form>
"""

logout_nav = """
<ul class="nav navbar-nav navbar-right">
  <li><a href='/logout'>Logout</a></li>
</ul>
"""

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


#
#
#
#tableProjectHTML = [ "<thead><tr><th>Name</th> <th></th> <th></th> <th>Permission</th> <th></th> </tr></thead> <tbody>" ]
#for projectDat in olioList:
#  projectId = projectDat["id"]
#  if projectDat["permission"] == "world-read":
#    perm = "<img src='img/heart.png' width='12px'></img> " + projectDat["permission"] 
#  else:
#    perm = "<img src='img/locked.png' width='12px'></img> " + projectDat["permission"] 
#
#  x = [ "<a href='manageproject.py?projectId=" + str(projectDat["id"]) + "'>" + projectDat["name"] + "</a>", 
#        #"<a href='bleepsix_sch?project=" + projectDat["id"] + "' >Schematic</a>", 
#        #"<a href='bleepsix_pcb?project=" + projectDat["id"] + "' >PCB</a>", 
#        "<a href='sch?project=" + projectDat["id"] + "' >Schematic</a>", 
#        "<a href='brd?project=" + projectDat["id"] + "' >PCB</a>", 
#        perm ]
#        #projectDat["permission"] ]
#  trs = "<tr> <td> "
#
#  if userData["type"] == "anonymous":
#    tre = "</td> <td> </td> </tr>"
#  else:
#    tre = "</td> <td> <a href='manageproject.py?projectId=" + str(projectDat["id"])+ "'>Manage</a> </td> </tr>"
#  tableProjectHTML.append( trs  + "</td> <td>".join(x) + tre )
#
#hs = "<table class='pure-table pure-table-horizontal' width='100%'>"
#he = "</tbody></table>"
#


template = mew.slurp_file("template/portfolio.html")
nav = mew.slurp_file("template/navbar_template.html")



unamestr = "[" + str(userName) + "]"

if userData["type"] == "anonymous":
  unamestr = "&lt; " + str(userName) + " &gt;"
  nav = nav.replace( "<!--NAVBAR_USER_CONTEXT-->", signupnav )

else:
  nav = nav.replace( "<!--NAVBAR_USER_CONTEXT-->",
      "<ul class=\"nav navbar-nav navbar-right\"> <li><a href='/logout'>Logout</a></li> </ul>")

nav = nav.replace( "<!--NAVBAR_USER_DISPLAY-->",
    "<ul class=\"nav navbar-nav\"> <li><a href=\"/user/\">" + unamestr + "</a></li> </ul>")


footer = mew.slurp_file("template/footer_template.html")
analytics = mew.slurp_file("template/analytics_template.html")

#tmp_str = mew.replaceTemplateMessage( template, msg, "nominal" )

tmp_str = template

tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
tmp_str = tmp_str.replace( "<!--BREADCRUMB-->", breadcrumb( str(userName) ) )
tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )


print "Content-Type: text/html;charset=utf-8"
print cookie.output()
print
print tmp_str


