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

def createProjectTable( olioList ):
  #tableProjectHTML = [ "<thead><tr><th>" + "</th><th>".join( [ "Project", "Sch", "Brd", "Access", "Dl" ] ) + "</th></tr></thead>" ]
  tableProjectHTML = [ "<thead><tr><th>" + "</th><th>".join( [ "Project", "&nbsp;", "&nbsp;", "Access", "&nbsp;" ] ) + "</th></tr></thead>" ]
  for projectDat in olioList:
    projectId = projectDat["id"]
    if projectDat["permission"] == "world-read":
      #perm = "<img src='img/heart.png' width='12px'></img> " + projectDat["permission"] 
      perm = "<i class='fa fa-heart'></i> " + projectDat["permission"] 
    else:
      #perm = "<img src='img/locked.png' width='12px'></img> " + projectDat["permission"] 
      perm = "<i class='fa fa-lock'></i> " + projectDat["permission"] 

    nam = projectDat["name"]
    #nam = re.sub( ' ', '', nam )

    x = [ #"<a href='project?projectId=" + str(projectDat["id"]) + "'>" + projectDat["name"] + "</a>", 
          "<a href='project?projectId=" + str(projectDat["id"]) + "'>" + nam + "</a>", 

          #"<a href='sch?project=" + projectDat["id"] + "' >Schematic</a>", 
          #"<a href='sch?project=" + projectDat["id"] + "' >Design</a>", 
          "<a href='sch?project=" + projectDat["id"] + "' ><i class='fa fa-toggle-right' ></i></a>", 

          #"<a href='brd?project=" + projectDat["id"] + "' >PCB</a>", 
          "<a href='sch?project=" + projectDat["id"] + "' ><i class='fa fa-arrow-circle-right' ></i></a>", 

          #perm, "<a href='#'><img src='img/download.png' width='18px'></img></a>" ]
          perm, "<a href='#'><i class='fa fa-cloud-download'></i></img></a>" ]
    trs = "<tr> <td style='word-break:break-all;' > "
    tre = "</td> </tr>"
    tableProjectHTML.append( trs  + "</td> <td style='word-break:break-word;' >".join(x) + tre )

  hs = "<table class='table table-striped table-bordered table-condensed' >"
  he = "</tbody></table>"

  return hs + "".join(tableProjectHTML) + he 

def createComponentAccordian( ):
  pass

def createModuleAccordian( ):
  pass

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

projectTable = createProjectTable( olioList )
tmp_str = tmp_str.replace( "<!--PROJECT_TABLE-->", projectTable )



tmp_str = tmp_str.replace( "<!--NAVBAR-->", nav )
tmp_str = tmp_str.replace( "<!--BREADCRUMB-->", breadcrumb( str(userName) ) )
tmp_str = tmp_str.replace( "<!--FOOTER-->", footer )
tmp_str = tmp_str.replace( "<!--ANALYTICS-->", analytics )


print "Content-Type: text/html;charset=utf-8"
print cookie.output()
print
print tmp_str


