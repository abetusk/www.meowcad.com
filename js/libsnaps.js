/* Take a picture of a JSON library element */

var g_mutex_ready = true;
var g_id = undefined;

var argv = require("yargs")
           .usage("$0 -i json_file [-W width] [-H height] [-o out_png] [-u userId] [-p projectId] [-v]")
           .demand("i")
           .describe("i json_file", "JSON component library file to render")
           .describe("W width", "Width")
           .describe("H height", "Height")
           .describe("u userId", "User ID")
           .describe("p projectId", "Project ID")
           .describe("o out_png", "Specify PNG output name")
           .describe("D out_png_dir", "Specify PNG output directory (will override -o option)")
           .describe("v", "Verbose flag")
           .argv;

var inpJsonFnRaw;
if (argv.i) { inpJsonFnRaw = argv.i; }

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

var output_directory = undefined;
if (argv.D) { output_directory = argv.D; }

if (!inpJsonFnRaw) {
  console.log("please provide an input JSON file");
  process.exit(1);
}

inpJsonFnA = inpJsonFnRaw.split( ',' );

var Canvas = require('canvas'),
    fs = require('fs'),
    Image = Canvas.Image,
    canvas = Canvas.createCanvas( width, height ),
    //canvas = new Canvas( width, height ),
    ctx = canvas.getContext('2d');

var sch6 = require( "../../bleepsix/js/sch/bleepsixSchematic.js" );
var brd6 = require( "../../bleepsix/js/brd/bleepsixBoardNode.js" );
var Bleepsix = require( "../../bleepsix/js/core/bleepsixRender.js" ),
    bleepsix = new Bleepsix( canvas );
var slurp = require( "./slurp_component_cache.js" );

var sch = new sch6();
var brd = new brd6();

process_iter(0);

function process_iter( index ) {

  if (index >= inpJsonFnA.length ) { return; }

  var inpJsonFn = inpJsonFnA[index];

  if (verbose) {
    console.log( "processing>>>", inpJsonFn );
  }

  while ( !g_mutex_ready ) {
    setTimeout( function() { process_iter(index); }, 100 );
    return;
  }


  var realfn = slurp.file_cascade( inpJsonFn, userId, projectId );
  if (!realfn) {
    console.log("could not find", inpJsonFn );
    process.exit(1);
    process.exit(1);
  }

  json_part = slurp.slurp_json( realfn );

  var transform = [[1,0],[0,-1]];

  var g_component_cache = {};
  var g_footprint_cache = {};

  //slurp.load_full_cache( g_component_cache, "json/component_location.json", userId, projectId );

  for (var x in g_component_cache ) {
    sch.find_component_bounding_box( g_component_cache[x] );
  }

  if (verbose) { console.log("# load done"); }

  global.g_painter = bleepsix;
  global.g_component_cache = g_component_cache;
  global.g_footprint_cache = g_footprint_cache;


  if (verbose) { 
    console.log( "#projectId:", projectId, "w:", width, "h:", height );
  }

  if (g_id) {
    sch.remove( { "id" : g_id, "ref" : sch.refLookup( g_id ) } );
  }

  g_id = sch.addComponentData( json_part, 0, 0, transform );
  sch.drawSchematic( false );

  sch.find_component_bounding_box( sch.kicad_sch_json.element[0] );
  sch.drawSchematic( false );

  var bbox = sch.getSchematicBoundingBox();
  var cbbox = sch.kicad_sch_json.element[0].coarse_bounding_box ;

  if (cbbox[0][0] < bbox[0][0]) { bbox[0][0] = cbbox[0][0]; }
  if (cbbox[0][1] < bbox[0][1]) { bbox[0][1] = cbbox[0][1]; }

  if (cbbox[1][0] > bbox[1][0]) { bbox[1][0] = cbbox[1][0]; }
  if (cbbox[1][1] > bbox[1][1]) { bbox[1][1] = cbbox[1][1]; }

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

  if (output_directory) {
  } else {
    writeSchPng( outfn );
  }

  setTimeout( function() { process_iter(index+1); }, 1 );
}


function writeSchPng( ofn ) {

  var outfd = fs.createWriteStream( ofn );
  var ostream  = canvas.pngStream();

  g_mutex_ready = false;

  ostream.on('data', function(chunk) { outfd.write(chunk); });
  ostream.on('end',
    function() {
      //g_mutex_ready = true;
      if (verbose) {
        console.log("#sch done");
      }
      outfd.end( undefined, 
                 undefined, 
                 function() { 
                   console.log("really ending now"); 
                   g_mutex_ready = true; 
                 } 
               );
    });

}



