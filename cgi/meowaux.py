#!/usr/bin/python

import re
import sys
import os
import redis
import hashlib
import time
import datetime
import uuid
import json
import random
import cgi

## -- file system and header (cookie) processing functions

#def breadcrumb( username, project=None ):
#  prefix = """
#  <div class='col-lg-12'>
#    <ul class='breadcrumb' >
#  """
#
#  s = "<li> <a href='/portfolio'>" + str(username) + "</a></li>\n"
#
#  if project is not None:
#    s += "<li> <a href='/portfolio/" + str(project) + "'>" + str(project) + "</a></li>\n"
#
#  suffix = "</div>"
#
#  return prefix + s + suffix

def log( s ):
  f = open( "/tmp/meowaux.log", "a" )
  f.write( str(s) + "\n" )
  f.close()

def safe_str( s ):
  return re.sub( '[^a-zA-Z-_%]', '', s )

def slurp_file(fn):
  f = open(fn, "r")
  s = f.read()
  f.close()
  return s


DEFAULT_DATA_LOCATION = "/var/www"
DEFAULT_COMP_LOCATION = "/var/www"
DEFAULT_MOD_LOCATION  = "/var/www"
USR_BASE_LOCATION = "/home/meow/usr"



# http://stackoverflow.com/questions/3812849/how-to-check-whether-a-directory-is-a-sub-directory-of-another-directory
#
def in_directory(fn, directory):
  #make both absolute    
  directory = os.path.join(os.path.realpath(directory), '')
  fn = os.path.realpath(fn)

  #return true, if the common prefix of both is equal to directory
  #e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
  return os.path.commonprefix([fn , directory]) == directory


def json_slurp_file(fn):
  data = "{ \"type\" : \"error\", \"reason\" : \"error\" }"
  try:
    with open(fn) as fp:
      data = fp.read()
  except Exception as ee:
    data = "{ \"type\" : \"error\", \"reason\" : \"" + str(ee) + "\" }"
  return data


# return file if found, checking in the following order:
#  - USR_BASE_LOCATION / <userId> / <projectId> / fn
#  - USR_BASE_LOCATION / <userId> / fn
#  - DEFAULT_DATA_LOCATION / FN
#
# return None if none found.
#
def file_cascade( userId, projectId, fn ):

  if (userId is not None) and (projectId is not None):
    usrDir = os.path.join( USR_BASE_LOCATION, str(userId) )
    projDir = os.path.join( usrDir , str(projectId) )

    if in_directory( usrDir, USR_BASE_LOCATION ):
      if in_directory( projDir, usrDir ):
        fullfn = os.path.join( projDir, fn )
        if in_directory( fullfn, projDir ) and os.path.isfile( fullfn ):
          return json_slurp_file( fullfn )

      fullfn = os.path.join( usrDir, fn )
      if in_directory( fullfn, usrDir ) and os.path.isfile( fullfn ):
        return json_slurp_file( fullfn )

  if (userId is not None) :
    usrDir = os.path.join( USR_BASE_LOCATION, str(userId) )
    if in_directory( usrDir, USR_BASE_LOCATION ):

      fullfn = os.path.join( usrDir, fn )
      if in_directory( fullfn, usrDir ) and os.path.isfile( fullfn ):
        return json_slurp_file( fullfn )

  fullfn = os.path.join( DEFAULT_DATA_LOCATION, fn )
  if in_directory( fullfn, DEFAULT_DATA_LOCATION ) and os.path.isfile( fullfn ):
    return json_slurp_file( fullfn )

  return "{ \"type\" : \"error\", \"reason\" : \"error\" }"

####
#
def file_cascade_fn( userId, projectId, fn ):

  data = { "type" : "success" }

  if (userId is not None) and (projectId is not None):

    usrDir = os.path.join( USR_BASE_LOCATION, str(userId) )
    projDir = os.path.join( usrDir , str(projectId) )
    if in_directory( usrDir, USR_BASE_LOCATION ):

      if in_directory( projDir, usrDir ):
        fullfn = os.path.join( projDir, fn )
        if in_directory( fullfn, projDir ) and os.path.isfile( fullfn ):
          data["filename"] = fullfn
          return json.dumps( data )

      fullfn = os.path.join( usrDir, fn )
      if in_directory( fullfn, usrDir ) and os.path.isfile( fullfn ):
        data["filename"] = fullfn
        return json.dumps( data )

  if (userId is not None) :

    usrDir = os.path.join( USR_BASE_LOCATION, str(userId) )
    if in_directory( usrDir, USR_BASE_LOCATION ):

      fullfn = os.path.join( usrDir, fn )
      if in_directory( fullfn, usrDir ) and os.path.isfile( fullfn ):
        data["filename"] = fullfn
        return json.dumps( data )

  fullfn = os.path.join( DEFAULT_DATA_LOCATION, fn )
  if in_directory( fullfn, DEFAULT_DATA_LOCATION ) and os.path.isfile( fullfn ):
    data["filename"] = fullfn
    return json.dumps( data )

  return "{ \"type\" : \"error\", \"reason\" : \"error\" }"



def getProjectPic( userId, projectId ):
  db = redis.Redis()

  rprojpic = {}
  rprojpic["schPicId"] = "sch-proj-default.png"
  rprojpic["brdPicId"] = "brd-proj-default.png"
  rprojpic["type"] = "error"

  #proj = db.hgetall( "project:" + str(projectId) )
  proj = getProject( str(projectId) )
  if not proj:
    return rprojpic

  qprojpic = db.hgetall( "projectpic:" + str(projectId) )
  if qprojpic:

    if proj["userId"] == userId:
      rprojpic["schPicId"] = qprojpic["schPicId"]
      rprojpic["brdPicId"] = qprojpic["brdPicId"]
      rprojpic["type"] = "default"
      return rprojpic

    if proj["permission"] == "world-read":

      schpic = db.hgetall( "pic:" + qprojpic["schPicId"] )
      if schpic["permission"] != "world-read":
        rprojpic["schPicId"] = "sch-proj-default.png"
        rprojpic["brdPicId"] = "brd-proj-default.png"
        rprojpic["type"] = "default"
        return rprojpic

      brdpic = db.hgetall( "pic:" + qprojpic["brdPicId"] )
      if brdpic["permission"] != "world-read":
        rprojpic["schPicId"] = "sch-proj-default.png"
        rprojpic["brdPicId"] = "brd-proj-default.png"
        rprojpic["type"] = "default"
        return rprojpic

      rprojpic["schPicId"] = qprojpic["schPicId"]
      rprojpic["brdPicId"] = qprojpic["brdPicId"]
      rprojpic["type"] = "project"
      return rprojpic

  rprojpic["type"] = "default"
  return rprojpic

def getCookieHash( environ ):
  cookie_hash = {}
  if 'HTTP_COOKIE' in environ:
    cookies_str = os.environ['HTTP_COOKIE']
    cookies = cookies_str.split('; ')

    for cookie in cookies:
      c = cookie.split('=')
      cookie_hash[ c[0] ] = c[1]

  return cookie_hash

# return the message, setting it expired if it's processed
#
def processCookieMessage( cookie, cookieHash ):

  msg,msgType = "", ""
  if "message" in cookieHash:
    msg = str(cookieHash["message"]).decode('string_escape')
    msg = re.sub( '^\s*"', '', msg )
    msg = re.sub( '"\s*$', '', msg )

    if "messageType" in cookieHash:
      msgType = cookieHash["messageType"].decode('string_escape')
      msgType = re.sub( '^\s*"', '', msgType )
      msgType = re.sub( '"\s*$', '', msgType )

    expiration = datetime.datetime.now() + datetime.timedelta(days=-1)
    cookie["message"] = ""
    cookie["message"]["expires"] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S PST")
    cookie["messageType"] = ""
    cookie["messageType"]["expires"] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S PST")

  return msg,msgType

def expireCookie( cookie, val ):
  expiration = datetime.datetime.now() + datetime.timedelta(days=-1)
  cookie[val] = ""
  cookie[val]["expires"] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S PST")

def breadcrumb( username=None, userId=None, projectName=None, projectId=None ):
  prefix = """
  <div class='row'>
    <div class='col-lg-12'>
      <ul class='breadcrumb' >
      <li>
  """
        #<li> <a href='/portfolio'>
  suffix = """
    </a>  </li>
      </ul>
    </div>
  </div>
  """

  s = ""

  if (username is not None) and (userId is not None):
    #s += username
    s += "<a href='/portfolio?userId=" + str(userId) + "'>" + username
    if (projectName is not None) and (projectId is not None):
      s += "</a></li> <li><a href='/project?projectId=" + str(projectId) + "'>" + str(projectName)

  return prefix + s + suffix


def loggedOutNavTemplate( nav_template ):
  xx = """
  <ul class='nav navbar-nav' style='float:right; margin-top:7px; margin-right:5px; ' >
    <li>

      <form action='/login' style='display:inline;' >
        <button class='btn btn-success' type='submit'>Log in</button>
      </form>

      <form action='/signup' style='display:inline;' >
        <button class='btn btn-warning' type='submit'>Sign up!</button>
      </form>

    </li>
  </ul>
  """
  return nav_template.replace( "<!--NAVBAR_USER_CONTEXT-->", xx )


def processLoggedInNavTemplate( nav_template, userName, userType ):

#  signupnav="""
#  <form class="navbar-form navbar-right" role='form' action='/register' method='POST'>
#  <div class='form-group'>
#  <button class='btn btn-warning' type='submit'>Register!</button>
#  </div>
#  </form>
#  """

  signupnav="""
  <div class='navbar-right' style='margin-top:7px;' >
  <button class='btn btn-warning' onclick='window.location.href = "/register";'>Register!</button>
  </div>
  """

  unamestr = "[" + str(userName) + "]"

  if userType == "anonymous":
    unamestr = "&lt; " + str(userName) + " &gt;"
    nav_template = nav_template.replace( "<!--NAVBAR_USER_CONTEXT-->", signupnav )
  else:
    logout = ""
    logout += "<ul class=\"nav navbar-nav navbar-right\">"
    logout += "  <li>"
    logout += "    <a href='/logout'><i class='fa fa-sign-out'></i> Logout</a>"
    logout += "  </li>"
    logout += "</ul>"
    nav_template = nav_template.replace( "<!--NAVBAR_USER_CONTEXT-->", logout )
        #"<ul class=\"nav navbar-nav navbar-right\"> <li><a href='/logout'>Logout</a></li> </ul>")

  if userType == "anonymous":
    nav_template = nav_template.replace( "<!--NAVBAR_USER_DISPLAY-->",
        "<ul class=\"nav navbar-nav\"> <li><a href=\"/register\">" + unamestr + "</a></li> </ul>")
  else:
    s = ""
    s += "<ul class=\"nav navbar-nav\">"
    s += "  <li>"
    s += "    <a href=\"/user\">" 
    s += "      <i class='fa fa-cog'></i>"
    s += "    </a>"
    s += "  </li>"
    s += "  <li>"
    #s += "    &nbsp;"
    s += "    <a href=\"/portfolio\">" 
    s +=      unamestr 
    s += "    </a>"
    s += "  </li>"
    s += "</ul>"
    nav_template = nav_template.replace( "<!--NAVBAR_USER_DISPLAY-->", s )

  return nav_template

def replaceTemplateMessage( template, msg, msgType ):

  if len(msg) == 0:
    return template.replace("<!--MESSAGE-->", message( "" ) )

  if msgType == "error":
    return template.replace("<!--MESSAGE-->", errorMessage( msg ) )

  elif msgType == "success":
    return template.replace("<!--MESSAGE-->", successMessage( msg ) )

  elif msgType == "status":
    return template.replace("<!--MESSAGE-->", statusMessage( msg ) )

  elif msgType == "nominal":
    return template.replace("<!--MESSAGE-->", nominalMessage( msg ) )

  else:
    return template.replace("<!--MESSAGE-->", message( msg ) )




## -- json dictionary

def randomName( fn, n ):

  json_data = open(fn)
  data = json.load(json_data)
  json_data.close()

  s = ""
  for i in range(n):
    if i>0:
      s += " "
    k = random.randrange( len(data["word"]) )
    s += data["word"][k]

  return s


## --- html helper functions

#def userIndicatorString( userId, userName ):
#  userData = getUser( userId )
#
#  userIndicator = ""
#  if str(userData["type"]) == "anonymous":
#    userIndicator += "<b> &lt; " + str(userName) + "&gt;  </b> "
#  else:
#    userIndicator = "<b><a href='usersettings' >" # ?userId=" + str(userId) + "'> "
#    userIndicator += "[" + str(userName) + "] </a> </b> "
#  userIndicator += " &nbsp; &nbsp; <a href='logout'>Logout</a> "
#  return userIndicator


def errorMessage( msg ):
  return "<div style='text-align:center;' id='message' class='alert alert-danger' >" + str(msg) + "</div>"
  #return "<div id='message' class='error-message' >" + str(msg) + "</div>"

def successMessage( msg ):
  return "<div style='text-align:center;' id='message' class='alert alert-success' >" + str(msg) + "</div>"
  #return "<div id='message' class='success-message'>" + str(msg) + "</div>"

def warningMessage( msg ):
  return "<div style='text-align:center;' id='message' class='alert alert-warning' >" + str(msg) + "</div>"
  #return "<div id='message' class='warning-message'>" + str(msg) + "</div>"

def statusMessage( msg ):
  return "<div style='text-align:center;' id='message' class='alert alert-info' >" + str(msg) + "</div>"
  #return "<div id='message' class='status-message'>" + str(msg) + "</div>"

def nominalMessage( msg ):
  return "<div style='text-align:center;' id='message' class='alert alert-primary' >" + str(msg) + "</div>"
  #return "<div id='message' class='nominal-message'>" + str(msg) + "</div>"

# landing place so wanrings don't move all content below it
#
def message( msg ):
  return "<div style='text-align:center;' id='message' class='no-message'>" + str(msg) + "</div>"

## --- authentication and session functions 

def authenticateSession( userId, sessionId ):
  db = redis.Redis()

  hashSessionId = hashlib.sha512( str(userId) + str(sessionId) ).hexdigest()

  x = db.sismember( "sesspool", hashSessionId )

  if not db.sismember( "sesspool", hashSessionId ):
    return False

  sessionDat = db.hgetall( "session:" + str(hashSessionId) )
  userDat = db.hgetall( "user:" + str(userId) )

  if ( ("userName" not in userDat) or
       ("userId" not in sessionDat) or
      (sessionDat["userId"] != userId) or
      (sessionDat["active"] != "1") ):
    return False;

  return True


def getHeartCount( projectId ):
  return 0

def getCommentCount( projectId ):
  return 0

def getDownloadCount( projectId ):
  return 0

def getSessions():
  db = redis.Redis()
  return db.smembers( "sesspool" )

def deactivateSession( userId, sessionId ):
  db = redis.Redis()

  hashSessionId = hashlib.sha512( str(userId) + str(sessionId) ).hexdigest()
  db.srem( "sesspool", str(hashSessionId) )
  x = db.hgetall( "session:" + str(hashSessionId) )
  db.hset( "session:" + str(hashSessionId), "active", 0 )
  return 1

def createSession( userId ):

  db = redis.Redis()

  sessionId = uuid.uuid4()

  hashSessionId = hashlib.sha512( str(userId) + str(sessionId) ).hexdigest()
  db.sadd( "sesspool", str(hashSessionId) )

  sess = {}
  sess["id"] = str(hashSessionId)
  sess["userId"] = str(userId)
  sess["active"] = 1
  db.hmset( "session:" + str(hashSessionId), sess )
  return str(sessionId)


def addemail( userId, email ):
  db = redis.Redis()

  useremailid = str(uuid.uuid4())

  obj = {}
  ts = time.time()
  obj["id"] = str(useremailid)
  obj["userId"] = str(userId)
  obj["email"] = str(email)
  obj["stime"] = ts
  obj["timestamp"] = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
  db.hmset( "useremail:" + str(useremailid), obj )

  db.sadd( "useremail:" + str(userId), str(useremailid) )


def feedback( userId, email, feedback ):
  db = redis.Redis()

  #user = getUser( userId )
  #if ("id" not in user) or (user["active"] != "1"):
  #  return False

  feedbackId = str(uuid.uuid4())

  ts = time.time()
  obj = {}
  obj["id"] = feedbackId
  obj["text"] = str(feedback)
  obj["userId"] = str(userId)
  obj["email"] = str(email)
  obj["stime"] = ts
  obj["timestamp"] = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
  db.hmset( "feedback:" + feedbackId, obj )

  db.sadd( "feedbackpool", feedbackId )

  return True

## --- user functions

def userPasswordTest( userId, testpass ):
  db = redis.Redis()
  testhashPassword = hashlib.sha512( str(userId) + str(testpass) ).hexdigest()
  obj = db.hgetall( "user:" + str(userId) )
  if not obj:
    return False
  if obj["passwordHash"] == testhashPassword:
    return True
  return False

def getProjectUserName( projectId ):
  db = redis.Redis()

  #p = db.hgetall( "project:" + str(projectId) )
  p = getProject( str(projectId) )
  if not p:
    return None
  uid = p["userId"]

  u = db.hgetall( "user:" + str(uid) )
  if not u:
    return None
  return u["userName"]

def getProjectUserId( projectId ):
  db = redis.Redis()

  #p = db.hgetall( "project:" + str(projectId) )
  p = getProject( str(projectId) )
  if not p:
    return None
  uid = p["userId"]
  return uid


def getProjectPermission( projectId ):
  db = redis.Redis()

  p = getProject( str(projectId) )
  if not p:
    return None
  return p["permission"]

def getUser( userId ):
  db = redis.Redis()
  return db.hgetall( "user:" + str(userId) )

def setUserPassword( userId, password ):
  db = redis.Redis()
  hashPassword = hashlib.sha512( str(userId) + str(password) ).hexdigest()
  return db.hset( "user:" + str(userId), "passwordHash", hashPassword )

def passwordTest( password ):
  if len(password) < 8:
    return False
  if len(password) > 20:
    return True
  if not re.search( '[0-9]', password):
    return False
  if not re.search( '[A-Z]', password):
    return False
  if not re.search( '[a-z]', password):
    return False
  return True

def transferUser( userid, username, password ):

  db = redis.Redis()

  u = db.hgetall( "user:" + str(userid) )
  if not u:
    return {}

  if u["type"] != "anonymous":
    t = db.hgetall( "username:" + str(u["userName"]) )
    if t:
      return {}

  usernameHash = {}
  usernameHash["id"] = str(userid)
  usernameHash["userName"] = str(username)

  hashpassword = hashlib.sha512( str(userid) + str(password) ).hexdigest()

  db.hset( "user:" + str(userid), "userName", str(username) )
  db.hset( "user:" + str(userid), "passwordHash", str(hashpassword) )
  db.hset( "user:" + str(userid), "type", "user" )

  db.hmset( "username:" + str(username), usernameHash )

  return db.hgetall( "user:" + str(userid) )


def createUser( userName, password ):
  db = redis.Redis()

  userId = str( uuid.uuid4() )
  hashPassword = hashlib.sha512( str(userId) + str(password) ).hexdigest()

  usernameObj = {}
  usernameObj["id"] = userId
  usernameObj["username"] = str(userName)
  r = db.hmset( "username:" + str(userName), usernameObj );

  ts = time.time()
  user = {}
  user["id"] = userId
  user["passwordHash"] = str(hashPassword)
  user["active"] = 1
  user["userName"] = str(userName)
  user["type"] = "user"
  user["stime"] = ts
  user["timestamp"] = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
  r = db.hmset( "user:" + userId, user );

  db.sadd( "userpool", userId )

  return user

def getUserName( userName ):
  db = redis.Redis()
  return db.hgetall( "username:" + str(userName) )

def userExists( userId ):
  db = redis.Redis()

  r = db.hgetall( "user:" + str(userId) )
  if r is None:
    return False

  if ("active" in r) and (r["active"] == "1"):
    return True

  return False

def deactivateUser( userId ):
  db = redis.Redis()
  return db.hset( "user:" + str(userId) , "active","0" )

  

## --- project functions

# add to olio
# create project
# create projectop
# add to projectevent
# create projectsnapshot
# update projectrecent
#
# add to projectpool
#
def createProject( userId, projectName, permission ):
  db = redis.Redis()

  projId = str(uuid.uuid4())

  userData = db.hgetall( "user:" + str(userId) )
  if ( (not userData) or  (userData["type"] == "anonymous") ):
    return None

  db.rpush( "olio:" + str(userId), projId )

  ts = time.time()
  proj = {}
  proj["id"] = projId
  proj["userId"] = str(userId)
  proj["name"] = str(projectName)
  proj["active"] = "1"
  proj["stime"] = ts
  proj["timestamp"] = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

  if str(permission) == "world-read":
    proj["permission"] = "world-read"
  else:
    proj["permission"] = "user"
  if not db.hmset( "project:" + proj["id"], proj ):
    return None

  defNetClass = {}
  defNetClass["name"] = "Default"
  defNetClass["description"] = "This is the default net class."
  defNetClass["unit"] = "deci-thou"
  defNetClass["track_width"] = 100
  defNetClass["clearance"] =  100
  defNetClass["via_diameter"] =  472
  defNetClass["via_drill_diameter"] =  250
  defNetClass["uvia_diameter"] =  200
  defNetClass["uvia_drill_diameter"] =  50
  defNetClass["net"] =  [ ]

  netClass = {}
  netClass["Default"] = defNetClass 

  schData = { "element" : [], "component_lib" :{}, "net_pin_id_map":{} }
  schData_s = json.dumps( schData )

  brdData = { "units": "deci-mils", "element" : [], "equipot" : [ { "net_name" : "", "net_number" : 0 } ], "net_class" : netClass }
  brdData_s = json.dumps( brdData )

  snap = {}
  snap["id"] = proj["id"]
  snap["json_sch"] = schData_s
  snap["json_brd"] = brdData_s
  db.hmset( "projectsnapshot:" + proj["id"] , snap )

  evId = str(uuid.uuid4())
  ev = {}
  ev["id"] = evId
  dat = {}
  dat["json_sch"] = schData
  dat["jons_brd"] = brdData
  dat["type"] = "none"
  dat["source"] = "none"
  dat["destination"] = "none"
  dat["action"] = "snapshot"
  ev["data"] = dat
  db.hmset( "projectop:" + evId, ev )
  db.rpush("projeectevent:" + projId, evId )


  db.hset( "projectrecent:" + str(userId), "projectId", proj["id"] )
  db.sadd( "projectpool", projId )

  return proj

def updateProjectShortDescription( userId, projectId, descr ):
  db = redis.Redis()
  proj = getProject( str(projectId) )

  if not proj: return None
  if proj["userId"] != str(userId): return None

  return db.hset( "project:" + str(projectId), "shortDescription", descr )



def updateProjectPermission( userId, projectId, perm ):
  db = redis.Redis()

  p = "none"
  if perm == "world-read":
    p = "world-read"
  elif perm == "user":
    p = "user"

  #proj = db.hgetall( "project:" + str(projectId) )
  proj = getProject( str(projectId) )

  if not proj:
    return None
  if proj["userId"] != str(userId):
    return None

  return db.hset( "project:" + str(projectId), "permission", p )


def getProject( projectId ):
  db = redis.Redis()

  proj = db.hgetall( "project:" + str(projectId) )
  if "shortDescription" not in proj:
    proj["shortDescription"] = ""

  return proj

 

def getProjectSnapshot( projectId ):
  db = redis.Redis()
  return db.hgetall( "projectsnapshot:" + str(projectId) )


def deleteProject( userId, projectId ):
  db = redis.Redis()

  #proj = db.hgetall( "project:" + str(projectId) )
  proj = getProject( str(projectId) )
  if not proj:
    return None

  if proj["userId"] != str(userId):
    return None

  r = db.hset( "project:" + str(projectId), "active", "0" )
  return r


def getProjectRecent( userId ):
  db = redis.Redis()

  proj = db.hgetall( "projectrecent:" + str(userId) )
  if not proj:
    return {}

  return proj

def setProjectRecent( userId, projectId ):
  db = redis.Redis()

  obj = {}
  obj["projectId"] = projectId

  r = db.hmset( "projectrecent:" + str(userId), obj )
  return r


## --- portfolio functions

def getPortfolio( userId ):
  db = redis.Redis()
  return db.lrange( "olio:" + str(userId), 0, -1 )

def getAllProjects( ):
  db = redis.Redis()

  pool = db.smembers( "projectpool" )

  projects = []

  for projId in pool:
    #proj = db.hgetall( "project:" + projId )
    proj = getProject( projId )

    if proj and proj["active"] == "1" and proj["permission"] == "world-read":
      user = db.hgetall( "user:" + proj["userId"] )
      proj["userName"] = user["userName"]
      proj["userType"] = user["type"]
      projects.append(proj)

  return projects



def getPortfolios( userId, includePrivateProjects = False ):
  db = redis.Redis()

  olios = []
  #olios = {}
  olioList = db.lrange( "olio:" + str(userId), 0, -1 )

  for projectId in olioList:
    proj = getProject( projectId )

    snap = getProjectSnapshot( projectId )
    proj["json_sch"] = snap["json_sch"];
    proj["json_brd"] = snap["json_brd"];

    if not includePrivateProjects:
      if proj["permission"] != "world-read":
        continue

    u = getUser( proj["userId"] )
    proj["userName"] = u["userName"]


    if ("active" in proj) and (str(proj["active"]) == "1"):
      olios.append( proj )
    #olios[str(projectId)] = getProject(projectId)



  return olios


## --- picture functions

def humanTime():
  ts = time.time()
  return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

def secondTime():
  return time.time()

def createPic( picId, userId, clientToken ):
  db = redis.Redis()

  user = db.hgetall( "user:" + str(userId) )
  picPermission = "user"
  if (user["type"] == "anonymous"):
    picPermission = "world-read"

  ts = time.time()

  pic = {}
  pic["id"] = str(picId)
  pic["userId"] = str(userId)
  pic["permission"] = picPermission
  pic["clientToken"] = str(clientToken)
  pic["stime"] = ts
  pic["timestamp"] = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
  db.hmset( "pic:" + str(picId), pic )

  msg = {}
  msg["id"] = str(clientToken)
  msg["message"] = str(picId)
  msg["type"] = "picCreate"
  db.hmset( "message:" + str(clientToken), msg )

  db.sadd( "picpool", str(picId) )

  return pic



##  --- signup helper functions

def addEmailSignup( emailAddress ):
  db = redis.Redis()

  emailId = str(uuid.uuid4())
  db.sadd( "emailSignups", emailId )

  em = {}
  em["id"] = emailId
  em["email"] = emailAddress
  em["date"] = datetime.datetime.now()
  em["timestamp"] = time.time()


  r = db.hmset( "email:" + emailId, em )
  if not r:
    return r

  return em

#####################

def renderAccordian( json_url, accid, userId = None, portfolioId = None ):
  jjstr = file_cascade( userId, portfolioId, json_url )
  jj = {}

  try:
    jj = json.loads(jjstr)
  except(ee):
    mew.log( "ERROR: (u " + str(userId) + ") " + str(ee)  )
    return

  accordian = []
  count = 0

  js_code = """<script>
  /* http://stackoverflow.com/questions/3820381/need-a-basename-function-in-javascript
     answered Sep 29 '10 at 9:44 by Nivas 
     user contributions licensed under cc by-sa 3.0
  */

  function basename_""" + accid + """(str)
  {
     var base = new String(str).substring(str.lastIndexOf('/') + 1); 
      if(base.lastIndexOf(".") != -1)       
          base = base.substring(0, base.lastIndexOf("."));
     return base;
  }

  function dirname_""" + accid + """(str)
  {
     var base = new String(str).substring(0, str.lastIndexOf('/') ); 
     return base;
  }

  </script>"""
  accordian.append( js_code )

  js_code = """<script> function utf8_to_b64( str ) {
      return window.btoa(encodeURIComponent( escape( str )));
    } </script>
  """
  accordian.append( js_code )

  js_code = " <script> function load_group_details_" + accid + "(group_base_name, n) {"
  js_code += """
  //console.log( group_base_name, n );
  """
  js_code += "} </script>"
  accordian.append( js_code )



  get_cred = ""
  if userId:
    get_cred = "&userId=" + str(userId)
    if portfolioId:
      get_cred += "&portfolioId=" + str(portfolioId)

  js_code = " <script> function load_details_" + accid + "(ele_id, data) {"
  js_code += """ 
  var ele_img = document.getElementById("img_" + ele_id);

  d = dirname_""" + accid + """( data );
  b = basename_""" + accid + """( data );
  d = d.replace( /\/json\//, "/png/" );
  //req = "/picModLibSentry.py?data=img/modlibsnap/" + encodeURI(b) + ".png";
  //req = "/picModLibSentry.py?data=" + encodeURI(d) + "/" + encodeURI(b) + ".png";
  req = "/picModLibSentry.py?data=" + encodeURI(d) + "/" + b + ".png";

//DEBUG
console.log("sending", req );

  ele_img.src = req;

  chev = document.getElementById("btn_chevron_" + ele_id);
  if (chev.className.match( /chevron-right/ )) {
    chev.className = "glyphicon glyphicon-chevron-down";
  } else {
    chev.className = "glyphicon glyphicon-chevron-right";
  }

  """
  js_code += "} </script>"
  accordian.append( js_code )

  js_code = "<script> function load_err_pic( ele_id ) {"
  js_code += """
  var ele_img = document.getElementById( "img_" + ele_id );
  ele_img.src = "/img/ghost_alt_big.png";
  """
  js_code += "} </script>"
  accordian.append( js_code )

  accordian.append( "<div class='panel-group' id='" + accid + "'>" )

  n=0

  for x in jj:
    name = ""
    if "name" in x:
      name = x["name"]

    li = []

    eleid = accid + "_" + str(count)
    count+=1

    accordian.append( "<div class='panel panel-default' style='margin:10px 10px;' >" )
    accordian.append( "  <div class='panel-heading'>" )
    accordian.append( "    <h4 class='panel-title'>" )

    hclick = " onclick='load_group_details_" + accid + "( \"" + accid + "_" + eleid + "\", " + str( len(x["list"]) ) + ");' "
    accordian.append( "      <a class='accordion-toggle collapsed' data-toggle='collapse' data-parent='#" + accid + "' " +
                     " href='#" + eleid +"' name='" + accid + "' " + hclick + " >" )
    accordian.append( cgi.escape( name ) )
    accordian.append( "      </a>" )
    accordian.append( "    </h4>" )
    accordian.append( "  </div>" )
    accordian.append( "</div>" )

    accordian.append( "<div id='" + eleid + "' name='" + accid + "' class='panel-collapse collapse'>" )
    accordian.append( "  <div class='panel-body'>" )

    accordian.append( "     <ul class='list-group'>" )

    for li_ele in x["list"]:
      accordian.append( "  <li class='list-group-item'>" )
      accordian.append( "    <div class='row'>" )

      accordian.append( "      <div class='col-sm-12'> " )

      collapse_id = accid + "_" + eleid + "_" + str(n)
      n += 1

      btnclick = " onclick='load_details_" + accid + "(\"" + collapse_id + "\", \"" + cgi.escape( li_ele["data"] ) + "\" );' "

      accordian.append( "<button name='" + accid + "' " + btnclick + " " +
                       "type='button' class='btn btn-default btn-sm accordion-toggle btn-responsive' data-toggle='collapse' " + 
                       " style='word-wrap:break-word; white-space:normal; ' " + 
                       " data-target='#" + collapse_id +"' > " )


      accordian.append( "<span id='btn_chevron_" + collapse_id + "' " +
                        " class='glyphicon glyphicon-chevron-right' style='margin-right:10px;' > ")
      accordian.append( " </span>" )
      accordian.append( cgi.escape( li_ele["name"] ) )
      accordian.append( " </button>" )

      accordian.append( " <div id='" + collapse_id + "' class='collapse' style='text-align:center;' >")
      accordian.append(" <img onerror='load_err_pic(\"" + collapse_id + "\"); ' style='width:100%; max-width:200px; opacity:0.95; text-align:center; ' " + 
                       " id='img_" + collapse_id + "' alt='...'></img> " )
      accordian.append(" </div> " )

      accordian.append( " </div>" )

      accordian.append( "    </div>" )
      accordian.append( "  </li>" )

    accordian.append( "     </ul>" )
    accordian.append( "  </div>" )
    accordian.append( "</div>" )

  accordian.append( "</div>" )

  r = "\n".join( accordian )
  return r


def queueImport( userId, sessionId, projectId, file_uuid, file_name = None  ):
  db = redis.Redis()
  ts = time.time()

  qid = str(uuid.uuid4())

  if file_name is None:
    file_name = file_uuid

  qf = {}
  qf["id"] = qid
  qf["userId"] = userId
  qf["sessionId"] = sessionId
  if projectId is not None:
    qf["projectId"] = projectId
    qf["type"] = "project"
  else:
    qf["type"] = "portfolio"
  qf["stime"] = ts
  qf["timestamp"] = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
  qf["fileUUID"] = file_uuid
  qf["fileName"] = file_name
  db.hmset( "importq:" + qid, qf )

  db.rpush( "importq", qid )

  return qid


# just return everything for now
#
def getExplorePortfolios( userId, start, end ):
  db = redis.Redis()

  username_h = {}

  projs = db.smembers( "projectpool" )

  r_proj = []

  for proj in projs:
    #p = db.hgetall( "project:" + str(proj) )
    p = getProject( str(proj) )

    if p["active"] != "1": continue
    #if p["userId"] == userId: continue
    if p["permission"] == "world-read":

      if not (p["userId"] in username_h):
        u = db.hgetall( "user:" + str(p["userId"]) )
        username_h[ p["userId"] ] = u["userName"]

      p["userName"] = username_h[ p["userId"] ]
      r_proj.append( p )


  return r_proj


def constructExploreHTMLList( userId, start, end ):

  projs = getExplorePortfolios( userId, start, end )

  #return constructProjectListTable( projs, start, end )
  return constructViewProjectListTable( projs, start, end )


def _constructProjectListTable( projs, start = 0, end = 10, schlink = "sch", brdlink = "brd"  ):

  table_cols = [ "Project", "Description", "Sch", "Brd", "DL" ]
  table_cols_sz = [ "4", "5", "1", "1", "1" ]

  tableProjectHTML = [ ]

  bbs =  "<button type='button' class='btn btn-default btn-xs'>"
  bbe = "</button>"

  bbs_sm =  "<button type='button' class='btn btn-default btn-sm'>"
  bbe_sm = "</button>"

  for p in projs:

    tableProjectHTML.append( "<div class='panel panel-default'> " )
    tableProjectHTML.append( "<div class='panel-body'> <div class='row'> " )


    tableProjectHTML.append( "<div class='col-sm-" + table_cols_sz[0] + "'>" )
    tableProjectHTML.append( "<a href='portfolio?userId=" + p["userId"] + "'>" + p["userName"] + "</a>" )
    tableProjectHTML.append( " / " )
    tableProjectHTML.append( "<a href='project?projectId=" + p["id"] + "'>" + p["name"] + "</a>" )
    tableProjectHTML.append( "</div>" )


    tableProjectHTML.append( "<div class='col-sm-" + table_cols_sz[1] + "'>" )
    tableProjectHTML.append( p["shortDescription"] )
    tableProjectHTML.append( "</div>" )


    tableProjectHTML.append( "<div class='col-sm-" + table_cols_sz[2] + "'>" )
    #tableProjectHTML.append(  "<a href='sch?project=" + p["id"] + "' >" +
    tableProjectHTML.append(  "<a href='" + schlink + "?project=" + p["id"] + "' >" +
                              bbs + "<img src='/img/alignment-unalign.svg' width='20px' /><br/>sch" + bbe + "</a>" )
    tableProjectHTML.append( "</div>" )


    tableProjectHTML.append( "<div class='col-sm-" + table_cols_sz[2] + "'>" )
    #tableProjectHTML.append(  "<a href='brd?project=" + p["id"] + "' >" +
    tableProjectHTML.append(  "<a href='" + brdlink + "?project=" + p["id"] + "' >" +
                              bbs + "<img src='/img/circuit-board.svg' width='20px' /><br/>brd" + bbe + "</a>" )
    tableProjectHTML.append( "</div>" )


    action = "onclick='downloadProject(\"" + p["id"] + "\");'"

    tableProjectHTML.append( "<div class='col-sm-" + table_cols_sz[2] + "'>" )
    tableProjectHTML.append( "<a href='#' " + action + " >" )
    tableProjectHTML.append( bbs_sm )
    tableProjectHTML.append( "<i class='fa fa-cloud-download fa-lg'></i></img>")
    tableProjectHTML.append( bbe_sm )
    tableProjectHTML.append( "</a>" )
    tableProjectHTML.append( "</div>" )


    tableProjectHTML.append( "</div></div></div>" )

  return "\n".join( tableProjectHTML )

  ###


  table_cols = [ "Project", "Owner", "&nbsp;"  ]

  tableProjectHTML = [ "<thead><tr><th>" +
                      "</th><th style='text-align:center;' >".join( table_cols ) +
                      "</th></tr></thead>" ]

  for projectDat in projs:
    projectId = str(projectDat["id"])
    nam = projectDat["name"]

    bbs = "<button type='button' class='btn btn-default btn-xs'>"
    bbe = "</button>"

    x = [ "<a href='project?projectId=" + projectId + "'>" + nam + "</a>",
          #projectDat["userId"], 
          projectDat["userName"], 
          "<a href='#'><i class='fa fa-cloud-download fa-lg'></i></img></a>" ]

    trs = "<tr> <td style='word-break:break-all;' > "
    tre = "</td> </tr>"
    tableProjectHTML.append( trs +
                             "</td> <td style='word-break:break-word; text-align:center; ' >".join(x) +
                             tre )

  hs = "<table class='table table-striped table-bordered table-condensed' >\n"
  he = "</tbody></table>\n"

  return hs + "\n".join( tableProjectHTML ) + he


def constructProjectListTable( projs, start = 0, end = 10 ):
  return _constructProjectListTable( projs, start, end, "sch", "brd" )

def constructViewProjectListTable( projs, start = 0, end = 10 ):
  return _constructProjectListTable( projs, start, end, "view_sch", "view_pcb" ) 

