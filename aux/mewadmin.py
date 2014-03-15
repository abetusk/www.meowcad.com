#!/usr/bin/python
#
"""
A helper script to get some common information from the database out
"""

import os, sys, re
import redis
import json
import meowaux as mew


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


def showhelp():
  print "  feedback"
  print "  users [all|anonymous]"
  print "  sessions"
  print "  signups"
  print
  print "  adduser <user> <pass>"
  print "  deluser <id>"
  print "  activateuser <id>"

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

elif op == "users":
  users( x )

elif op == "sessions":
  sessions()

elif op == "signups":
  signups()

elif op == "adduser":
  adduser(x, y)

elif op == "deluser":
  deluser(x)

elif op == "activateuser":
  activateuser(x)

elif op == "help":
  showhelp()




