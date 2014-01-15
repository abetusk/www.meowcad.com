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

  if not db.sismember( "sesspool", hashSessionId ):
    return 0

  sessionDat = db.hgetall( "session:" + str(hashSessionId) )
  userDat = db.hgetall( "user:" + str(userId) )

  if ( ("userName" not in userDat) or
       ("userId" not in sessionDat) or
      (sessionDat["userId"] != userId) ):
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



## --- user functions

def getUser( userId ):
  db = redis.Redis()
  return db.hgetall( "user:" + str(userId) )

def setUserPassword( userId, password ):
  db = redis.Redis()
  hashPassword = hashlib.sha512( str(userId) + str(password) ).hexdigest()
  return db.hset( "user:" + str(userId), "passwordHash", hashPassword )


## --- project functions

def createProject( userId, projectName, permission ):
  db = redis.Redis()

  projId = str(uuid.uuid4())
  schId = str(uuid.uuid4())
  brdId = str(uuid.uuid4())

  db.rpush( "olio:" + str(userId), projId )

  proj = {}
  proj["id"] = projId
  proj["userId"] = str(userId)
  proj["name"] = str(projectName)
  proj["sch"] = schId
  proj["brd"] = brdId
  proj["active"] = "1"
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
  brd["permission"] = proj["permission"]
  db.hmset("brd:" + brdId, brd )

  brdData = "{ \"element\" : [] }"
  db.hmset("brd:" + brdId + ":0", { "data" : brdData } )
  db.hmset("brd:" + brdId + ":snapshot", { "data" : brdData } )

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


## --- portfolio functions


def getPortfolio( userId ):
  db = redis.Redis()
  return db.lrange( "olio:" + str(userId), 0, -1 )

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

  pic = {}
  pic["id"] = str(picId)
  pic["userId"] = str(userId)
  pic["permission"] = "user"
  pic["clientToken"] = str(clientToken)

  db.hmset( "pic:" + str(picId), pic )

  msg = {}
  msg["id"] = str(clientToken)
  msg["message"] = str(picId)
  msg["type"] = "picCreate"
  db.hmset( "message:" + str(clientToken), msg )

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


