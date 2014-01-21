#!/usr/bin/python

import re,cgi,cgitb,sys
import os
import urllib
import Cookie
import datetime
import meowaux as mew
cgitb.enable()

successMessage = " \
<h3> Email address received </h3> \
<p> \
Thank you for your interest.  We will be sure to send you an email when \
the site will be available. \
</p>"

errorMessage = " \
<h3> ERROR </h3> \
<p> \
We're sorry!  There was an error processing your request.  Please send \
us an email at info@meowcad.com or try again later! \
</p>"

msg = errorMessage

cookie = Cookie.SimpleCookie()

email = None
form = cgi.FieldStorage()
if "email" in form:
  email = form["email"].value
  msg = successMessage;


em = mew.addEmailSignup( email )


template = mew.slurp_file("template/signupresponse.html")
tmp_str = template.replace("<!--RESPONSE-->", msg )


print "Content-type: text/html; charset=utf-8;"
print
print tmp_str



