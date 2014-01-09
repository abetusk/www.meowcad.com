var auth = require("./meowauth.js");
var aux = require("./meowaux.js");
var proj = require("./meowproject.js");
var async = require("async");
var io = require("socket.io").listen(8000);
var redis = require('redis'),
    db = redis.createClient();

function _makeData(  transactionId, socket, db, data )
{
  var x = 
      { 
        transactionId : transactionId,
        socket : socket, 
        db : db, 
        data : data 
      };

  return x;
}

io.sockets.on('connection', function (socket) {
  var transactionId = aux.guid();

  //socket.emit('meow');

  socket.on('mrow', function (data) {
    console.log("got mrow (" + transactionId + ")");
    console.log(data);
    console.log("");
  });

  //socket.on("auth", function(data) { authRequest( { uid: uid, socket : socket , db : db, data :data} ); });
  socket.on("auth", function(data) { 
    auth.authRequest( _makeData( transactionId, socket, db, data ) );
  });

  socket.on("meow", function(data) { 
    auth.meow( _makeData( transactionId, socket, db, data ) );
  });

  socket.on("anonymous", function(data) { 
    auth.anonymous( _makeData( transactionId, socket, db, data ) );
  });


  // -- proj
  socket.on("schauth", function(data) {
    proj.schAuth( _makeData( transactionId, socket, db, data ) );
  });

  socket.on("schsnapshot", function(data) {
    proj.schSnapshot( _makeData( transactionId, socket, db, data ) );
  });

  socket.on("schfullpush", function(data) {
    proj.schFullPush( _makeData( transactionId, socket, db, data ) );
  });


  socket.on("brdauth", function(data) {
    proj.brdAuth( _makeData( transactionId, socket, db, data ) );
  });

  socket.on("brdfullpush", function(data) {
    proj.brdFullPush( _makeData( transactionId, socket, db, data ) );
  });


  socket.on("newproject", function(data) {
    proj.newProject( _makeData( transactionId, socket, db, data ) );
  });


  //-- pic
  //
  socket.on("picpermission", function(data) {
    aux.picPermission( _makeData( transactionId, socket, db, data ) );
  });

  socket.on("picaccess", function(data) {
    aux.picAccess( _makeData( transactionId, socket, db, data ) );
  });

  socket.on("picready", function(data) {
    aux.picReady( _makeData( transactionId, socket, db, data ) );
  })


});

//io.socket.on('mrow', function(socket) { console.log("got mrow"); });

io.sockets.on("ping", function(socket) { console.log("pong"); });


