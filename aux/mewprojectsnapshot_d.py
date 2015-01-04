#!/usr/bin/python

import sys
import os
import os.path
import re
import redis
import time
import subprocess as sp
import uuid
import meowaux as mew

db = redis.Redis()

last_project_event_h = {}
g_fn = "./project_event_hash.list"
g_snapdir = "/home/meow/www.meowcad.com/js"
g_snapexec = "projectsnap.js"

USRBASE = "/home/meow/usr"
FILEPATH = "/home/meow/stage"

sleepy = 1

def load_project_event_hash():
  global last_project_event_h

  if os.path.isfile( g_fn ):
    f = open( g_fn )
    for line in f:
      line = line.rstrip()
      vv = line.split(",")
      last_project_event_h[ vv[0] ] = vv[1]
    f.close()

def write_project_event_hash():
  global last_project_event_h

  print "writing"

  f = open( g_fn + ".tmp", "w" )
  for x in last_project_event_h:
    f.write( x + "," + last_project_event_h[x] + "\n" )
  f.close

  os.rename( g_fn + ".tmp", g_fn )


def create_snapshot( userId,  projectId ):
  ex = os.path.join( g_snapdir, g_snapexec )
  print ex

  schpicid = uuid.uuid4()
  brdpicid = uuid.uuid4()

  #schfn = FILEPATH + "/" + str(schpicid)
  #brdfn = FILEPATH + "/" + str(brdpicid)

  sp.call( [ "mkdir", "-p", os.path.join( USRBASE, userId, projectId, "img" ) ] )

  schfn = os.path.join( USRBASE, userId, projectId, "img", str(schpicid) )
  brdfn = os.path.join( USRBASE, userId, projectId, "img", str(brdpicid) )

  ee = [ "node", ex, "-p", projectId, "-u", userId, "-s", schfn, "-b", brdfn ] 
  print ee
  sp.call( ee )

  st = mew.secondTime()
  ht = mew.humanTime()

  projpic = {}
  projpic["userId"] = userId
  projpic["projectId"] = projectId
  projpic["schPicId"] = str(schpicid)
  projpic["brdPicId"] = str(brdpicid)
  projpic["stime"] = st
  projpic["timestamp"] = ht
  db.hmset( "projectpic:" + str(projectId), projpic )

  proj = mew.getProject( projectId )

  pic = {}
  pic["id"] = str(schpicid)
  pic["permission"] = proj["permission"]
  pic["userId"] = userId
  pic["clientToken"] = ""
  pic["projectId"] = projectId
  pic["stime"] = st
  pic["timestamp"] = ht
  db.hmset( "pic:" + str(schpicid) , pic )

  pic = {}
  pic["id"] = str(brdpicid)
  pic["permission"] = proj["permission"]
  pic["userId"] = userId
  pic["clientToken"] = ""
  pic["projectId"] = projectId
  pic["stime"] = st
  pic["timestamp"] = ht
  db.hmset( "pic:" + str(brdpicid) , pic )

def process_projects():
  global last_project_event_h

  dirty = False

  projects = db.smembers( "projectpool" )
  for projid in projects:
    x = db.hgetall( "project:" + projid )

    if not x: continue
    if x["active"] == 0: continue

    userId = x["userId"]

    l = db.lrange( "projectevent:" + projid, -1, -1 )

    if len(l) > 0 :

      if ( (projid in last_project_event_h) and 
           (last_project_event_h[projid] == l[0]) ):
        continue

      if projid in last_project_event_h:
        print ">>", projid, last_project_event_h[projid], "!=", l[0]
      else:
        print ">>", projid, "(nil)" , "!=", l[0]

      dirty = True

      last_project_event_h[projid] = l[0]

      create_snapshot( userId, projid )

  if dirty:
    dirty = False
    write_project_event_hash()


load_project_event_hash()

while True:

  print ">"

  process_projects()
  time.sleep(sleepy)

