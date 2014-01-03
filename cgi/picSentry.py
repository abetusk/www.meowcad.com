#!/usr/bin/python

import re
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
FILEBASE = "/tmp/stage"

def error_and_quit():
  print "Status: 404 Not Found"
  print
  sys.exit(0)

fields = cgi.FieldStorage()
if "id" not in fields:
  error_and_quit()

fileId = fields["id"].value
fileId = re.sub("[^a-zA-Z0-9-]*", "", fileId);

db = redis.Redis()
picDat = db.hgetall("pic:" + fileId)

if ("id" not in picDat) or ("permission" not in picDat):
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
  except IOError:
    error_and_quit()

else:

  f = open("/tmp/pic.log", "a")

  if "sessionId" not in fields:
    error_and_quit()
  sessionId = fields["sessionId"].value

  ## DEBUG
  f.write("sessionId: " + sessionId + "\n")

  if "userId" not in fields:
    error_and_quit()
  fieldUserId = fields["userId"].value

  ## DEBUG
  f.write("field userId: " + fieldUserId + "\n")

  if (len(sessionId) == 0) or (len(fieldUserId) == 0):
    error_and_quit()

  userDat = db.hgetall("user:" + fieldUserId)
  if "id" not in userDat:
    error_and_quit()

  userId = userDat["id"]
  userName = userDat["userName"]
  passwordHash = userDat["passwordHash"]

  hashedSessionId = hashlib.sha512( userId + sessionId ).hexdigest()


  ## DEBUG
  f.write("db userId: " + userId + "\n")
  f.write("db userName: " + userName + "\n")
  f.write("hashed session id: " + hashedSessionId + "\n")

  if not db.sismember( "sesspool" , hashedSessionId ):
    error_and_quit()

  ## DEBUG
  f.write("cp\n")

  ## DEBUG
  f.write("pic userid: " + picDat["userId"] + "\n");

  if picDat["userId"] != userId:
    error_and_quit()

  try:
    with open( FILEBASE + "/" + fileId ) as pic_fd:
      print "Content-Type: image/png"
      print
      print pic_fd.read()

    f.write("wrote png\n");
    f.close()
  except IOError as e:
    f.write("IOError:" + str(e) );

    f.close()

    error_and_quit()



