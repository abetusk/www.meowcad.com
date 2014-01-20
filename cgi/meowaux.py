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

## -- file system and header (cookie) processing functions

def log( s ):
  f = open( "/tmp/meowaux.log", "a" )
  f.write( str(s) + "\n" )
  f.close()


def slurp_file(fn):
  f = open(fn, "r")
  s = f.read()
  f.close()
  return s

def getCookieHash( environ ):
  cookie_hash = {}
  if 'HTTP_COOKIE' in environ:
    cookies_str = os.environ['HTTP_COOKIE']
    cookies = cookies_str.split('; ')

    for cookie in cookies:
      c = cookie.split('=')
      cookie_hash[ c[0] ] = c[1]

  return cookie_hash

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



def userIndicatorString( userId, userName ):
  userIndicator = "<b><a href='usersettings' >" # ?userId=" + str(userId) + "'> "
  userIndicator += "[" + str(userName) + "] </a> </b> "
  userIndicator += " &nbsp; &nbsp; <a href='logout'>Logout</a> "
  return userIndicator

def errorMessage( msg ):
  return "<div id='message' class='error-message' >" + str(msg) + "</div>"

def successMessage( msg ):
  return "<div id='message' class='success-message'>" + str(msg) + "</div>"

def warningMessage( msg ):
  return "<div id='message' class='warning-message'>" + str(msg) + "</div>"

def statusMessage( msg ):
  return "<div id='message' class='status-message'>" + str(msg) + "</div>"

def nominalMessage( msg ):
  return "<div id='message' class='nominal-message'>" + str(msg) + "</div>"

# landing place so wanrings don't move all content below it
#
def message( msg ):
  return "<div id='message' class='no-message'>" + str(msg) + "</div>"

## --- authentication and session functions 

def authenticateSession( userId, sessionId ):
  db = redis.Redis()

  hashSessionId = hashlib.sha512( str(userId) + str(sessionId) ).hexdigest()

  #print "hashsession:"
  #print hashSessionId

  if not db.sismember( "sesspool", hashSessionId ):
    return 0

  sessionDat = db.hgetall( "session:" + str(hashSessionId) )
  userDat = db.hgetall( "user:" + str(userId) )

  #print sessionDat
  #print userDat

  if ( ("userName" not in userDat) or
       ("userId" not in sessionDat) or
      (sessionDat["userId"] != userId) or
      (sessionDat["active"] != "1") ):
    return 0;

  return 1


def getSessions():
  db = redis.Redis()
  return db.smembers( "sesspool" )

def deactivateSession( userId, sessionId ):
  db = redis.Redis()

  hashSessionId = hashlib.sha512( str(userId) + str(sessionId) ).hexdigest()
  db.srem( "sesspool", str(hashSessionId) )
  x = db.hgetall( "session:" + str(hashSessionId) )
  #if "active" not in x: return 0
  db.hset( "session:" + str(hashSessionId), "active", 0 )
  return 1


def feedback( userId, feedback ):
  db = redis.Redis()

  user = getUser( userId )
  if ("id" not in user) or (user["active"] != "1"):
    return False

  feedbackId = str(uuid.uuid4())

  ts = time.time()
  obj = {}
  obj["id"] = feedbackId
  obj["text"] = str(feedback)
  obj["userId"] = str(userId)
  obj["stime"] = ts
  obj["timestamp"] = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
  db.hmset( "feedback:" + feedbackId, obj )

  db.sadd( "feedbackpool", feedbackId )

  return True

## --- user functions

def getUser( userId ):
  db = redis.Redis()
  return db.hgetall( "user:" + str(userId) )

def setUserPassword( userId, password ):
  db = redis.Redis()
  hashPassword = hashlib.sha512( str(userId) + str(password) ).hexdigest()
  return db.hset( "user:" + str(userId), "passwordHash", hashPassword )

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

def createProject( userId, projectName, permission ):
  db = redis.Redis()

  projId = str(uuid.uuid4())
  schId = str(uuid.uuid4())
  brdId = str(uuid.uuid4())

  userData = db.hgetall( "user:" + str(userId) )
  if ( (not userData) or  (userData["type"] == "anonymous") ):
    return None


  db.rpush( "olio:" + str(userId), projId )

  ts = time.time()
  proj = {}
  proj["id"] = projId
  proj["userId"] = str(userId)
  proj["name"] = str(projectName)
  proj["sch"] = schId
  proj["brd"] = brdId
  proj["active"] = "1"
  proj["stime"] = ts
  proj["timestamp"] = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
  if str(permission) == "world-read":
    proj["permission"] = "world-read"
  else:
    proj["permission"] = "user"
  if not db.hmset( "project:" + proj["id"], proj ):
    return None

  sch = {}
  sch["id"] = schId
  sch["userId"] = str(userId)
  sch["projectId"] = projId
  sch["name"] = randomName( "./american-english.json", 3 )
  sch["active"] = 1
  sch["ind"] = 0
  sch["permission"] = proj["permission"]
  db.hmset("sch:" + schId, sch )

  schData = "{ \"element\" : [] }"
  db.hmset("sch:" + schId + ":0", { "data" : schData } )
  db.hmset("sch:" + schId + ":snapshot", { "data" : schData } )

  brd = {}
  brd["id"] = brdId
  brd["userId"] = str(userId)
  brd["projectId"] = projId
  brd["name"] = randomName( "./american-english.json", 3 )
  brd["active"] = 1
  brd["ind"] = 0
  brd["permission"] = proj["permission"]
  db.hmset("brd:" + brdId, brd )

  brdData = "{ \"element\" : [] }"
  db.hmset("brd:" + brdId + ":0", { "data" : brdData } )
  db.hmset("brd:" + brdId + ":snapshot", { "data" : brdData } )

  db.sadd( "projectpool", projId )

  return proj

def updateProjectPermission( userId, projectId, perm ):
  db = redis.Redis()

  p = "none"
  if perm == "world-read":
    p = "world-read"
  elif perm == "user":
    p = "user"

  proj = db.hgetall( "project:" + str(projectId) )

  if not proj:
    return None
  if proj["userId"] != str(userId):
    return None

  return db.hset( "project:" + str(projectId), "permission", p )


def getProject( projectId ):
  db = redis.Redis()
  return db.hgetall( "project:" + str(projectId) )


def deleteProject( userId, projectId ):
  db = redis.Redis()

  proj = db.hgetall( "project:" + str(projectId) )
  if not proj:
    return None

  if proj["userId"] != str(userId):
    return None

  r = db.hset( "project:" + str(projectId), "active", "0" )
  schId = proj["sch"]
  brdId = proj["brd"]

  r = db.hset( "sch:" + str(schId), "active", "0" )
  r = db.hset( "brd:" + str(brdId), "active", "0" )

  return r


def getProjectRecent( userId ):
  db = redis.Redis()

  proj = db.hgetall( "projectrecent:" + str(userId) )
  if not proj:
    return {}

  return proj

def setProjectRecent( userId, projectId, schematicId, boardId  ):
  db = redis.Redis()

  obj = {}
  obj["project"] = projectId
  obj["sch"] = schematicId
  obj["brd"] = boardId

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
    proj = db.hgetall( "project:" + projId )
    if proj and proj["active"] == "1" and proj["permission"] == "world-read":
      projects.append(proj)

  return projects



def getPortfolios( userId ):
  db = redis.Redis()

  olios = []
  #olios = {}
  olioList = db.lrange( "olio:" + str(userId), 0, -1 )

  

  for projectId in olioList:
    proj = getProject( projectId )
    if ("active" in proj) and (str(proj["active"]) == "1"):
      olios.append( proj )
    #olios[str(projectId)] = getProject(projectId)

  return olios


## --- picture functions


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


