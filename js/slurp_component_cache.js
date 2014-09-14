var default_base = "/var/www";
var user_base = "/home/meow/usr";

var fs = require("fs");

// Unsafe in terms of userId and projectId.
// If we need this we'll put it in, for now we're leaving
// it out for simplicity.
//
function file_cascade( fn, userId, projectId ) {

  if ( (typeof userId !== 'undefined') && (typeof projectId !== 'undefined') )
  {
    var full_fn = user_base + "/" + userId + "/" + projectId + "/" + fn ;
    if ( fs.existsSync( full_fn ) ) 
    {
      var st = fs.statSync( full_fn );
      if (st) { return full_fn; }
    }
  }

  if (typeof userId !== 'undefined')
  {
    var full_fn = user_base + "/" + userId + "/" + fn ;
    if ( fs.existsSync( full_fn ) ) 
    {
      var st = fs.statSync( full_fn );
      if (st) { return full_fn; }
    }
  }

  var full_fn = default_base + "/" + fn;
  if ( fs.existsSync( full_fn ) ) 
  {
    var st = fs.statSync( full_fn );
    if (st) { return full_fn; }
  }

  return null;

}

function slurp_json( fn ) {
  var data = fs.readFileSync( fn );

  try {
    var json = JSON.parse( data );
  } catch (ee) {
    console.log( "could not parse JSON, got:", ee );
    return null;
  }
  return json;
}




function load_full_cache( cache, location_file, userId, projectId )
{
  var loc_fn = file_cascade( location_file, userId, projectId );
  if (!loc_fn) { return null; }

  var loc_json = slurp_json( loc_fn );
  for (var x in loc_json) {

    decode_loc = decodeURIComponent( loc_json[x].location );
    //decode_loc = loc_json[x].location ;

    var fn = file_cascade( decode_loc, userId, projectId );
    if (fn) {
      cache[ x ] = slurp_json(fn);
      //console.log(fn, x, g_component_cache[x] );
    } else {
      console.log("# element not found >>>", x, loc_json[x].location, "u:" + userId, "p:" + projectId, "location:", decode_loc);
    }
  }

}

module.exports = {
  default_base : default_base,
  user_base : user_base,
  file_cascade : file_cascade,
  slurp_json : slurp_json,
  load_full_cache : load_full_cache
};


//DEBUG
/*
var g_component_cache = {};
var g_footprint_cache = {};

var userId = "abe";
var projectId = "mewmew";

load_full_cache( g_component_cache, "json/component_location.json", userId, projectId );
load_full_cache( g_footprint_cache, "json/footprint_location.json", userId, projectId );

for (var x in g_component_cache) {
  console.log(x, g_component_cache[x]);
}

for (var x in g_footprint_cache) {
  console.log(x, g_footprint_cache[x]);
}
*/
//DEBUG

/*
var component_location_fn = file_cascade( "json/component_location.json", userId, projectId );
var footprint_location_fn = file_cascade( "json/footprint_location.json", userId, projectId );

foot_loc_json = slurp_json( footprint_location_fn );
for (var x in foot_loc_json) {
  decode_loc = decodeURIComponent( foot_loc_json[x].location );
  var fn = file_cascade( decode_loc, userId, projectId );
  if (fn) {
    g_footprint_cache[ x ] = slurp_json(fn);
    //console.log(fn, x, g_footprint_cache[x] );
  } else {
    console.log("# footprint not found >>>", x, foot_loc_json[x].location );
  }
}
*/

//console.log( comp_loc_json );
//console.log( foot_loc_json );



/*
var x = fs.readdirSync( "." );

for (var i=0; i<x.length; i++){
  var f = x[i];
  var stat = fs.statSync(f);

  if (stat.isDirectory()) {
    console.log( f + "/" );
  } else {
    console.log( "./" + f );

    var data = fs.readFileSync( f );
    console.log( data.toString() );
  }

}
*/
