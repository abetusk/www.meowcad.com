#!/usr/bin/python

import os, sys, re
import json


if len(sys.argv) < 4:
  print "provide id sch brd"
  sys.exit(1)

sch_fn = sys.argv[2]
brd_fn = sys.argv[3]

with open(sch_fn, "r") as fp:
  sch_str = json.dumps(json.loads(fp.read()))
with open(brd_fn, "r") as fp:
  brd_str = json.dumps(json.loads(fp.read()))

obj={}
obj["id"] = sys.argv[1]
obj["json_sch"] = sch_str
obj["json_brd"] = brd_str

print json.dumps(obj)

