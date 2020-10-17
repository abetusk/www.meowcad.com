var g_painter=0;

var g_counter = 0;
var frame = 0;
var lastTime;


function psuedo_rand(seed, x) {
  return ('0.'+Math.sin(seed + x).toString().substr(6))
}

function bg_redraw() {
  var W=g_painter.width, H=g_painter.height;

  var n=10, m = 10;

  var w = 16, h= 16, b=0;
  var n = W/(w+b), m = H/(h+b);

  var blue = "rgb(153,153,255)";
  var light = "rgb(255,255,204)";

  //var v0 = [ 153, 153, 255 ];
  //var v1 = [ 255, 255, 204 ];

  //var v0 = [ 148, 26, 26 ];
  //var v0 = [ 185, 26, 26 ];
  //var v1 = [ 31, 108, 108 ];

  var v0 = [ 91, 178, 178 ];
  var v1 = [ 91, 178, 178 ];

  var amin = 0.05;
  var amax = 0.15;

  // To actually see changes:
  //var amin = 0.1;
  //var amax = 0.91;

  var dv = numeric.sub( v1, v0 );
  var ds = numeric.norm2( dv );

  g_painter.setView( W/2, H/2, 1.0 );
  g_painter.startDraw();

  for (var i=0; i<n; i++) {
    var x = i*(w+b) + b;
    for (var j=0; j<m; j++) {
      var y = j*(h+b) + b;

      var dt = new Date();
      var t = dt.getTime();
      var a = amin + (amax-amin)*psuedo_rand( 0, (i*m + j) + t/100000000000.0 );

      var d = numeric.norm2( [ (n-i)/n, (m-j)/m ] ) / Math.sqrt(2);
      var vc = numeric.add( v0, numeric.mul( d, dv ) );
      for (var k=0; k<3; k++) { vc[k] = Math.floor( vc[k] ); }
      var rgba = "rgba(" + vc[0].toString() + "," + vc[1].toString() + "," + vc[2].toString() + "," + a.toString() + ")";

      g_painter.drawRectangle( x, y, w, h, 0, "", true, rgba );
    }
  }

  g_painter.endDraw();

  g_painter.dirty_flag = false;
}

var prev_width = 0, prev_height = 0;

function bg_loop() {
  frame = frame + 1;
  if ( frame >= 30 ) {
    var d = new Date();
    msec = (d.getTime() - lastTime ) / frame;
    lastTime = d;
    frame = 0;
  }

  /*
  var saved_dirty = g_painter.dirty_flag;

  var jumbo = $("#jumbotron");

  var w = jumbo.width();
  var h = jumbo.height();

  if ( ( w != prev_width ) || ( h != prev_height ) ) {
    prev_width = w;
    prev_height = h;

    var pad = jumbo.css("padding").split(" ");
    if ( pad.length == 2 ) {
      w += 2*parseInt( pad[1] );
      h += 2*parseInt( pad[0] );
    } else if (pad.length == 1) {
      w += 2*parseInt( pad[0] );
      h += 2*parseInt( pad[0] );
    }

    var c = $("#bg_canvas");
    c.attr('width', w );
    c.attr('height', h );

    g_painter.dirty_flag=true;
  }
  */


  if (g_painter.dirty_flag) { bg_redraw(); }

  requestAnimationFrame( bg_loop, 100 );
}

function bg_resize( ) {
  var jumbo = $("#jumbotron");
  var w = jumbo.width();
  var h = jumbo.height();


  var padding = jumbo.css('padding');

  /*
  var xy = padding.split(' ');
  var xpad = 0;
  var ypad = 0;

  if (xy.length == 2) {
    ypad = 2*parseInt( xy[0].replace('px', '') );
    xpad = 2*parseInt( xy[1].replace('px', '') );
  } else if (xy.length==1) {
    if (xy[0] !== "") {
      xpad = 2*parseInt( xy[0].replace('px', '') );
      ypad = 2*parseInt( xy[0].replace('px', '') );
    }
  }
  */

  var xpad = 0;
  var ypad = 0;

  if ( jumbo.css("padding-left") !== "" ) {
    xpad += parseInt( jumbo.css("padding-left").replace('px', '') );
  }

  if ( jumbo.css("padding-right") !== "" ) {
    xpad += parseInt( jumbo.css("padding-right").replace('px', '') );
  }

  if ( jumbo.css("padding-top") !== "" ) {
    ypad += parseInt( jumbo.css("padding-top").replace('px', '') );
  }

  if ( jumbo.css("padding-bottom") !== "" ) {
    ypad += parseInt( jumbo.css("padding-bottom").replace('px', '') );
  }

  w += xpad;
  h += ypad;

  var canvas = document.getElementById("bg_canvas");
  canvas.width = w;
  canvas.height = h;

  g_painter.setWidthHeight( w, h );

  g_painter.dirty_flag = true;
  requestAnimationFrame( bg_loop, 1 );
}

function bg_init() {
  var canvas = document.getElementById("bg_canvas");
  g_painter = new bleepsixRender( "bg_canvas" );

  var jumbo = $("#jumbotron");
  var w = jumbo.width();
  var h = jumbo.height();

  g_painter.setWidthHeight( w, h );

  g_painter.dirty_flag = true;

  requestAnimationFrame( bg_loop, 1 );

  setInterval( function() { g_painter.dirty_flag=true; }, 1000.0 );
}


