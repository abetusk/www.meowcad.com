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
#resultLocation = "signupemailfail.html"
resultLocation = "signupfail"

cookie = Cookie.SimpleCookie()

email = None
form = cgi.FieldStorage()
if "email" in form:
  email = form["email"].value
  msg = successMessage;
  #resultLocation = "signupemailsuccess.html"
  resultLocation = "signupsuccess"

  em = mew.addEmailSignup( email )

print "Location:" + resultLocation
print


