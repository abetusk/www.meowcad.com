#!/usr/bin/env node


/*
 *
 * To the extent possible under law, the person who associated CC0 with
 * this source code has waived all copyright and related or neighboring rights
 * to this source code.
 *
 * You should have received a copy of the CC0 legalcode along with this
 * work.  If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.
 *
*/


// cli front end for kijson-lib
//

// Merge two separate projects into one
//
//


KJSON_VERSION = "0.1.0";

var fs = require('fs');
var kijson = require("./kijson-lib.js");


function show_version(fp) {
  fp.write("version: " + KJSON_VERSION + "\n");
}

function show_help(fp) {
  show_version(fp)
  fp.write("\n");
  fp.write("usage:\n");
  fp.write("\n");
  fp.write("    kijson [-a merge|join] [-h] [-v] [-D] proja projb\n");
  fp.write("\n");
  fp.write("  merge                       merge projects together\n")
  fp.write("  join                        join board and schematic JSON files into a project file\n");
  fp.write("  [-D]                        debug output\n");
  fp.write("  [-h]                        show help (this screen)\n");
  fp.write("  [-v]                        show version\n");
  fp.write("\n");
  fp.write("\n");
}

function s4() {
  return Math.floor((1 + Math.random()) * 0x10000)
             .toString(16)
             .substring(1);
};
function guid() {
  return s4() + s4() + '-' +
         s4() + '-' +
         s4() + '-' +
         s4() + '-' + s4() + s4() + s4();
}


var option = {
  "action" : "join",
  "verbose" : false,
  "debug" : false,
  "silent": false,
  "project_fn" : [ '', '' ]
};

var override_option = {};

function update_option(dat, override) {
  override = ((typeof override === "undefined") ? {} : override);
  for (var key in option) {

    // update the option if it's in our custom config
    //
    if (key in dat) {

      // but not if it's specified on the command line
      //
      if ( !(key in override) ) {
        option[key] = dat[key];
      }

    }

  }
}

var getopt = require("posix-getopt");
var parser, opt;
parser = new getopt.BasicParser("hvDa:(action)", process.argv);
while ((opt =  parser.getopt()) !== undefined) {

  switch(opt.option) {

    case 'h':
      show_help(process.stdout);
      process.exit(0);
      break;

    case 'v':
      show_version(process.stdout);
      process.exit(0);
      break;

    case 'D':
      option.debug = true;
      break;

    case 'a':
      option.action = opt.optarg;
      break;

    default:
      show_help(process.stderr);
      process.exit(-1);
      break;
  }
}

if (option.debug) {
  console.log(JSON.stringify(option, null, 2));
  process.exit(0);
}

if (parser.optind() < process.argv.length) {
  option.project_fn[0] = process.argv[parser.optind()];
  option.project_fn[1] = process.argv[parser.optind()+1];
}


//-------------------------
//     _       _       
//    (_) ___ (_)_ __  
//    | |/ _ \| | '_ \ 
//    | | (_) | | | | |
//   _/ |\___/|_|_| |_|
//  |__/               
//
if (option.action == "join") {
	var proj = [ {}, {} ];
  try {
    proj[0] = JSON.parse(fs.readFileSync(option.project_fn[0]));
    proj[1] = JSON.parse(fs.readFileSync(option.project_fn[1]));
  } catch (err) {
    console.log("invalid file");
    process.exit(-1);
  }

  var _proj = kijson.join(proj[0], proj[1]);

  console.log( JSON.stringify(_proj, null, 2) );
}

//-----------------------------------
//                                 
//   _ __ ___   ___ _ __ __ _  ___ 
//  | '_ ` _ \ / _ \ '__/ _` |/ _ \
//  | | | | | |  __/ | | (_| |  __/
//  |_| |_| |_|\___|_|  \__, |\___|
//                      |___/      
//
else if (option.action == "merge") {
	var proj = [ {}, {} ];
  try {
    proj[0] = JSON.parse(fs.readFileSync(option.project_fn[0]));
    proj[1] = JSON.parse(fs.readFileSync(option.project_fn[1]));
  } catch (err) {
    console.log("invalid file");
    process.exit(-1);
  }

  var _proj = kijson.merge(proj[0], proj[1]);

  console.log( JSON.stringify(_proj, null, 2) );
}

