#!/usr/bin/python
#
"""
A helper script to get some common information from the database out
"""

import os, sys, re
import redis
import json
import meowaux as mew

def project( projectId ):
  """Get project information"""

  u = mew.getProject( projectId )
  for x in u:
    print str(x) + ":", u[x]
  print

def projectsnapshot( projectId ):
  """Get projectsnapshot information"""

  db = redis.Redis()

  s = db.hgetall( "projectsnapshot:" + str(projectId) )

  obj = {}
  obj["json_sch"] = s["json_sch"]
  obj["json_brd"] = s["json_brd"]
  obj["id"] = s["id"]
  print(json.dumps(obj))
  print

def projectevent( projectId ):
  db = redis.Redis()
  s = db.lrange("projectevent:" + str(projectId), 0, -1)
  for evid in s:
    print str(evid)
    ev = db.hgetall("projectop:" + str(projectId) + ":" + str(evid))
    print "id:", str(evid)
    print "data", str(ev["data"])
    print ""


def loadprojectsnapshot( projectId, fn ):
  """Force a projects snapshot into database"""

  with open(fn, 'r') as fp:
    z = fp.read()
  s = json.loads(z)

  json_sch = json.dumps( s["json_sch"] )
  json_brd = json.dumps( s["json_brd"] )

  db = redis.Redis()
  db.hset( "projectsnapshot:" + projectId, "id", projectId )
  db.hset( "projectsnapshot:" + projectId, "json_sch", json_sch )
  db.hset( "projectsnapshot:" + projectId, "json_brd", json_brd )

def pullprojectsnapshot( projectId, fn ):
  """Force a projects snapshot into database"""

  db = redis.Redis()
  p = db.hgetall( "projectsnapshot:" + projectId )
  json_sch = json.loads( p["json_sch"] )
  json_brd = json.loads( p["json_brd"] )

  j = {}
  j["json_sch"] = json_sch
  j["json_brd"] = json_brd

  with open(fn, 'w') as fp:
    fp.write( json.dumps(j) )

def user( userId ):
  """Get user information"""

  u = mew.getUser( userId )
  for x in u:
    print str(x) + ":", u[x]
  print

def portfolio( userId ):
  """Get Portfolio for a userid"""

  olio = mew.getPortfolios( userId )
  for proj in olio:
    print
    print
    for x in proj:
      print str(x) + ":", proj[x]

  print

def passwordreset():
  """Print all passwordreset entries"""

  db = redis.Redis()

  fbp = db.smembers( "passwordresetpool" )
  if not fbp: return

  print

  for a in fbp:
    fb = db.hgetall( "passwordreset:" + str(a) )

    email = fb["email"]
    tim = fb["timestamp"]
    txt = fb["text"]

    print ">>>"
    print "datetime:", tim
    print "email:", email
    print "text:>"
    print txt
    print
    print


def feedback():
  """Print all feedback entries"""

  db = redis.Redis()

  fbp = db.smembers( "feedbackpool" )
  if not fbp: return

  print

  for a in fbp:
    fb = db.hgetall( "feedback:" + str(a) )

    uid = fb["userId"]
    email = fb["email"]
    tim = fb["timestamp"]
    txt = fb["text"]

    userDat = db.hgetall( "user:" + str(uid) )

    print ">>>"
    print "datetime:", tim
    if userDat:
      print "user:", userDat["userName"], uid
    print "email:", email
    print "text:>"
    print txt
    print
    print


def users( flag ):
  """Print users"""

  anonUserFlag = False
  regUserFlag  = True

  if flag == "all":
    anonUserFlag = True
    regUserFlag  = True
  elif flag == "anonymous":
    anonUserFlag = True
    regUserFlag  = False

  db = redis.Redis()

  up = db.smembers( "userpool" )

  print

  for userid in up:

    userDat = db.hgetall( "user:" + str(userid) )

    if (userDat["type"] == "anonymous") and not anonUserFlag:
      continue

    if (userDat["type"] == "user") and not regUserFlag:
      continue

    act = "active"
    if userDat["active"] != "1": act = "nonactive"

    print ">>>>"
    print "user:", userDat["userName"], userid
    print "status:", act, "(" + str(userDat["active"]) + ")"
    print "type:", userDat["type"]
    print
    print

def sessions():
  db = redis.Redis()

  sess = db.smembers( "sesspool" )

  print

  for sessid in sess:

    s = db.hgetall( "session:" + str(sessid) )
    userDat = db.hgetall( "user:" + str(s["userId"]) )

    act = "active"
    if s["active"] != "1": act = "nonactive"

    print ">>>>>"
    print "sessionId:", sessid
    print "status:", act, "(" + str(s["active"]) + ")"
    print "user:", userDat["userName"], userDat["id"]
    print
    print

def signups():
  db = redis.Redis()

  sups = db.smembers( "emailSignups" )

  print

  for sup in sups:

    s = db.hgetall( "email:" + str(sup) )
    print ">>>>>>"
    print "id:", sup
    print "datetime:", s["date"]
    print "email:", s["email"]
    print
    print

def adduser(username, password):
  if username is None or password is None:
    print "provide username and password"
    return
  usr = mew.createUser( username, password )
  print str(usr["id"])

def deluser(userid):
  if userid is None :
    print "provide userid"
    return
  db = redis.Redis()
  userDat = db.hgetall( "user:" + str(userid) )
  if "id" not in userDat:
    print "user not found"
    return
  mew.deactivateUser( userid )

def activateuser(userid):
  if userid is None :
    print "provide userid"
    return

  db = redis.Redis()
  userDat = db.hgetall( "user:" + str(userid) )
  if "id" not in userDat:
    print "user not found"
    return

  db.hset( "user:" + str(userid), "active", "1" )

def setuserpassword(userid, password):
  if userid is None :
    print "provide userid"
    return

  mew.setUserPassword( userid, password )

def showhelp():
  print "  feedback"
  print "  passwordreset"
  print "  users [all|anonymous]"
  print "  portfolio <userId>"
  print "  user <userId>"
  print "  project <projectId>"
  print "  projectsnapshot <projectId>"
  print "  projectevent <projectId>"
  print "  loadprojectsnapshot <projectId> <fn>"
  print "  sessions"
  print "  signups"
  print
  print "  adduser <user> <pass>"
  print "  passuser <id> <pass>"
  print "  deluser <id>"
  print "  activateuser <id>"
  print

if len(sys.argv) < 2:
  print "provide command"
  showhelp()
  sys.exit(0)

op = str(sys.argv[1])
x, y = None, None
if len(sys.argv) > 2:
  x = str(sys.argv[2])
  if len(sys.argv) > 3:
    y = str(sys.argv[3])

if op == "feedback":
  feedback()

elif op == "passwordreset":
  passwordreset()

elif op == "users":
  users( x )

elif op == "sessions":
  sessions()

elif op == "signups":
  signups()

elif op == "adduser":
  adduser(x, y)

elif op == "passuser":
  setuserpassword(x, y)

elif op == "deluser":
  deluser(x)

elif op == "activateuser":
  activateuser(x)

elif op == "portfolio":
  portfolio(x)

elif op == "user":
  user(x)

elif op == "project":
  project(x)

elif op == "projectsnapshot":
  projectsnapshot(x)

elif op == "loadprojectsnapshot":
  loadprojectsnapshot(x, y)

elif op == "pullprojectsnapshot":
  pullprojectsnapshot(x, y)

elif op == "projectevent":
  projectevent(x)

elif op == "help":
  showhelp()




