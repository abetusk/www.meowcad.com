var auth = require("./meowauth.js");
var aux = require("./meowaux.js");
var async = require("async");
var io = require("socket.io").listen(8000);
var redis = require('redis'),
    db = redis.createClient();

io.sockets.on('connection', function (socket) {
  var transactionId = aux.guid();

  socket.emit('meow');

  socket.on('mrow', function (data) {
    console.log("got mrow (" + transactionId + ")");
    console.log(data);
    console.log("");
  });

  //socket.on("auth", function(data) { authRequest( { uid: uid, socket : socket , db : db, data :data} ); });
  socket.on("auth", function(data) { 
    auth.authRequest( 
      { 
        transactionId : transactionId,
        socket : socket, 
        db : db, 
        data : data 
      }
    ) ;
  });

  socket.on("picpermission", function(data) {
    aux.picPermission({
      transactionId: transactionId,
      socket : socket,
      db: db,
      data : data
    });
  });

  socket.on("picaccess", function(data) {
    aux.picAccess({
      transactionId: transactionId,
      socket : socket,
      db: db,
      data : data
    });
  });

  socket.on("picready", function(data) {
    aux.picReady({
      transactionId: transactionId,
      socket : socket,
      db: db,
      data : data
    });
  })

});

//io.socket.on('mrow', function(socket) { console.log("got mrow"); });

io.sockets.on("ping", function(socket) { console.log("pong"); });


