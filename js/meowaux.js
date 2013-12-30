var crypto = require('crypto');
var async = require("async");

function authResponse( m )
{
  console.log("auth response (" + m.uid + ")" );
  m.socket.emit("auth", { type:"response", status:"success", sesstok : m.uid } );
}

function s4() {
    return Math.floor((1 + Math.random()) * 0x10000)
      .toString(16)
      .substring(1);
}

function guid() {
    return s4() + s4() + '-' +
           s4() + '-' +
           s4() + '-' +
           s4() + '-' + s4() + s4() + s4();
}


module.exports = {

  s4 : s4,
  guid : guid,
  
  picPermission : function( m ) {
    var userId = m.data.userId;
    var sessionId = m.data.sessionId;
    var picId = m.data.picId;
    var socket = m.socket;
    var db = m.db;

    console.log("picPermission starting, userid: " + userId + ", sessionId: " + sessionId);

    var userRequest = false;
    if ( (typeof userId !== 'undefined') &&
         (typeof sessionId !== 'undefined') )
    {
      userRequest = true;
    }

    async.waterfall([
      function(callback)
      {

        console.log("calling redis hgetall on pic:" + picId);

        db.hgetall( "pic:" + picId, callback );
      },
      function( d, callback )
      {

        if (!d)
        {
          socket.emit("picpermission", { type : "response", status : "error", message: "nonexistent or unauthorized" });
          return;
        }

        var picUserId = d.userId;
        var picPermission = d.permission;

        console.log("pic permission: " + picPermission);

        if ( (!userRequest) &&
             (picPermission == "world-read") )
        {
          socket.emit("picpermission", { 
            type : "response", 
            status : "success", 
            message: "ready", 
            editPermission: "denied" 
          });
          return;
        }
        
        var sha512 = crypto.createHash('sha512');
        var sessHash = sha512.update( picUserId + sessionId ).digest('hex');

        console.log(sessHash);

        db.hgetall( "session:" + sessHash, function(err, d) { callback(err, picPermission,d); });
      },
      function(picPermission, d, callback)
      {

        if (!d)
        {
          socket.emit("picpermission", { type : "response", status : "error", message: "nonexistent or unauthorized" });
          return;
        }

        sessUserId = d.userId;

        if ( sessUserId != userId )
        {
          socket.emit("picpermission", {type:"response", status:"error", message: "nonexistent or unauthroized" });
          return;
        }

        socket.emit("picpermission", {
          type:"response", 
          status:"success", 
          message: "ready",
          editPermission: "allowed",
          permission: picPermission
        });

      }

    ],
    function (err,result) {
      console.log("picPermission error:");
      console.log(err);
      console.log(result);
    });

  },

  picAccess : function( m )
  {
    var db          = m.db;
    var socket      = m.socket;

    var picId       = m.data.picId;
    var userId      = m.data.userId;
    var sessionId   = m.data.sessionId;
    var picPermission = m.data.permission;

    console.log(m.data);

    if ( ( typeof picPermission === 'undefined' ) ||
         ( typeof picId === 'undefined' ) ||
         ( typeof userId === 'undefined' ) ||
         ( typeof sessionId === 'undefined' ) )
    {
      socket.emit("picaccess", { type:"response", status: "error", message: "access denied (0)" });
      return;
    }

    async.waterfall([
      function(callback) {

        var sha512 = crypto.createHash('sha512');
        var sessHash = sha512.update( userId + sessionId ).digest('hex');

        db.hgetall( "session:" + sessHash , callback );
      },
      function(d, callback) {

        if (!d)
        {
          socket.emit("picaccess", { type:"response", status: "error", message: "access denied (1)" });
          return;
        }

        db.hgetall( "pic:" + picId, callback );
      },
      function(d, callback)
      {
        if (!d)
        {
          socket.emit("picaccess", { type:"response", status: "error", message: "access denied (2)" });
          return;
        }

        var picUserId = d.userId;

        if ( picUserId != userId )
        {
          socket.emit("picaccess", { type:"response", status: "error", message: "access denied (3)" });
          return;
        }

        if (picPermission == "world-read")
        {
          db.hmset( "pic:" + picId, { permission: "world-read" });
        }
        else if (picPermission == "user")
        {
          db.hmset( "pic:" + picId, { permission: "user" });
        }
        else
        {
          // user is authenticaed, so giving a useful error message doesn't leak 
          // unauthorized information.
          //
          socket.emit("picaccess", { type:"response", status: "error", message: "invalid permission" });
          return;
        }

        socket.emit("picaccess", { type:"response", status:"success", message: "permission changed" });

      }
    ],
    function(err, result) {
    });
  },

  bar : function() {
    console.log("bar");
  }

};







