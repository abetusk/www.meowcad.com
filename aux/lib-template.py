#!/usr/bin/python
#
# To the extent possible under law, the person who associated CC0 with
# this source code has waived all copyright and related or neighboring rights
# to this source code.
#
# You should have received a copy of the CC0 legalcode along with this
# work.  If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.
#

import sys
import json
import getopt

def mm2decimil(mm):
  return 10000.0*float(mm)/25.4

def inch2mm(inch):
  return 25.4*float(inch)

def decimil2mm(decimil):
  return 25.4*float(decimil)/10000.0

def inch2decimil(inch):
  return float(inch)*10000.0

def decimil2inch(decimil):
  return float(decimil)/10000.0

template = {
  "library_name": "meow",
  "layer" : "15",
  "attribute1":"00000000",
  "name":"meow",
  "keyword": [ "meow" ],

  "timestamp": "00200000",
  "timestamp_op": "0",
  "rotation_cost_90":"0",
  "rotation_cost_180":"0",
  "attribute2": "~~",
  "units":"deci-mils",

  "orientation": "0",
  "angle": 0.0,
  "x": 0.0,
  "y": 0.0,

  "art" : [],
  "text" : [],
  "pad" : []
}

art_template = {
  "segment": {
    "line_width": 120.0,
    "startx":0.0,
    "starty":0.0,
    "endx":0.0,
    "endy":0.0,
    "layer":"21",
    "shape":"segment"
  }
}

text_template = {
  "layer": "21",
  "angle": 0.0,
  "misc": "misc",
  "sizex": 0.0,
  "sizey": 0.0,
  "x": 0.0,
  "y": 0.0,
  "number": "0",
  "visible": True,
  "flag": "N",
  "text": "",
  "rotation": "0",
  "penwidth": 0.0
}

pad_template = {
  "th" : {
    "name": "",
    "net_name": "",
    "type": "STD",
    "shape_code": "C",

    "angle": 0.0,
    "drill_diam": 0.0,

    "deltax": 0.0,
    "deltay": 0.0,

    "sizex": 0.0,
    "sizey": 0.0,

    "drill_x": 0.0,
    "drill_y": 0.0,

    "layer_mask": "00E0FFFF",
    "shape": "circle",
    "net_number": "0",

    "posx": 0.0,
    "posy": 0.0,

    "drill_shape": "circle",
    "orientation": 0
  },

  "sm": {
    "name": "",
    "angle": 0.0,
    "orientation": 0,
    "shape": "rectangle",
    "shape_code": "R",
    "type": "SMD",

    "drill_shape": "circle",
    "drill_diam": 0.0,
    "drill_x": 0.0,
    "drill_y": 0.0,

    "deltax": 0.0,
    "deltay": 0.0,
    "sizex": 0.0,
    "sizey": 0.0,

    "layer_mask": "00888000",
    "posx": 0.0,
    "posy": 0.0
  }
}

opt_val = {
  "units" : "decimil",
  "name": "meow",
  "pitchx": 1000,
  "pitchy": 1000,
  "row":0,
  "col":0,
  "diameter":0,
  "drill_diameter":0,
  "type": "decimil"
}

def show_help(fp):
  fp.write("\n")
  fp.write("usage:\n\n")
  fp.write("  lib-template.py [-h] ...\n")
  fp.write("\n")
  fp.write("  --units           decimil, mm, inch\n")
  fp.write("  --pitchx          pitchx\n")
  fp.write("  --pitchy          pitchy\n")
  fp.write("  --row             row\n")
  fp.write("  --col             col\n")
  fp.write("  --diameter        diaemeter\n")
  fp.write("  --drill_diameter  drill diaemeter\n")
  fp.write("  --type            th, sm\n")
  fp.write("  --name            library name\n")
  fp.write("  [-h]              help\n")
  fp.write("\n")

long_opt = [
  "units=",
  "pitchx=",
  "pitchy=",
  "row=",
  "col=",
  "diameter=",
  "drill_diameter=",
  "type=",
  "name=",
]

try:
  opts, args = getopt.getopt(sys.argv[1:], "h",long_opt)
except getopt.GetoptError:
  show_help(sys.stderr)
  sys.exit(2)
for opt, arg in opts:
  if opt == "-h":
    show_help(sys.stdout)
    sys.exit(0)
  elif opt in ("--units"):
    opt_val["units"] = arg
  elif opt in ("--pitchx"):
    opt_val["pitchx"] = arg
  elif opt in ("--pitchy"):
    opt_val["pitchy"] = arg
  elif opt in ("--row"):
    opt_val["row"] = arg
  elif opt in ("--col"):
    opt_val["col"] = arg
  elif opt in ("--diameter"):
    opt_val["diameter"] = arg
  elif opt in ("--drill_diameter"):
    opt_val["drill_diameter"] = arg
  elif opt in ("--type"):
    opt_val["type"] = arg
  elif opt in ("--name"):
    opt_val["name"] = arg

pitchx = 0
pitchy = 0

if opt_val["units"] == "mm":
  pitchx = mm2decimil(float(opt_val["pitchx"]))
  pitchy = mm2decimil(float(opt_val["pitchy"]))
elif opt_val["units"] == "inch":
  pitchx = inch2decimil(float(opt_val["pitchx"]))
  pitchy = inch2decimil(float(opt_val["pitchy"]))
elif opt_val["units"] == "decimil":
  pitchx = float(opt_val["pitchx"])
  pitchy = float(opt_val["pitchy"])

nx = int(opt_val["col"])
ny = int(opt_val["row"])

cx = pitchx*float(nx-1) / 2.0
cy = pitchy*float(ny-1) / 2.0

part = template.copy()

part["name"] = "meow"

t0 = text_template.copy()
t1 = text_template.copy()

part["text"].append(t0)
part["text"].append(t1)

pad_name = 1
for ii in range(ny):
  for jj in range(nx):

    y = float(ii)*pitchy - cy
    x = float(jj)*pitchx - cx

    pad = pad_template["th"].copy()
    pad["name"] = str(pad_name)
    pad["posx"] = x
    pad["posy"] = y
    pad["sizex"] = mm2decimil(2.0)
    pad["sizey"] = mm2decimil(2.0)
    pad["drill_diam"] = mm2decimil(1.0)

    pad_name += 1

    part["pad"].append(pad)

    #print x, y

print json.dumps(part, indent=2)
