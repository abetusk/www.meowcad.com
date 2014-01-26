#!/usr/bin/python

import re
import os
import cgi
import cgitb
import sys
import json
import uuid
import subprocess as sp
import redis
import hashlib

cgitb.enable();

#FILEBASE = "/tmp/pic"
#FILEBASE = "/tmp/stage"
FILEBASE = "/home/meow/stage"

g_debug = False
def log_line( l ):
  #logf = open("/tmp/picsentry.log", "a")
  logf = open("/home/meow/picsentry.log", "a")
  logf.write( l  + "\n")
  logf.close()


def error_and_quit():

  if g_debug:
    log_line("error, quitting")

  print "Status: 404 Not Found"
  print
  sys.exit(0)

fields = cgi.FieldStorage()
if "id" not in fields:

  if g_debug:
    log_line("no id")

  error_and_quit()

fileId = fields["id"].value
fileId = re.sub("[^a-zA-Z0-9-]*", "", fileId);

db = redis.Redis()
picDat = db.hgetall("pic:" + fileId)

if ("id" not in picDat) or ("permission" not in picDat):
  if g_debug:
    log_line("no id or permission in picDat")

  error_and_quit()

# If it's world readable, don't botehr looking up permissions,
# just display it
#
if picDat["permission"] == "world-read":

  try:
    with open( FILEBASE + "/" + fileId ) as f:
      print "Content-Type: image/png"
      print
      print f.read()
  except IOError, e:

    if g_debug:
      s_e = str(e)
      log_line("ioerror (1) when trying to read " + fileId + " '" + s_e + "'"  )

    error_and_quit()

else:

  if "sessionId" not in fields:
    if g_debug:
      log_line("no session id")
    error_and_quit()

  sessionId = fields["sessionId"].value

  if "userId" not in fields:

    if g_debug:
      log_line("no user id")

    error_and_quit()
  fieldUserId = fields["userId"].value

  if (len(sessionId) == 0) or (len(fieldUserId) == 0):
    if g_debug:
      log_line("length 0 for sessionId or fieldUserId")

    error_and_quit()

  userDat = db.hgetall("user:" + fieldUserId)
  if "id" not in userDat:
    if g_debug:
      log_line("no id in userDat")

    error_and_quit()

  userId = userDat["id"]
  userName = userDat["userName"]
  passwordHash = userDat["passwordHash"]

  hashedSessionId = hashlib.sha512( userId + sessionId ).hexdigest()

  if not db.sismember( "sesspool" , hashedSessionId ):
    if g_debug:
      log_line("session not in sesspool")

    error_and_quit()

  if picDat["userId"] != userId:
    if g_debug:
      log_line("picDat user id != userId")

    error_and_quit()

  try:
    fn = FILEBASE + "/" + fileId
    with open( fn ) as pic_fd:
      d = pic_fd.read()

    print "Content-Type: image/png"
    print
    print d

  except IOError as e:

    ## DEBUG
    #f.write("IOError:" + str(e) );
    #f.close()
    if g_debug:
      s_e = str(e)
      log_line("error opening file (2) " + fileId + ", got '" + s_e + "'")


    error_and_quit()



