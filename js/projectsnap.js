/* Take a picture of the schematic and board */

var argv = require("yargs")
           .usage("$0 -p projectId [-u userId] [-W width] [-H height] [-sch sch-outpng] [-brd brd-outpng] [-v]")
           .demand("p")
           .describe("p projectId", "project id")
           .describe("u userId", "user id")
           .describe("W width", "width")
           .describe("H height", "height")
           .describe("s sch-outpng", "specify schematic output name")
           .describe("b brd-outpng", "specify board output name")
           .describe("v", "verbose")
           .argv;

var userId;
if (argv.u) { userId = argv.u; }

var projectId;
if (argv.p) { projectId = argv.p; }

var schoutfn = "sch-out.png";
if (argv.s) { schoutfn = argv.s; }

var brdoutfn = "brd-out.png";
if (argv.b) { brdoutfn = argv.b; }

var width = 400;
if (argv.W) { width = argv.W; }

var height = 400;
if (argv.H) { height = argv.H; }

var verbose = true;
if (argv.v) { verbose = true; }

if (!projectId) {
  console.log("please provide a projectId");
  process.exit(1);
}

var Canvas = require('canvas'),
    fs = require('fs'),
    Image = Canvas.Image,
    canvas = new Canvas( width, height ),
    ctx = canvas.getContext('2d');

var redis = require("redis"),
    db = redis.createClient();

var sch6 = require( "../../bleepsix/js/sch/bleepsixSchematic.js" );
var brd6 = require( "../../bleepsix/js/brd/bleepsixBoardNode.js" );
var Bleepsix = require( "../../bleepsix/js/core/bleepsixRender.js" ),
    bleepsix = new Bleepsix( canvas );


var sch = new sch6();
var brd = new brd6();

var g_component_cache = {};
var g_footprint_cache = {};

var slurp = require( "./slurp_component_cache.js" );
slurp.load_full_cache( g_component_cache, "json/component_location.json", userId, projectId );
slurp.load_full_cache( g_footprint_cache, "json/footprint_location.json", userId, projectId );

for (var x in g_component_cache ) {
  sch.find_component_bounding_box( g_component_cache[x] );
}


var hershey_ascii_json = slurp.slurp_json( "/var/www/json/utf8_hershey_ascii.json" );
brd._load_hershey_ascii_font( hershey_ascii_json );

if (verbose) { console.log("# load done"); }

global.g_painter = bleepsix;
global.g_component_cache = g_component_cache;
global.g_footprint_cache = g_footprint_cache;


bleepsix.fillRect( 200, 150, 100, 50, "rgb(255,255,136)" )


if (verbose) { 
  console.log( "#projectId:", projectId, "w:", width, "h:", height, "schofn:", schoutfn,  "brdofn:", brdoutfn );
}

var g_project;

var key = "projectsnapshot:" + projectId;
db.hgetall( key, processProject_sch );


function processProject_sch(err, obj) {
  db.end();

  if (!obj) {
    console.log("project (" + projectId + ") not found"); 
    process.exit(2);
  }

  g_project = obj;

  if (verbose) {
    console.log( "#dimensions:", bleepsix.width, bleepsix.height );
    console.log( "#center:", bleepsix.view.cx, bleepsix.view.cy );
    console.log( "#zoom:", bleepsix.zoom );
  }

  //--------------------------------
  var strsch = obj.json_sch;
  var sch_json;
  try { sch_json = JSON.parse( strsch ); } 
  catch (ee) { console.log("bad sch parse", ee ); process.exit(); }

  sch.load_schematic( sch_json );

  if (verbose) { console.log( sch.kicad_sch_json ); }

  sch.drawSchematic( false );

  var bbox = sch.getSchematicBoundingBox();

  var cx = (bbox[0][0] + bbox[1][0])/2.0;
  var cy = (bbox[0][1] + bbox[1][1])/2.0;

  var dx = (bbox[1][0] - bbox[0][0]);
  var dy = (bbox[1][1] - bbox[0][1]);

  var dmax = ( (dx<dy) ? dy : dx );
  var viewmax = ( (width < height) ? height : width );

  var f = dmax / viewmax;
  if (f < 0.001) f = 0.1;

  var sch_fudge = 1.1;
  f *= sch_fudge;

  g_painter.setView( cx, cy, 1/f );

  g_painter.startDrawColor( "rgb(255,255,255)" );
  sch.drawSchematic( false );
  g_painter.endDraw();


  //writeSchPng( "sch-" + outfn );
  writeSchPng( schoutfn );

}

function writeSchPng( ofn ) {
  var outfd = fs.createWriteStream( ofn );
  var ostream  = canvas.pngStream();

  ostream.on('data', function(chunk) { outfd.write(chunk); });
  ostream.on('end',
    function() {

      if (verbose) {
        console.log("#sch done");
      }

      processProject_brd();
    });
}

function processProject_brd() {

  //----------------------

  var strbrd = g_project.json_brd;
  var brd_json;
  try { brd_json = JSON.parse( strbrd ); } 
  catch (ee) { console.log("bad brd parse", ee ); process.exit(); }

  brd.load_board( brd_json );

  if (verbose) { console.log( brd.kicad_brd_json ); }

  brd.drawBoard();

  var bbox = brd.getBoardBoundingBox();

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

  g_painter.setView( cx, cy, 1/f );

  g_painter.startDrawColor( "rgb(0,0,0)" );
  brd.drawBoard();
  g_painter.endDraw();


  //writeBrdPng( "brd-" + outfn );
  writeBrdPng( brdoutfn );
}


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


