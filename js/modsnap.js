/* Take a picture of a JSON library element */

var yargs = require("yargs");
var argv = yargs
           .usage("$0 -i json_file [-W width] [-H height] [-o out_png] [-u userId] [-p projectId] [-v]")
           //.demand("i")
           .describe("i json_file", "JSON module file to render")
           .describe("I local_json_file", "JSON library file to render (local file)")
           .describe("W width", "Width")
           .describe("H height", "Height")
           .describe("u userId", "User ID")
           .describe("p projectId", "Project ID")
           .describe("o out_png", "Specify PNG output name")
           .describe("v", "Verbose flag")
           .argv;

var inpJsonFn;
if (argv.i) { inpJsonFn = argv.i; }

var local_file = false;
if (argv.I) { local_file = true; }

var outfn = "out.png";
if (argv.o) { outfn = argv.o; }

var width = 200;
if (argv.W) { width = argv.W; }

var height = 200;
if (argv.H) { height = argv.H; }

var userId = undefined;
if (argv.u) { userId = argv.u; }

var projectId = undefined;
if (argv.p) { projectId = argv.u; }

var verbose = false;
if (argv.v) { verbose = true; }

if ((!local_file) && (!inpJsonFn)) {
  console.log("please provide an input JSON file");
  console.log(yargs.help());
  process.exit(1);
}

var Canvas = require('canvas'),
    fs = require('fs'),
    Image = Canvas.Image,
    //canvas = new Canvas( width, height ),
    canvas = Canvas.createCanvas( width, height ),
    ctx = canvas.getContext('2d');

var sch6 = require( "../../bleepsix/js/sch/bleepsixSchematic.js" );
var brd6 = require( "../../bleepsix/js/brd/bleepsixBoardNode.js" );
var Bleepsix = require( "../../bleepsix/js/core/bleepsixRender.js" ),
    bleepsix = new Bleepsix( canvas );
var slurp = require( "./slurp_component_cache.js" );

var sch = new sch6();
var brd = new brd6();


var realfn = slurp.file_cascade( inpJsonFn, userId, projectId );
if (local_file) { realfn = argv.I; }
if (!realfn) {
  console.log("could not find", inpJsonFn );
  process.exit();
}

json_part = slurp.slurp_json( realfn );
json_part.type = "module";

if (!("angle" in json_part)) {
  json_part.angle = 0;
}

for (var ind in json_part.pad) {
  if (!( "angle" in json_part.pad[ind])) {
    json_part.pad[ind].angle = 0;
  }
}

for (var ind in json_part.text) {
  if (!( "angle" in json_part.text[ind])) {
    json_part.text[ind].angle = 0;
  }
}


var g_component_cache = {};
var g_footprint_cache = {};

//slurp.load_full_cache( g_component_cache, "json/component_location.json", userId, projectId );
//slurp.load_full_cache( g_footprint_cache, "json/footprint_location.json", userId, projectId );

//for (var x in g_component_cache ) {
//  sch.find_component_bounding_box( g_component_cache[x] );
//}

var hershey_ascii_json = slurp.slurp_json( "/var/www/json/utf8_hershey_ascii.json" );
brd._load_hershey_ascii_font( hershey_ascii_json );

if (verbose) { console.log("# load done"); }

global.g_painter = bleepsix;
global.g_component_cache = g_component_cache;
global.g_footprint_cache = g_footprint_cache;


if (verbose) { 
  console.log( "#projectId:", projectId, "w:", width, "h:", height );
}


brd.updateBoundingBox( json_part );

brd.addFootprintData( json_part, 0, 0 );
brd.drawBoard();

var bbox = brd.getBoardBoundingBox();
var cbbox = brd.kicad_brd_json.element[0].coarse_bounding_box ;

if ( cbbox[0][0] < bbox[0][0] ) { bbox[0][0] = cbbox[0][0]; }
if ( cbbox[0][1] < bbox[0][1] ) { bbox[0][1] = cbbox[0][1]; }

if ( cbbox[1][0] > bbox[1][0] ) { bbox[1][0] = cbbox[1][0]; }
if ( cbbox[1][1] > bbox[1][1] ) { bbox[1][1] = cbbox[1][1]; }

//console.log( cbbox );
//console.log(bbox);

var cx = (bbox[0][0] + bbox[1][0])/2.0;
var cy = (bbox[0][1] + bbox[1][1])/2.0;

var dx = (bbox[1][0] - bbox[0][0]);
var dy = (bbox[1][1] - bbox[0][1]);

var dmax = ( (dx<dy) ? dy : dx );
var viewmax = ( (width < height) ? height : width );

var f = dmax / viewmax;
if (f < 0.001) f = 0.1;

var brd_fudge = 1.1;
f *= brd_fudge;


//console.log( cx, cy, 1.0/f );

g_painter.setView( cx, cy, 1.0/f );

g_painter.startDrawColor( "rgb(0,0,0)" );
brd.drawBoard();
g_painter.endDraw();

writeBrdPng( outfn );

function writeBrdPng( ofn ) {
  var outfd = fs.createWriteStream( ofn );
  var ostream  = canvas.pngStream();

  ostream.on('data', function(chunk) { outfd.write(chunk); });
  ostream.on('end',
    function() {

      if (verbose) {
        console.log("#brd done");
      }

    });
}



