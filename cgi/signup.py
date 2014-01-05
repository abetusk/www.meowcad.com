#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import datetime
import meowaux as mew
cgitb.enable()

cookie = Cookie.SimpleCookie()

msg = ""

cookie_hash = mew.getCookieHash( os.environ )
if "message" in cookie_hash:
  msg = str(cookie_hash["message"])
  msg = re.sub( '^\s*"', '', msg )
  msg = re.sub( '"\s*$', '', msg )

  expiration = datetime.datetime.now() + datetime.timedelta(days=-1)
  cookie["message"] = ""
  cookie["message"]["expires"] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S PST")

template = mew.slurp_file("../template/signup.html")

if len(msg) > 0:
  tmp_str = template.replace("<!--MESSAGE-->", mew.nominalMessage(msg) )
else:
  tmp_str = template.replace("<!--MESSAGE-->", mew.message("") )

print "Content-type: text/html; charset=utf-8;"
print cookie.output()
print
print tmp_str



