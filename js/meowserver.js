var auth = require("./meowauth.js");
var aux = require("./meowaux.js");
var proj = require("./meowproject.js");
var async = require("async");
var io = require("socket.io").listen(8000);
var redis = require('redis'),
    db = redis.createClient();

function _makeData(  transactionId, socket, db, data, callback )
{
  callback = ((typeof callback === 'undefined') ? function() {} : callback );

  var x = 
      { 
        transactionId : transactionId,
        socket : socket, 
        db : db, 
        data : data ,
        callback : callback
      };

  return x;
}

var activeSession = {};
var projectListener = {};

function registerProjectListener( transactionId, projectId, socket )
{
  activeSession[transactionId].projectId = projectId;

  if (projectId in projectListener)
    projectListener[projectId][transactionId] = socket;
  else
    projectListener[projectId] = { transactionId : socket };

}

io.sockets.on('connection', function (socket) {
  var transactionId = aux.guid();

  activeSession[transactionId] = { authenticated : false, socket : socket, db : db,  };

  // state management
  //
  socket.on("disconnect", function() {
    console.log("deleting session with transactionId " + transactionId);

    if ("projectId" in activeSession[transactionId])
    {
      var projId = activeSession[transactionId].projectId;

      console.log("  found projectId, " + projId + ", deleting from projectListener");

      delete projectListener[ projId ];
    }
    delete activeSession[transactionId];
  });

  //socket.emit('meow');

  socket.on('mrow', function (data) {
    console.log("got mrow (" + transactionId + ")");
    console.log(data);
    console.log("");
  });

  socket.on("auth", function(data) { 
    auth.authRequest( _makeData( transactionId, socket, db, data ) );
  });

  socket.on("meow", function(data) { 
    auth.meow( _makeData( transactionId, socket, db, data ) );
  });

  socket.on("anonymouscreate", function(data) { 
    auth.anonymousCreate( _makeData( transactionId, socket, db, data ) );
  });


  // -- proj
  //
  socket.on("newproject", function(data) {
    proj.newProject( _makeData( transactionId, socket, db, data, registerProjectListener) );
  });

  socket.on("projectauth", function(data) {
    proj.projectAuth( _makeData( transactionId, socket, db, data, registerProjectListener ) );
  });


  socket.on("projectflush", function(data) {
    proj.projectFlush( _makeData( transactionId, socket, db, data ) );
  });

  socket.on("projectop", function(data) {
    proj.projectOp( _makeData( transactionId, socket, db, data ) );
  });

  socket.on("projectsnapshot", function(data) {
    proj.projectSnapshot( _makeData( transactionId, socket, db, data ) );
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


